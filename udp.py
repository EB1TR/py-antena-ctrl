""" Six Pack & Filter Control - UDP to MQTTn"""
#
# Six Pack & Filter Control
#

# pylint: disable=invalid-name;
# pylint: disable=too-few-public-methods;
# pylint: disable=C0301, R0912, R0914, R0915, R1702, W0703

__author__ = 'EB1TR'
__date__ = "12/09/2020"

import settings
import socket
import paho.mqtt.client as mqtt
import xmltodict


try:
    MQTT_HOST = settings.Config.MQTT_HOST
    MQTT_PORT = settings.Config.MQTT_PORT
    STN1 = settings.Config.STN1
    STN2 = settings.Config.STN2
    pass
except Exception as e:
    print('Unexpected: %s' % e)
    exit(1)


def mqtt_connect():
    mqtt_c = mqtt.Client(transport='tcp')
    mqtt_c.connect(MQTT_HOST, MQTT_PORT, 600)
    return mqtt_c


def define_band(qrg):
    if qrg in range(180000, 200000):
        band = 160
    elif qrg in range(350000, 400000):
        band = 80
    elif qrg in range(700000, 720000):
        band = 40
    elif qrg in range(1400000, 1435000):
        band = 20
    elif qrg in range(2100000, 2145000):
        band = 15
    elif qrg in range(2800000, 2970000):
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
            if radio_i[1] == 2:
                mqtt_c.publish("stn1/radio2/qrg", radio_i[3])
                mqtt_c.publish("stn1/radio2/band", radio_i[2])
                mqtt_c.publish("stn1/radio2/mode", radio_i[4])
                mqtt_c.publish("stn1/radio2/op", radio_i[5])
        if radio_i[0] == 2:
            if radio_i[1] == 1:
                mqtt_c.publish("stn2/radio1/qrg", radio_i[3])
                mqtt_c.publish("stn2/radio1/band", radio_i[2])
                mqtt_c.publish("stn2/radio1/mode", radio_i[4])
                mqtt_c.publish("stn2/radio1/op", radio_i[5])
            if radio_i[1] == 2:
                mqtt_c.publish("stn2/radio2/qrg", radio_i[3])
                mqtt_c.publish("stn2/radio2/band", radio_i[2])
                mqtt_c.publish("stn2/radio2/mode", radio_i[4])
                mqtt_c.publish("stn2/radio2/op", radio_i[5])
    except:
        print("MQTT problem")


def process_radio_info(xml_data, mqtt_c):
    stn = 0
    radio = int(xml_data["RadioInfo"]['RadioNr'])
    qrg = int(xml_data["RadioInfo"]['Freq'])
    band = define_band(qrg)
    mode = str(xml_data["RadioInfo"]['Mode'])
    op = str(xml_data["RadioInfo"]['OpCall'])
    op = op.upper()
    radio_i = [stn, radio, band, qrg, mode, op]
    if xml_data["RadioInfo"]['StationName'] == STN1:
        radio_i[0] = 1
    if xml_data["RadioInfo"]['StationName'] == STN2:
        radio_i[0] = 2

    publish_radio_info(mqtt_c, radio_i)

    if radio_i[0] == 0:
        print("STN no se ha encontrado: " + str(radio_i))
    else:
        print(str(radio_i))


def process_xml(xml_data, mqtt_c):
    try:
        process_radio_info(xml_data, mqtt_c)
    except:
        print("Paquete no válido")


def do_udp():
    global STN1
    global STN2
    mqtt_c = mqtt_connect()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 12060))
    while True:
        data, address = sock.recvfrom(1024)
        data = data.decode('utf-8')
        xml_data = xmltodict.parse(data)
        process_xml(xml_data, mqtt_c)


if __name__ == '__main__':
    do_udp()
