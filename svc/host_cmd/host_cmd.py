__author__ = 'EB1TR'

import paho.mqtt.client as mqtt
import os
import time

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_KEEP = 600


def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT")
    client.subscribe([
        ("host_cmd", 0)
    ])


def on_message(client, userdata, msg):
    dato = msg.payload.decode('utf-8')
    if dato == "reboot":
        os.system("sudo shutdown -r now")
    elif dato == "poweroff":
        os.system("sudo shutdown -h now")
    elif dato == "restartn1":
        os.system("docker-compose -f $PATHCTRL/docker-compose.yaml restart n1")


while True:
    try:
        mqtt_client = mqtt.Client("host_cmd")
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.loop_start()
    except:
        print("MQTT no disponible")
        time.sleep(2)
