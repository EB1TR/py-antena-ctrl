""" Six Pack & Filter Control - UDP to MQTTn"""
#
# Six Pack & Filter Control
#

# pylint: disable=invalid-name;
# pylint: disable=too-few-public-methods;
# pylint: disable=C0301, R0912, R0914, R0915, R1702, W0703

__author__ = 'EB1TR'
__date__ = "12/09/2020"

import socket
import paho.mqtt.client as mqtt
import xmltodict
import json

MQTT_HOST = "mqtt"
MQTT_PORT = 1883
MQTT_KEEP = 600

try:
    with open('cfg/stn1.json') as json_file:
        data = json.load(json_file)
        STN1 = dict(data)
    with open('cfg/stn2.json') as json_file:
        data = json.load(json_file)
        STN2 = dict(data)
    with open('cfg/segmentos.json') as json_file:
        data = json.load(json_file)
        SEGMENTOS = dict(data)
except Exception as e:
    print("Fallo al cargar configuraciones.")
    print(e)
    exit(0)


def mqtt_connect():
    mqtt_c = mqtt.Client("n1")
    mqtt_c.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP)
    return mqtt_c


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
    elif qrg in range(2795000, 2970000):
        band = 10
    else:
        band = 0
    if band != 0 and band in (80, 160):
        for e in SEGMENTOS[str(band)]:
            if qrg in range(int(SEGMENTOS[str(band)][e]['principio']), int(SEGMENTOS[str(band)][e]['fin'])):
                segmento = e
    else:
        segmento = "0"
    return band, int(segmento)


def publish_radio_info(mqtt_c, radio_i):
    try:
        if radio_i[0] == 1:
            if radio_i[1] == 1:
                mqtt_c.publish("stn1/qrg", radio_i[3])
                mqtt_c.publish("stn1/band", str(radio_i[2]))
                mqtt_c.publish("stn1/mode", radio_i[4])
                mqtt_c.publish("stn1/op", radio_i[5])
        if radio_i[0] == 2:
            if radio_i[1] == 1:
                mqtt_c.publish("stn2/qrg", radio_i[3])
                mqtt_c.publish("stn2/band", str(radio_i[2]))
                mqtt_c.publish("stn2/mode", radio_i[4])
                mqtt_c.publish("stn2/op", radio_i[5])
    except Exception as e:
        print("Problema en la publicación MQTT.")
        print(e)


def process_radio_info(xml_data, mqtt_c):
    stn = 0
    radio = int(xml_data["RadioInfo"]['RadioNr'])
    qrg = int(xml_data["RadioInfo"]['Freq'])
    mode = str(xml_data["RadioInfo"]['Mode']).upper()
    stn_name = str(xml_data["RadioInfo"]['StationName']).upper()
    op = str(xml_data["RadioInfo"]['OpCall']).upper()

    try:
        band, segmento = define_band(qrg)
    except Exception as e:
        print("Fallo en la obtención de la banda y segmento.")
        print(e)
    
    radio_i = [stn, radio, [band, segmento], qrg, mode, op]
    
    if stn_name == str(STN1['netbios']).upper():
        radio_i[0] = 1
    if stn_name == str(STN2['netbios']).upper():
        radio_i[0] = 2
    publish_radio_info(mqtt_c, radio_i)

    if radio_i[0] == 0:
        print("STN no se ha encontrado: " + str(radio_i))
    else:
        print(str(radio_i))


def process_xml(xml_data, mqtt_c):
    try:
        process_radio_info(xml_data, mqtt_c)
    except Exception as e:
        print("Fallo al procesar XML.")
        print(e)


def do_udp():
    global STN1
    global STN2
    print("Netbios STN1: " + STN1['netbios'])
    print("Netbios STN2: " + STN2['netbios'])
    mqtt_c = mqtt_connect()
    mqtt_c.loop_start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 12060))
    while True:
        try:
            data, address = sock.recvfrom(1024)
            data = data.decode('utf-8')
            xml_data = xmltodict.parse(data)
            process_xml(xml_data, mqtt_c)
        except:
            pass


if __name__ == '__main__':
    do_udp()
