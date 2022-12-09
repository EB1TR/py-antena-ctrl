""" Six Pack, Stack & RX Control """

__author__ = 'EB1TR'

import json
import paho.mqtt.client as mqtt

MQTT_HOST = "mqtt"
MQTT_PORT = 1883
MQTT_KEEP = 60


try:
    with open('cfg/stacks.json') as json_file:
        data = json.load(json_file)
        STACKS = dict(data)
    with open('cfg/sixpack.json') as json_file:
        data = json.load(json_file)
        SIXPACK = dict(data)
    with open('cfg/stn1.json') as json_file:
        data = json.load(json_file)
        STN1 = dict(data)
    with open('cfg/stn2.json') as json_file:
        data = json.load(json_file)
        STN2 = dict(data)
    with open('cfg/rx1.json') as json_file:
        data = json.load(json_file)
        RX1 = dict(data)
    with open('cfg/rx2.json') as json_file:
        data = json.load(json_file)
        RX2 = dict(data)
    with open('cfg/segmentos.json') as json_file:
        data = json.load(json_file)
        SEGMENTOS = dict(data)
        print("Datos de STNs cargados desde fichero...")
except Exception as e:
    print("Error en los ficheros de configuracion: %s" % e)


def nr_ant(stack_band):
    global STACKS
    ant_1 = stack_band['1']['estado']
    ant_2 = stack_band['2']['estado']
    ant_3 = stack_band['3']['estado']
    ant_stack = [ant_1, ant_2, ant_3]
    ant_qty = len([e for e in ant_stack if e == True])
    return ant_qty


