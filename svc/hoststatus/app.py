__author__ = 'EB1TR'

import paho.mqtt.client as mqtt
import psutil
import time
import os

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883


def mqtt_connect():
    mqtt_c = mqtt.Client(transport='tcp')
    mqtt_c.connect(MQTT_HOST, MQTT_PORT, 5)
    return mqtt_c


def temp():
    cpu_temp = os.popen("vcgencmd measure_temp").readline()
    return round(float(cpu_temp.replace("temp=", "")), 1)


while True:
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Convert Bytes to GB (Bytes -> KB -> MB -> GB)
    # free = round(disk.free/1024.0/1024.0/1024.0, 1)
    # total = round(disk.total/1024.0/1024.0/1024.0, 1)
    # disk_info = str(free) + 'GB free / ' + str(total) + 'GB total ( ' + str(disk.percent) + '% )'

    mqtt_client = mqtt_connect()

    print(type(temp()))

    mqtt_client.publish("host/status/cpu/temp", temp())
    mqtt_client.publish("host/status/cpu/used", round(cpu, 1))
    mqtt_client.publish("host/status/memory/used", round(memory.percent, 1))
    mqtt_client.publish("host/status/memory/total", round(disk.percent, 1))

    time.sleep(0.5)
