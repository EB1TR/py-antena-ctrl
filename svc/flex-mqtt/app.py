"""FlexRadio TCP/VITA-49 to MQTT bridge."""

import os
import re
import socket
import struct
import sys
import threading
import time

import paho.mqtt.client as mqtt

import settings
from commands import CommandBridge


CONFIG = settings.load_config()
UDP_IP = "0.0.0.0"
UDP_PORT = CONFIG.udp_port
TELNET_HOST = CONFIG.flex_host
TELNET_PORT = CONFIG.flex_port
STN = CONFIG.station
MQTT_BROKER = CONFIG.mqtt_host
MQTT_PORT = CONFIG.mqtt_port

TELNET_TIMEOUT = 10
UDP_TIMEOUT_SECONDS = 20
TX_QUERY_INTERVAL_SECONDS = 2
TX_HEARTBEAT_INTERVAL_SECONDS = 2
ACTIVE_SLICE = 0
LAST_QRG = 0
LAST_BAND = "[0, 0]"
LAST_TRANSMITTING = None
LAST_TX_PUBLISH_TIME = 0.0

TX_QUERY_MESSAGES = (
    b"C12|transmit\n",
    b"C13|interlock\n",
    b"C14|radio\n",
)

SUBSCRIBE_MESSAGES = [
    f"C0|client init PYAPP{STN}\n",
    "C1|sub slice all\n",
    "C2|sub meter 4\n",
    "C3|sub meter 7\n",
    "C4|sub meter 8\n",
    "C5|sub meter 10\n",
    "C6|sub meter 11\n",
    f"C7|client udpport {UDP_PORT}\n",
    "C8|sub tx all\n",
    "C9|sub transmit all\n",
    "C10|sub interlock all\n",
    "C11|sub radio all\n",
    "C12|transmit\n",
    "C13|interlock\n",
    "C14|radio\n",
    "C15|sub atu all\n",
]


class FlexConnection:
    """Small line-oriented TCP client replacing the removed telnetlib module."""

    def __init__(self, host, port, timeout):
        self.socket = socket.create_connection((host, port), timeout=timeout)
        self.buffer = b""
        self.write_lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.socket.close()

    def write(self, data):
        with self.write_lock:
            self.socket.sendall(data)

    def read_until(self, separator, timeout):
        deadline = time.monotonic() + timeout
        while separator not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return b""
            self.socket.settimeout(remaining)
            try:
                chunk = self.socket.recv(4096)
            except TimeoutError:
                return b""
            if not chunk:
                raise ConnectionError("FlexRadio cerró la conexión TCP")
            self.buffer += chunk

        end = self.buffer.index(separator) + len(separator)
        result, self.buffer = self.buffer[:end], self.buffer[end:]
        return result


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Log the MQTT connection result."""
    global LAST_TX_PUBLISH_TIME

    if reason_code == 0:
        client.subscribe([(f"set/{STN}/mox", 0), (f"set/{STN}/tune", 0), (f"set/{STN}/atu", 0), (f"set/{STN}/split", 0)])
        print(f"Conectado al broker {MQTT_BROKER} por el puerto {MQTT_PORT}")
        if LAST_TRANSMITTING is not None:
            LAST_TX_PUBLISH_TIME = time.monotonic()
            client.publish(
                f"{STN}/tx", "1" if LAST_TRANSMITTING else "0", retain=True
            )
    else:
        print(f"Fallo al conectar, código: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Log MQTT disconnections; Paho handles the reconnect loop."""
    print(f"Desconectado (código: {reason_code}), intentando reconectar...")


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
command_bridge = CommandBridge(STN, mqtt_client.publish)
mqtt_client.on_message = command_bridge.on_message
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


def parse_key_values(text):
    """Parse the key=value fields in a FlexRadio status line."""
    values = {}
    for part in str(text or "").split():
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key.strip().lower()] = value.strip()
    return values


def normalize_tx_state(value):
    """Convert stable FlexRadio interlock states to TX/RX."""
    text = str(value or "").strip().upper()
    if text == "TRANSMITTING":
        return True
    if text in (
        "RECEIVE",
        "READY",
        "NOT_READY",
        "TX_FAULT",
        "TIMEOUT",
        "STUCK_INPUT",
    ):
        return False
    # PTT_REQUESTED / UNKEY_REQUESTED are transitions, not final TX/RX states.
    # Unknown states must not overwrite the last confirmed state either.
    return None


