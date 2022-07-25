__author__ = 'EB1TR'

import paho.mqtt.client as mqtt
import psutil
import time
import os

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883


flag_connected = False


def temp():
    cpu_temp = os.popen(r"vcgencmd measure_temp | egrep -o '[0-9]*\.[0-9]*'").readline()
    return round(float(cpu_temp.replace("temp=", "")), 1)


def on_connect(client, userdata, flags, rc):
    global flag_connected
    print("MQTT Conectado")
    flag_connected = True


def on_disconnect(client, userdata, rc):
    global flag_connected
    print("MQTT Desconectado")
    flag_connected = False


def conn_mqtt():
    c = mqtt.Client("host_status")
    c.connect(MQTT_HOST, MQTT_PORT, 5)
    c.on_connect = on_connect
    c.on_disconnect = on_disconnect
    return c


while True:
    if not flag_connected:
        try:
            client = conn_mqtt()
            flag_connected = True
        except:
            pass
    else:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        client.publish("host/status/temp", temp())
        client.publish("host/status/cpu/used", round(cpu, 1))
        client.publish("host/status/memory/used", round(memory.percent, 1))
        client.publish("host/status/memory/total", round(disk.percent, 1))
        client.loop(timeout=1.0, max_packets=1)
    time.sleep(1)
