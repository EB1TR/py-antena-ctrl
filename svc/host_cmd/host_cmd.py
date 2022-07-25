__author__ = 'EB1TR'

import paho.mqtt.client as mqtt
import os
import time

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883


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


while True:
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 5)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.loop_forever()
    except:
        print("MQTT no disponible")
        time.sleep(2)
