__author__ = 'EB1TR'

import paho.mqtt.client as mqtt
import os
import time

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

flag_connected = 0


def on_connect(client, userdata, flags, rc):
    global flag_connected
    print("Conectado a MQTT")
    flag_connected = 1
    client.subscribe([
        ("hostcmd", 0)
    ])


def on_message(client, userdata, msg):
    dato = msg.payload.decode('utf-8')
    if dato == "shutdown -r now":
        os.system("reboot")
    elif dato == "poweroff":
        os.system("shutdown -h now")


mqtt_client = mqtt.Client()

while flag_connected == 0:
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 600)
    except:
        print(time.time(), "Servidor MQTT no disponible...")
        time.sleep(3)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
