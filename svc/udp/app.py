""" N1MM UDP to MQTT """

__author__ = 'EB1TR'

import socket
import paho.mqtt.client as mqtt
import xmltodict
import json

import settings

MQTT_HOST = settings.Config.MQTT_HOST
MQTT_PORT = int(settings.Config.MQTT_PORT)

try:
    with open('cfg/stn1.json') as json_file:
        data_file = json.load(json_file)
        STN1 = dict(data_file)
    with open('cfg/stn2.json') as json_file:
        data_file = json.load(json_file)
        STN2 = dict(data_file)
    print("Datos de STNs cargados desde ficheros...")
except Exception as e:
    print("Error en los ficheros de configuracion: %s" % e)


def mqtt_connect():
    mqtt_client = mqtt.Client(transport='tcp')
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 600)
    return mqtt_client


def define_band(qrg):
    if qrg in range(175000, 205000):
        band = 160
    elif qrg in range(345000, 400000):
        band = 80
    elif qrg in range(695000, 735000):
        band = 40
    elif qrg in range(1395000, 1440000):
        band = 20
    elif qrg in range(2095000, 2150000):
        band = 15
    elif qrg in range(2795000, 2975000):
        band = 10
    else:
        band = 0
    return band


def publish_radio_info(mqtt_c, radio_i):
    try:
        if radio_i[0] == 1:
            if radio_i[1] == 1:
                mqtt_c.publish("stn1/radio1/qrg", radio_i[3])
                mqtt_c.publish("stn1/radio1/band", radio_i[2])
                mqtt_c.publish("stn1/radio1/mode", radio_i[4])
                mqtt_c.publish("stn1/radio1/op", radio_i[5])
        if radio_i[0] == 2:
            if radio_i[1] == 1:
                mqtt_c.publish("stn2/radio1/qrg", radio_i[3])
                mqtt_c.publish("stn2/radio1/band", radio_i[2])
                mqtt_c.publish("stn2/radio1/mode", radio_i[4])
                mqtt_c.publish("stn2/radio1/op", radio_i[5])
    except Exception as e:
        print("Problemas al publicar en MQTT: %s" % e)


def process_radio_info(xml_data, mqtt_c):
    stn = 0
    try:
        radio = int(xml_data["RadioInfo"]['RadioNr'])
        qrg = int(xml_data["RadioInfo"]['Freq'])
        mode = str(xml_data["RadioInfo"]['Mode'])
        op = str(xml_data["RadioInfo"]['OpCall'])

        band = define_band(qrg)
        op = op.upper()

        radio_i = [stn, radio, band, qrg, mode, op]

        if xml_data["RadioInfo"]['StationName'] == STN1['netbios']:
            radio_i[0] = 1
        if xml_data["RadioInfo"]['StationName'] == STN2['netbios']:
            radio_i[0] = 2

        publish_radio_info(mqtt_c, radio_i)

        if radio_i[0] == 0:
            print("STN no se ha encontrado: %s" % str(radio_i))
        else:
            print(str(radio_i))

    except Exception as e:
        print("Paquete XML no válido")
        print(e)
        print(xml_data)


def do_udp():
    global STN1
    global STN2
    print("Netbios STN1: " + STN1['netbios'])
    print("Netbios STN2: " + STN2['netbios'])
    mqtt_c = mqtt_connect()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 12060))
    while True:
        try:
            data = sock.recvfrom(1024)
            data = data.decode('utf-8')
            xml_data = xmltodict.parse(data)
            process_radio_info(xml_data, mqtt_c)
        except Exception as e:
            print("Error en el socket UDP")
            print(e)


if __name__ == '__main__':
    do_udp()
