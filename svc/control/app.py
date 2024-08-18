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
        print("Datos de STNs cargados desde fichero...")
except Exception as e:
    print("Error en los ficheros de configuracion: %s" % e)
    exit(0)


def nr_ant(stack_band):
    global STACKS
    ant_1 = stack_band['1']['estado']
    ant_2 = stack_band['2']['estado']
    ant_3 = stack_band['3']['estado']
    ant_stack = [ant_1, ant_2, ant_3]
    ant_qty = len([e for e in ant_stack if e is True])
    return ant_qty


def config_stack(band):
    global STACKS
    ant_qty = nr_ant(STACKS[str(band)])
    if ant_qty == 1:
        STACKS[str(band)]['balun'] = False
    else:
        STACKS[str(band)]['balun'] = True

    if not STACKS[str(band)]['1']['estado']:
        topic = STACKS[str(band)]['1']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['1']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['2']['estado']:
        topic = STACKS[str(band)]['2']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['2']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['3']['estado']:
        topic = STACKS[str(band)]['3']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['3']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['balun']:
        topic = STACKS[str(band)]['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['rele']
        mqtt_client.publish(topic, str(1))


def config_multiplex(band):
    global STACKS
    ant_qty = nr_ant(STACKS[str(band)])
    if ant_qty == 1:
        STACKS[str(band)]['balun'] = False
    else:
        STACKS[str(band)]['balun'] = True

    if not STACKS[str(band)]['1']['estado']:
        topic = STACKS[str(band)]['1']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['1']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['2']['estado']:
        topic = STACKS[str(band)]['2']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['2']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['3']['estado']:
        topic = STACKS[str(band)]['3']['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['3']['rele']
        mqtt_client.publish(topic, str(1))

    if not STACKS[str(band)]['balun']:
        topic = STACKS[str(band)]['rele']
        mqtt_client.publish(topic, str(0))
    else:
        topic = STACKS[str(band)]['rele']
        mqtt_client.publish(topic, str(1))


def assign_sixpack(STNX, stn, band_in):
    global SIXPACK
    # Ponemos todos los relés del SixPack a 0
    for e in SIXPACK[str(stn)]:
        topic = SIXPACK[str(stn)][e]['rele']
        mqtt_client.publish(topic, str(0))
    # Activamos los relés que correspondan del SixPack
    if band_in != 0:
        topic = SIXPACK[str(stn)][str(band_in)]['rele']
        mqtt_client.publish(topic, str(1))
        config_stack(band_in)


def clear_ant():
    assign_stn(1, 0)
    assign_stn(2, 0)


def assign_stn(stn, band):
    global STN1
    global STN2
    if stn == 1:
        STNX = STN1
        STNY = STN2
        STNZ = "2"
    else:
        STNX = STN2
        STNY = STN1
        STNZ = "1"
    if bool(SIXPACK[str(stn)][str(band)]['multiplex']) and bool(SIXPACK[STNZ][str(STNY['band'])]['multiplex']):
        both_multiplex = True
    else:
        both_multiplex = False
    if band != STNY['band'] and band != 0 and not both_multiplex:
        if STNX['band'] != band:
            assign_sixpack(STNX, stn, band)
        STNX['band'] = band
    else:
        assign_sixpack(STNX, stn, 0)
        STNX['band'] = 0
    if stn == 1:
        STN1 = STNX
    else:
        STN2 = STNX


def status(topic):
    data_json = json.dumps(
        {
            'stn1': STN1,
            'stn2': STN2,
            'stacks': STACKS,
            'sixpack': SIXPACK
        }, sort_keys=False
    )
    mqtt_client.publish(topic, str(data_json))


def change_stack(band, nro):
    if int(nro) != 0:
        if STACKS[str(band)][nro]['estado']:
            if nr_ant(STACKS[str(band)]) > 1:
                STACKS[str(band)][nro]['estado'] = False
        else:
            STACKS[str(band)][nro]['estado'] = True
    else:
        if STACKS[str(band)]["salidas"] > 1:
            ant_a = STACKS[str(band)]["1"]['estado']
            ant_b = STACKS[str(band)]["2"]['estado']
            ant_c = STACKS[str(band)]["3"]['estado']
            stack = [ant_a, ant_b, ant_c]
            if stack.count(True) == 1:
                if STACKS[str(band)]["salidas"] == 2 and STACKS[str(band)]["1"]['estado']:
                    STACKS[str(band)]["1"]['estado'] = False
                    STACKS[str(band)]["2"]['estado'] = True
                elif STACKS[str(band)]["salidas"] == 2 and STACKS[str(band)]["2"]['estado']:
                    STACKS[str(band)]["2"]['estado'] = False
                    STACKS[str(band)]["1"]['estado'] = True
                elif STACKS[str(band)]["salidas"] == 3 and STACKS[str(band)]["1"]['estado']:
                    STACKS[str(band)]["1"]['estado'] = False
                    STACKS[str(band)]["3"]['estado'] = False
                    STACKS[str(band)]["2"]['estado'] = True
                elif STACKS[str(band)]["salidas"] == 3 and STACKS[str(band)]["2"]['estado']:
                    STACKS[str(band)]["2"]['estado'] = False
                    STACKS[str(band)]["1"]['estado'] = False
                    STACKS[str(band)]["3"]['estado'] = True
                elif STACKS[str(band)]["salidas"] == 3 and STACKS[str(band)]["3"]['estado']:
                    STACKS[str(band)]["3"]['estado'] = False
                    STACKS[str(band)]["2"]['estado'] = False
                    STACKS[str(band)]["1"]['estado'] = True
            else:
                STACKS[str(band)]["2"]['estado'] = False
                STACKS[str(band)]["3"]['estado'] = False
                STACKS[str(band)]["1"]['estado'] = True
    config_stack(str(band))


def on_connect(client, userdata, flags, rc, more):
    print("Conectado a MQTT")
    client.subscribe([
        ("stn1/band", 0),
        ("stn2/band", 0),
        ("set/#", 0),
        ("update", 0)
    ])


def on_message(client, userdata, msg):
    global STN1
    global STN2
    global STACKS
    global SIXPACK

    dato = msg.payload.decode('utf-8')

    # Mensajes recibidos desde UDP
    if msg.topic == "stn1/band":
        if STN1['auto']:
            dato = json.loads(dato)
            assign_stn(1, dato[0])

    elif msg.topic == "stn2/band":
        if STN2['auto']:
            dato = json.loads(dato)
            assign_stn(2, dato[0])

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
    elif msg.topic == "set/stn1/stack" and int(STN1['band']) != 0:
        if int(dato) <= STACKS[str(STN1['band'])]['salidas']:
            change_stack(STN1['band'], dato)

    elif msg.topic == "set/stn2/stack" and int(STN2['band']) != 0:
        if int(dato) <= STACKS[str(STN2['band'])]['salidas']:
            change_stack(STN2['band'], dato)

    elif msg.topic == "set/stn1/nostack" and int(STN1['band']) != 0:
        if STACKS[str(STN1['band'])]["salidas"] > 1:
            change_stack(STN1['band'], 0)

    elif msg.topic == "set/stn2/nostack" and int(STN2['band']) != 0:
        if STACKS[str(STN2['band'])]["salidas"] > 1:
            change_stack(STN2['band'], 0)

    elif msg.topic == "set/stack160" and int(STN1['band']) != 160 and int(STN2['band']) != 160:
        if int(dato) <= STACKS[str(160)]['salidas']:
            change_stack(160, dato)

    elif msg.topic == "set/stack80" and int(STN1['band']) != 80 and int(STN2['band']) != 80:
        if int(dato) <= STACKS[str(80)]['salidas']:
            change_stack(80, dato)

    elif msg.topic == "set/stack40" and int(STN1['band']) != 40 and int(STN2['band']) != 40:
        if int(dato) <= STACKS[str(40)]['salidas']:
            change_stack(40, dato)

    elif msg.topic == "set/stack20" and int(STN1['band']) != 20 and int(STN2['band']) != 20:
        if int(dato) <= STACKS[str(17)]['salidas']:
            change_stack(20, dato)

    elif msg.topic == "set/stack15" and int(STN1['band']) != 15 and int(STN2['band']) != 15:
        if int(dato) <= STACKS[str(15)]['salidas']:
            change_stack(15, dato)

    elif msg.topic == "set/stack10" and int(STN1['band']) != 10 and int(STN2['band']) != 10:
        if int(dato) <= STACKS[str(10)]['salidas']:
            change_stack(10, dato)
    else:
        pass

    status("pytofront")


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP)
status("pytofront")
clear_ant()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
