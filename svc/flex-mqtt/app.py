"""FlexRadio TCP/VITA-49 to MQTT bridge."""

import os
import re
import socket
import struct
import sys
import telnetlib
import threading
import time

import paho.mqtt.client as mqtt

import settings


UDP_IP = "0.0.0.0"
UDP_PORT = int(settings.Config.UDPPORT)
TELNET_HOST = settings.Config.FLEXIP
TELNET_PORT = int(settings.Config.FLEXPORT)
STN = settings.Config.STN
MQTT_BROKER = settings.Config.MQTT_HOST
MQTT_PORT = int(settings.Config.MQTT_PORT)

TELNET_TIMEOUT = 10
UDP_TIMEOUT_SECONDS = 20
ACTIVE_SLICE = 0
LAST_QRG = 0
LAST_BAND = "[0, 0]"

SUBSCRIBE_MESSAGES = [
    f"C0|client init PYAPP{STN}\n",
    "C1|sub slice 0\n",
    "C2|sub meter 4\n",
    "C3|sub meter 7\n",
    "C4|sub meter 8\n",
    "C5|sub meter 10\n",
    "C6|sub meter 11\n",
    f"C7|client udpport {UDP_PORT}\n",
]


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Log the MQTT connection result."""
    if reason_code == 0:
        print(f"Conectado al broker {MQTT_BROKER} por el puerto {MQTT_PORT}")
    else:
        print(f"Fallo al conectar, código: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Log MQTT disconnections; Paho handles the reconnect loop."""
    print(f"Desconectado (código: {reason_code}), intentando reconectar...")


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


def telnet_listener():
    """Subscribe to FlexRadio slices and publish their frequency."""
    global LAST_QRG, LAST_BAND, ACTIVE_SLICE

    while True:
        try:
            tn = telnetlib.Telnet(TELNET_HOST, TELNET_PORT, TELNET_TIMEOUT)

            for msg in SUBSCRIBE_MESSAGES:
                tn.write(msg.encode("ascii"))
                time.sleep(0.5)

            def list_slices():
                while True:
                    tn.write(b"C999|slice list\n")
                    time.sleep(2)

            thread_slice = threading.Thread(target=list_slices, daemon=True)
            thread_slice.start()

            while True:
                data = tn.read_until(b"\n", timeout=1)

                if not data:
                    continue

                line = data.decode("utf-8", errors="ignore").strip()

                if line.startswith("R999|0|"):
                    if line == "R999|0|" and ACTIVE_SLICE != 9:
                        tn.write(b"C1000|unsub slice all\n")
                        ACTIVE_SLICE = 9
                    elif line == "R999|0|0" and ACTIVE_SLICE != 0:
                        tn.write(b"C1001|sub slice 0\n")
                        ACTIVE_SLICE = 0
                    elif line == "R999|0|1" and ACTIVE_SLICE != 1:
                        tn.write(b"C1002|sub slice 1\n")
                        ACTIVE_SLICE = 1
                    elif line == "R999|0|0 1" and ACTIVE_SLICE != 0:
                        tn.write(b"C1003|sub slice 0\n")
                        ACTIVE_SLICE = 0

                if ACTIVE_SLICE == 9:
                    mqtt_client.publish(f"{STN}/band", "[0, 0]")
                    mqtt_client.publish(f"{STN}/qrg", "0")
                else:
                    mqtt_client.publish(f"{STN}/band", LAST_BAND)
                    mqtt_client.publish(f"{STN}/qrg", LAST_QRG)

                match_qrg = re.search(r"RF_frequency=([0-9.]+)", line)
                if match_qrg:
                    frequency = float(match_qrg.group(1))
                    LAST_QRG = frequency * 100000
                    mqtt_client.publish(f"{STN}/qrg", LAST_QRG)

                    band = obtain_band(frequency)
                    LAST_BAND = str([band, 0])
                    mqtt_client.publish(f"{STN}/band", LAST_BAND)

        except Exception as exc:
            print(f"[TELNET] Error or disconnected: {exc}")
            print("[TELNET] Reconnect in 5 seconds...")
            time.sleep(5)
            mqtt_client.publish(f"{STN}/band", "[0, 0]")
            mqtt_client.publish(f"{STN}/qrg", "0")


def udp_listener():
    """Receive the VITA-49 meter stream from FlexRadio."""
    global last_udp_time

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    while True:
        data, _address = sock.recvfrom(4096)
        last_udp_time = time.time()
        process_vita49(data)


last_udp_time = time.time()


def udp_activity_monitor():
    """Restart the bridge when the FlexRadio UDP stream stops."""
    global last_udp_time

    while True:
        time.sleep(5)
        inactive = time.time() - last_udp_time

        if inactive > UDP_TIMEOUT_SECONDS:
            print(f"[UDP] No data in {UDP_TIMEOUT_SECONDS} seconds. Restarting connection...")
            os.execv(sys.executable, ["python"] + sys.argv)


def process_vita49(data):
    """Decode FlexRadio VITA-49 meters and publish them to MQTT."""
    header_format = "!BBHIQIQ"
    header_size = struct.calcsize(header_format)

    try:
        struct.unpack(header_format, data[0:header_size])
        payload = data[header_size:]
        meter_data = {}

        for meter_id, meter_value in struct.iter_unpack("!hh", payload):
            meter_data[meter_id] = meter_value

        for meter_id, value in meter_data.items():
            meter_id = f"0{meter_id}"[-2:]

            match meter_id:
                case "04":
                    mqtt_client.publish(f"{STN}/tensiona", value / 256)
                case "07":
                    mqtt_client.publish(f"{STN}/fun", value)
                case "08":
                    mqtt_client.publish(f"{STN}/pwr", 10 ** ((value / 128) / 10) * 1e-3)
                case "10":
                    mqtt_client.publish(f"{STN}/swr", value / 128)
                case "11":
                    mqtt_client.publish(f"{STN}/temp", value / 64)

    except struct.error as exc:
        print(f"[UDP] [ERROR]: {exc}")


def obtain_band(frequency):
    """Return the configured band in metres for a frequency in MHz."""
    bands = {
        160: (1.7, 2.1),
        80: (3.3, 4.0),
        60: (5.0, 5.5),
        40: (6.0, 8.0),
        30: (9.0, 13.0),
        20: (13.0, 16.0),
        17: (16.0, 19.0),
        15: (19.0, 22.0),
        12: (22.0, 25.5),
        10: (25.5, 30.0),
    }

    for band, (start, end) in bands.items():
        if start <= frequency <= end:
            return band
    return 0


if __name__ == "__main__":
    thread_udp = threading.Thread(target=udp_listener, daemon=True)
    thread_telnet = threading.Thread(target=telnet_listener, daemon=True)
    thread_watchdog = threading.Thread(target=udp_activity_monitor, daemon=True)

    thread_udp.start()
    thread_telnet.start()
    thread_watchdog.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Closing program...")