def config_stack(band):
    global STACKS
    ant_qty = nr_ant(STACKS[str(band)])
    if ant_qty == 1:
        STACKS[str(band)]['balun'] = False
    else:
        STACKS[str(band)]['balun'] = True

    if not STACKS[str(band)]['1']['estado']:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['1']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['1']['rele'])
        mqtt_client.publish(topic, str(1))  

    if not STACKS[str(band)]['2']['estado']:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['2']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['2']['rele'])
        mqtt_client.publish(topic, str(1))  

    if not STACKS[str(band)]['3']['estado']:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['3']['tta'], STACKS[str(band)]['3']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['3']['tta'], STACKS[str(band)]['3']['rele'])
        mqtt_client.publish(topic, str(1))  

    if not STACKS[str(band)]['balun']:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['tta'], STACKS[str(band)]['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['tta'], STACKS[str(band)]['rele'])
        mqtt_client.publish(topic, str(1))


def assign_sixpack(STNX, stn, band_in):
    global SIXPACK
    for e in SIXPACK[str(stn)]:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (SIXPACK[str(stn)][e]['tta'], SIXPACK[str(stn)][e]['rele'])
        mqtt_client.publish(topic, str(0))
    if band_in != 0:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (SIXPACK[str(stn)][str(band_in)]['tta'], SIXPACK[str(stn)][str(band_in)]['rele'])
        mqtt_client.publish(topic, str(1))
        config_stack(band_in)


def change_segment(stn, band, segment):
    global SEGMENTOS
    global STN1
    global STN2
    if segment != 0:
        for e in SEGMENTOS[str(band)]:
            topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (SEGMENTOS[str(band)][e]['tta'], SEGMENTOS[str(band)][e]['rele'])
            mqtt_client.publish(topic, str(0))
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (SEGMENTOS[str(band)][str(segment)]['tta'], SEGMENTOS[str(band)][str(segment)]['rele'])
        mqtt_client.publish(topic, str(1))
    if stn == 1:
        STN1['segmento'] = segment
    else:
        STN2['segmento'] = segment


def clear_ant():
    assign_stn(1, 0)
    assign_stn(2, 0)


def assign_rx(STNX, RXX, ant):
    if STNX['rx'][str(STNX['band'])] != "0":
        ant_out = RXX[STNX['rx'][str(STNX['band'])]]
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (ant_out['tta'], ant_out['rele'])
        mqtt_client.publish(topic, str(0))
    ant_in = RXX[ant]
    topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (ant_in['tta'], ant_in['rele'])
    mqtt_client.publish(topic, str(1))


def assign_stn(stn, band):
    global STN1
    global STN2
    if stn == 1:
        STNX = STN1
        STNY = STN2
    else:
        STNX = STN2
        STNY = STN1
    if band != STNY['band'] and band != 0:
        if STNX['band'] != band:
            assign_sixpack(STNX, stn, band)
        STNX['band'] = band
    else:
        assign_sixpack(STNX, stn, 0)
        STNX['band'] = 0

    if stn == 1:
        STN1 = STNX
    if stn == 2:
        STN2 = STNX


def status(topic):
    data_json = json.dumps(
        {
            'stn1': STN1,
            'stn2': STN2,
            'stacks': STACKS,
            'sixpack': SIXPACK,
            'rx1': RX1,
            'rx2': RX2,
            'segmentos': SEGMENTOS
        }, sort_keys=False
    )

    mqtt_client.publish(topic, str(data_json))


def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT")
    client.subscribe([
        ("stn1/band", 0),
        ("stn2/band", 0),
        ("set/stn1/antm", 0),
        ("set/stn2/antm", 0),
        ("set/stn1/band", 0),
        ("set/stn2/band", 0),
        ("set/stn1/stack", 0),
        ("set/stn2/stack", 0),
        ("set/rx1", 0),
        ("set/rx2", 0),
        ("update", 0),
        ("set/stn1/nostack", 0),
        ("set/stn2/nostack", 0)
    ])


def on_message(client, userdata, msg):
    global STN1
    global STN2
    global STACKS
    global SIXPACK
    global RX1
    global RX2

    dato = msg.payload.decode('utf-8')

    # Mensajes recibidos desde UDP
    if msg.topic == "stn1/band":
        if STN1['auto']:
            dato = json.loads(dato)
            assign_stn(1, dato[0])
            if dato[1] != STN1['segmento'] and STACKS[str(STN1['band'])]['1']['estado']:
                change_segment(1, dato[0], dato[1])
    elif msg.topic == "stn2/band":
        if STN2['auto']:
            dato = json.loads(dato)
            assign_stn(2, dato[0])
            if dato[1] != STN2['segmento'] and STACKS[str(STN2['band'])]['1']['estado']:
                change_segment(2, dato[0], dato[1])

    # Mensajes recibidos desde FRONT
    elif not STN1['auto'] and msg.topic == "set/stn1/band":
        dato = int(dato)
        assign_stn(1, dato)

    elif not STN2['auto'] and msg.topic == "set/stn2/band":
        dato = int(dato)
        assign_stn(2, dato)
    elif msg.topic == "set/stn1/antm":
        if STN1['auto']:
            STN1['auto'] = False
        else:
            STN1['auto'] = True
    elif msg.topic == "set/stn2/antm":
        if STN2['auto']:
            STN2['auto'] = False
        else:
            STN2['auto'] = True
    elif msg.topic == "set/rx1" and not STN1['band'] == 0:
        assign_rx(STN1, RX1, dato)
        STN1['rx'][str(STN1['band'])] = dato
    elif msg.topic == "set/rx2" and not STN2['band'] == 0:
        assign_rx(STN2, RX2, dato)
        STN2['rx'][str(STN2['band'])] = dato
    elif msg.topic == "set/stn1/stack" and int(STN1['band']) != 0:
        if int(dato) <= STACKS[str(STN1['band'])]['salidas']:
            if STACKS[str(STN1['band'])][dato]['estado']:
                if nr_ant(STACKS[str(STN1['band'])]) > 1:
                    STACKS[str(STN1['band'])][dato]['estado'] = False
            else:
                STACKS[str(STN1['band'])][dato]['estado'] = True
            config_stack(str(STN1['band']))
    elif msg.topic == "set/stn2/stack" and int(STN2['band']) != 0:
        if int(dato) <= STACKS[str(STN2['band'])]['salidas']:
            if STACKS[str(STN2['band'])][dato]['estado']:
                if nr_ant(STACKS[str(STN2['band'])]) > 1:
                    STACKS[str(STN2['band'])][dato]['estado'] = False
            else:
                STACKS[str(STN2['band'])][dato]['estado'] = True
            config_stack(str(STN2['band']))
    elif msg.topic == "set/stn1/nostack" and int(STN1['band']) != 0:
        if STACKS[str(STN1['band'])]["salidas"] > 1:
            ant_a = STACKS[str(STN1['band'])]["1"]['estado']
            ant_b = STACKS[str(STN1['band'])]["2"]['estado']
            ant_c = STACKS[str(STN1['band'])]["3"]['estado']
            stack = [ant_a, ant_b, ant_c]
            if stack.count(True) == 1:
                if STACKS[str(STN1['band'])]["salidas"] == 2 and STACKS[str(STN1['band'])]["1"]['estado']:
                    STACKS[str(STN1['band'])]["1"]['estado'] = False
                    STACKS[str(STN1['band'])]["2"]['estado'] = True
                elif STACKS[str(STN1['band'])]["salidas"] == 2 and STACKS[str(STN1['band'])]["2"]['estado']:
                    STACKS[str(STN1['band'])]["2"]['estado'] = False
                    STACKS[str(STN1['band'])]["1"]['estado'] = True
                elif STACKS[str(STN1['band'])]["salidas"] == 3 and STACKS[str(STN1['band'])]["1"]['estado']:
                    STACKS[str(STN1['band'])]["1"]['estado'] = False
                    STACKS[str(STN1['band'])]["3"]['estado'] = False
                    STACKS[str(STN1['band'])]["2"]['estado'] = True
                elif STACKS[str(STN1['band'])]["salidas"] == 3 and STACKS[str(STN1['band'])]["2"]['estado']:
                    STACKS[str(STN1['band'])]["2"]['estado'] = False
                    STACKS[str(STN1['band'])]["1"]['estado'] = False
                    STACKS[str(STN1['band'])]["3"]['estado'] = True
                elif STACKS[str(STN1['band'])]["salidas"] == 3 and STACKS[str(STN1['band'])]["3"]['estado']:
                    STACKS[str(STN1['band'])]["3"]['estado'] = False
                    STACKS[str(STN1['band'])]["2"]['estado'] = False
                    STACKS[str(STN1['band'])]["1"]['estado'] = True
            else:
                STACKS[str(STN1['band'])]["2"]['estado'] = False
                STACKS[str(STN1['band'])]["3"]['estado'] = False
                STACKS[str(STN1['band'])]["1"]['estado'] = True
            config_stack(str(STN1['band']))
    elif msg.topic == "set/stn2/nostack" and int(STN2['band']) != 0:
        if STACKS[str(STN2['band'])]["salidas"] > 1:
            ant_a = STACKS[str(STN2['band'])]["1"]['estado']
            ant_b = STACKS[str(STN2['band'])]["2"]['estado']
            ant_c = STACKS[str(STN2['band'])]["3"]['estado']
            stack = [ant_a, ant_b, ant_c]
            if stack.count(True) == 1:
                if STACKS[str(STN2['band'])]["salidas"] == 2 and STACKS[str(STN2['band'])]["1"]['estado']:
                    STACKS[str(STN2['band'])]["1"]['estado'] = False
                    STACKS[str(STN2['band'])]["2"]['estado'] = True
                elif STACKS[str(STN2['band'])]["salidas"] == 2 and STACKS[str(STN2['band'])]["2"]['estado']:
                    STACKS[str(STN2['band'])]["2"]['estado'] = False
                    STACKS[str(STN2['band'])]["1"]['estado'] = True
                elif STACKS[str(STN2['band'])]["salidas"] == 3 and STACKS[str(STN2['band'])]["1"]['estado']:
                    STACKS[str(STN2['band'])]["1"]['estado'] = False
                    STACKS[str(STN2['band'])]["3"]['estado'] = False
                    STACKS[str(STN2['band'])]["2"]['estado'] = True
                elif STACKS[str(STN2['band'])]["salidas"] == 3 and STACKS[str(STN2['band'])]["2"]['estado']:
                    STACKS[str(STN2['band'])]["2"]['estado'] = False
                    STACKS[str(STN2['band'])]["1"]['estado'] = False
                    STACKS[str(STN2['band'])]["3"]['estado'] = True
                elif STACKS[str(STN2['band'])]["salidas"] == 3 and STACKS[str(STN2['band'])]["3"]['estado']:
                    STACKS[str(STN2['band'])]["3"]['estado'] = False
                    STACKS[str(STN2['band'])]["2"]['estado'] = False
                    STACKS[str(STN2['band'])]["1"]['estado'] = True
            else:
                STACKS[str(STN2['band'])]["2"]['estado'] = False
                STACKS[str(STN2['band'])]["3"]['estado'] = False
                STACKS[str(STN2['band'])]["1"]['estado'] = True
            config_stack(str(STN2['band']))

    status("pytofront")


mqtt_client = mqtt.Client("control")
mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP)
status("pytofront")
clear_ant()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
