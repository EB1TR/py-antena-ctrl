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
import time
import sys
import paho.mqtt.client as mqtt
import xmltodict
import json

MQTT_HOST = "mqtt"
MQTT_PORT = 1883
MQTT_KEEP = 5
mqtt_flag = True

try:
    with open('../../cfg/stn1.json') as json_file:
        data = json.load(json_file)
        STN1 = dict(data)
    with open('../../cfg/stn2.json') as json_file:
        data = json.load(json_file)
        STN2 = dict(data)
except Exception as e:
    print("Fallo al cargar configuraciones.")
    print(e)
    exit(0)


def mqtt_connect():
    global mqtt_flag
    while mqtt_flag:
        try:
            print("Intentando conexión MQTT: %s:%s" % (MQTT_HOST, MQTT_PORT))
            mqtt_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
            mqtt_c.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP)
            mqtt_c.loop_start()
            mqtt_flag = False
            return mqtt_c
        except KeyboardInterrupt:
            print("Parando: Usuario")
            sys.exit(0)
        except:
            print("Conexión fallida a MQTT: %s:%s" % (MQTT_HOST, MQTT_PORT))
            time.sleep(1)


def define_band(qrg):
    if qrg in range(175000, 205000):
        band = 160
    elif qrg in range(345000, 400000):
        band = 80
    elif qrg in range(530000, 550000):
        band = 60
    elif qrg in range(695000, 735000):
        band = 40
    elif qrg in range(1000000, 1020000):
        band = 30
    elif qrg in range(1395000, 1440000):
        band = 20
    elif qrg in range(1800000, 1820000):
        band = 17
    elif qrg in range(2095000, 2150000):
        band = 15
    elif qrg in range(2480000, 2500000):
        band = 12
    elif qrg in range(2795000, 2970000):
        band = 10
    else:
        band = 0

    segmento = "0"
    return band, int(segmento)


def publish_radio_info(mqtt_c, radio_i):
    try:
        if mqtt_c.is_connected() and radio_i[0] == 1:
            mqtt_c.publish("stn1/qrg", radio_i[2])
            mqtt_c.publish("stn1/band", str(radio_i[1]))
            mqtt_c.publish("stn1/mode", radio_i[3])
            mqtt_c.publish("stn1/op", radio_i[4])
            print("Publicación correcta: %s" % radio_i)
        elif mqtt_c.is_connected() and radio_i[0] == 2:
            mqtt_c.publish("stn2/qrg", radio_i[2])
            mqtt_c.publish("stn2/band", str(radio_i[1]))
            mqtt_c.publish("stn2/mode", radio_i[3])
            mqtt_c.publish("stn2/op", radio_i[4])
            print("Publicación correcta: %s" % radio_i)
        elif not mqtt_c.is_connected():
            print("MQTT desconectado.")
        else:
            print("Radio no válida.")
    except Exception as e:
        print("Excepción en publicadión MQTT")
        print(e)


def process_radio_info(xml_data):
    global STN1
    global STN2
    try:
        qrg = int(xml_data["RadioInfo"]['Freq'])
        mode = str(xml_data["RadioInfo"]['Mode']).upper()
        op = str(xml_data["RadioInfo"]['OpCall']).upper()
        stn_name = str(xml_data["RadioInfo"]['StationName']).upper()
        if stn_name == str(STN1['netbios']).upper():
            stn = 1
        elif stn_name == str(STN2['netbios']).upper():
            stn = 2
        else:
            stn = 0
        band, segmento = define_band(qrg)
        radio_dict = [stn, [band, segmento], qrg, mode, op]
        return radio_dict
    except Exception as e:
        print("Fallo al procesar Radio Info.")
        print(e)


def process_xml(data):
    try:
        xml_data = xmltodict.parse(data)
        return xml_data
    except Exception as e:
        print("Fallo al procesar XML.")
        print(e)


def do_udp():
    print("Netbios STN1: " + STN1['netbios'])
    print("Netbios STN2: " + STN2['netbios'])
    mqtt_c = mqtt_connect()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 12060))
    while True:
        try:
            data, address = sock.recvfrom(1024)
            data = data.decode('utf-8')
            xml_data = process_xml(data)
            data_dict = process_radio_info(xml_data)
            publish_radio_info(mqtt_c, data_dict)
        except KeyboardInterrupt:
            print("Parando: Usuario")
            sys.exit(0)
        except:
            print("Fallo general en el servicio UDP.")
            pass


if __name__ == '__main__':
    do_udp()