def publish_transmit_state(transmitting):
    """Publish TX/RX immediately on change and periodically as a heartbeat."""
    global LAST_TRANSMITTING, LAST_TX_PUBLISH_TIME

    now = time.monotonic()
    changed = transmitting != LAST_TRANSMITTING
    if not changed:
        if now - LAST_TX_PUBLISH_TIME < TX_HEARTBEAT_INTERVAL_SECONDS:
            return

    LAST_TRANSMITTING = transmitting
    LAST_TX_PUBLISH_TIME = now
    mqtt_client.publish(f"{STN}/tx", "1" if transmitting else "0", retain=True)
    if changed:
        print(f"FlexRadio {STN}: {'TX' if transmitting else 'RX'}")


def update_transmit_state(line):
    """Derive actual TX/RX only from FlexRadio interlock status messages."""

    match = re.match(r"^S[0-9A-Fa-f]+\|interlock\s+(.+)$", line)
    if not match:
        return

    # Slice tx=1 selects the transmit slice; rfpower is a power setting.
    # Neither means that the radio is currently transmitting.
    values = parse_key_values(match.group(1))
    transmitting = normalize_tx_state(values.get("state"))
    if transmitting is not None:
        publish_transmit_state(transmitting)


def telnet_listener():
    """Subscribe to FlexRadio slices and publish their frequency."""
    global LAST_QRG, LAST_BAND, ACTIVE_SLICE, LAST_TRANSMITTING

    while True:
        try:
            with FlexConnection(TELNET_HOST, TELNET_PORT, TELNET_TIMEOUT) as tn:
                LAST_TRANSMITTING = None
                for msg in SUBSCRIBE_MESSAGES:
                    tn.write(msg.encode("ascii"))
                    time.sleep(0.5)

                command_bridge.attach(tn)
                next_slice_query = 0
                next_tx_query = time.monotonic() + TX_QUERY_INTERVAL_SECONDS
                while True:
                    command_bridge.expire()
                    now = time.monotonic()
                    if now >= next_slice_query:
                        tn.write(b"C999|slice list\n")
                        next_slice_query = now + 2

                    if now >= next_tx_query:
                        for message in TX_QUERY_MESSAGES:
                            tn.write(message)
                        next_tx_query = now + TX_QUERY_INTERVAL_SECONDS

                    data = tn.read_until(b"\n", timeout=1)

                    if not data:
                        continue

                    line = data.decode("utf-8", errors="ignore").strip()
                    command_bridge.status(line)
                    command_bridge.response(line)
                    update_transmit_state(line)
                    # Confirm TCP liveness even when interlock has not changed.
                    if LAST_TRANSMITTING is not None:
                        publish_transmit_state(LAST_TRANSMITTING)

                    receive_slice = command_bridge.split.receiver()
                    ACTIVE_SLICE = 9 if receive_slice is None else receive_slice

                    if ACTIVE_SLICE == 9:
                        mqtt_client.publish(f"{STN}/band", "[0, 0]")
                        mqtt_client.publish(f"{STN}/qrg", "0")
                    else:
                        mqtt_client.publish(f"{STN}/band", LAST_BAND)
                        mqtt_client.publish(f"{STN}/qrg", LAST_QRG)

                    receive_frequency = command_bridge.split.frequency()
                    if receive_frequency is not None:
                        frequency = float(receive_frequency)
                        LAST_QRG = frequency * 100000
                        mqtt_client.publish(f"{STN}/qrg", LAST_QRG)

                        band = obtain_band(frequency)
                        LAST_BAND = str([band, 0])
                        mqtt_client.publish(f"{STN}/band", LAST_BAND)

        except Exception as exc:
            LAST_TRANSMITTING = None
            command_bridge.detach()
            print(f"[TELNET] Error or disconnected: {exc}")
            print("[TELNET] Reconnect in 5 seconds...")
            time.sleep(5)
            mqtt_client.publish(f"{STN}/band", "[0, 0]")
            mqtt_client.publish(f"{STN}/qrg", "0")
        finally:
            command_bridge.detach()


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
