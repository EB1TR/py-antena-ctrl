""" Six Pack, Stack & RX Control """

__author__ = 'EB1TR'

import json
import paho.mqtt.client as mqtt
import os

MQTT_HOST = "mqtt"
MQTT_PORT = 1883


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

    if STACKS[str(band)]['1']['estado'] == False:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['1']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['1']['rele'])
        mqtt_client.publish(topic, str(1))  

    if STACKS[str(band)]['2']['estado'] == False:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['2']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['1']['tta'], STACKS[str(band)]['2']['rele'])
        mqtt_client.publish(topic, str(1))  

    if STACKS[str(band)]['3']['estado'] == False:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['3']['tta'], STACKS[str(band)]['3']['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['3']['tta'], STACKS[str(band)]['3']['rele'])
        mqtt_client.publish(topic, str(1))  

    if STACKS[str(band)]['balun'] == False:
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
        ("configtopy", 0)
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
            if dato[0] in (160, 80) and dato[1] != STN1['segmento'] and STACKS[str(STN1['band'])]['1']['estado'] == True:
                change_segment(1, dato[0], dato[1])

    if msg.topic == "stn2/band":
        if STN2['auto']:
            dato = json.loads(dato)
            assign_stn(2, dato[0])
            if dato[0] in (160, 80) and dato[1] != STN2['segmento'] and STACKS[str(STN1['band'])]['1']['estado'] == True:
                change_segment(2, dato[0], dato[1])

    # Mensajes recibidos desde FRONT
    if not STN1['auto'] and msg.topic == "set/stn1/band":
        dato = int(dato)
        assign_stn(1, dato)

    if not STN2['auto'] and msg.topic == "set/stn2/band":
        dato = int(dato)
        assign_stn(2, dato)

    if msg.topic == "set/stn1/antm":
        if STN1['auto']:
            STN1['auto'] = False
        else:
            STN1['auto'] = True

    if msg.topic == "set/stn2/antm":
        if STN2['auto']:
            STN2['auto'] = False
        else:
            STN2['auto'] = True

    if msg.topic == "set/rx1" and not STN1['band'] == 0:
        assign_rx(STN1, RX1, dato)
        STN1['rx'][str(STN1['band'])] = dato

    if msg.topic == "set/rx2" and not STN2['band'] == 0:
        assign_rx(STN2, RX2, dato)
        STN2['rx'][str(STN2['band'])] = dato

    if msg.topic == "set/stn1/stack" and int(STN1['band']) != 0:
        if STACKS[str(STN1['band'])][dato]['estado']:
            if nr_ant(STACKS[str(STN1['band'])]) > 1:
                STACKS[str(STN1['band'])][dato]['estado'] = False
        else:
            STACKS[str(STN1['band'])][dato]['estado'] = True

        config_stack(str(STN1['band']))

    if msg.topic == "set/stn2/stack" and int(STN2['band']) != 0:
        if STACKS[str(STN2['band'])][dato]['estado']:
            if nr_ant(STACKS[str(STN2['band'])]) > 1:
                STACKS[str(STN2['band'])][dato]['estado'] = False
        else:
            STACKS[str(STN2['band'])][dato]['estado'] = True

        config_stack(str(STN2['band']))

    # Mensajes recibidos desde CONFIGURACION
    if msg.topic == "configtopy":
        dato = json.loads(dato)

        STACKS['160']['salidas'] = int(dato['a1600'])
        STACKS['160']['tta'] = dato['a1600t']
        STACKS['160']['rele'] = int(dato['a1600r'])
        STACKS['160']['1']['nombre'] = dato['a1601']
        STACKS['160']['1']['tta'] = dato['a1601t']
        STACKS['160']['1']['rele'] = dato['a1601r']
        STACKS['160']['2']['nombre'] = dato['a1602']
        STACKS['160']['2']['tta'] = dato['a1602t']
        STACKS['160']['2']['rele'] = dato['a1602r']
        STACKS['160']['3']['nombre'] = dato['a1603']
        STACKS['160']['3']['tta'] = dato['a1603t']
        STACKS['160']['3']['rele'] = dato['a1603r']

        STACKS['80']['salidas'] = int(dato['a800'])
        STACKS['80']['tta'] = dato['a800t']
        STACKS['80']['rele'] = int(dato['a800r'])
        STACKS['80']['1']['nombre'] = dato['a801']
        STACKS['80']['1']['tta'] = dato['a801t']
        STACKS['80']['1']['rele'] = dato['a801r']
        STACKS['80']['2']['nombre'] = dato['a802']
        STACKS['80']['2']['tta'] = dato['a802t']
        STACKS['80']['2']['rele'] = dato['a802r']
        STACKS['80']['3']['nombre'] = dato['a803']
        STACKS['80']['3']['tta'] = dato['a803t']
        STACKS['80']['3']['rele'] = dato['a803r']

        STACKS['40']['salidas'] = int(dato['a400'])
        STACKS['40']['tta'] = dato['a400t']
        STACKS['40']['rele'] = int(dato['a400r'])
        STACKS['40']['1']['nombre'] = dato['a401']
        STACKS['40']['1']['tta'] = dato['a401t']
        STACKS['40']['1']['rele'] = dato['a401r']
        STACKS['40']['2']['nombre'] = dato['a402']
        STACKS['40']['2']['tta'] = dato['a402t']
        STACKS['40']['2']['rele'] = dato['a402r']
        STACKS['40']['3']['nombre'] = dato['a403']
        STACKS['40']['3']['tta'] = dato['a403t']
        STACKS['40']['3']['rele'] = dato['a403r']

        STACKS['20']['salidas'] = int(dato['a200'])
        STACKS['20']['tta'] = dato['a200t']
        STACKS['20']['rele'] = int(dato['a200r'])
        STACKS['20']['1']['nombre'] = dato['a201']
        STACKS['20']['1']['tta'] = dato['a201t']
        STACKS['20']['1']['rele'] = dato['a201r']
        STACKS['20']['2']['nombre'] = dato['a202']
        STACKS['20']['2']['tta'] = dato['a202t']
        STACKS['20']['2']['rele'] = dato['a202r']
        STACKS['20']['3']['nombre'] = dato['a203']
        STACKS['20']['3']['tta'] = dato['a203t']
        STACKS['20']['3']['rele'] = dato['a203r']

        STACKS['15']['salidas'] = int(dato['a150'])
        STACKS['15']['tta'] = dato['a150t']
        STACKS['15']['rele'] = int(dato['a150r'])
        STACKS['15']['1']['nombre'] = dato['a151']
        STACKS['15']['1']['tta'] = dato['a151t']
        STACKS['15']['1']['rele'] = dato['a151r']
        STACKS['15']['2']['nombre'] = dato['a152']
        STACKS['15']['2']['tta'] = dato['a152t']
        STACKS['15']['2']['rele'] = dato['a152r']
        STACKS['15']['3']['nombre'] = dato['a153']
        STACKS['15']['3']['tta'] = dato['a153t']
        STACKS['15']['3']['rele'] = dato['a153r']

        STACKS['10']['salidas'] = int(dato['a100'])
        STACKS['10']['tta'] = dato['a100t']
        STACKS['10']['rele'] = int(dato['a100r'])
        STACKS['10']['1']['nombre'] = dato['a101']
        STACKS['10']['1']['tta'] = dato['a101t']
        STACKS['10']['1']['rele'] = dato['a101r']
        STACKS['10']['2']['nombre'] = dato['a102']
        STACKS['10']['2']['tta'] = dato['a102t']
        STACKS['10']['2']['rele'] = dato['a102r']
        STACKS['10']['3']['nombre'] = dato['a103']
        STACKS['10']['3']['tta'] = dato['a103t']
        STACKS['10']['3']['rele'] = dato['a103r']

        SIXPACK['1']['10']['tta'] = dato['sp110t']
        SIXPACK['1']['10']['rele'] = dato['sp110r']
        SIXPACK['1']['15']['tta'] = dato['sp115t']
        SIXPACK['1']['15']['rele'] = dato['sp115r']
        SIXPACK['1']['20']['tta'] = dato['sp120t']
        SIXPACK['1']['20']['rele'] = dato['sp120r']
        SIXPACK['1']['40']['tta'] = dato['sp140t']
        SIXPACK['1']['40']['rele'] = dato['sp140r']
        SIXPACK['1']['80']['tta'] = dato['sp180t']
        SIXPACK['1']['80']['rele'] = dato['sp180r']
        SIXPACK['1']['160']['tta'] = dato['sp1160t']
        SIXPACK['1']['160']['rele'] = dato['sp1160r']

        SIXPACK['2']['10']['tta'] = dato['sp210t']
        SIXPACK['2']['10']['rele'] = dato['sp210r']
        SIXPACK['2']['15']['tta'] = dato['sp215t']
        SIXPACK['2']['15']['rele'] = dato['sp215r']
        SIXPACK['2']['20']['tta'] = dato['sp220t']
        SIXPACK['2']['20']['rele'] = dato['sp220r']
        SIXPACK['2']['40']['tta'] = dato['sp240t']
        SIXPACK['2']['40']['rele'] = dato['sp240r']
        SIXPACK['2']['80']['tta'] = dato['sp280t']
        SIXPACK['2']['80']['rele'] = dato['sp280r']
        SIXPACK['2']['160']['tta'] = dato['sp2160t']
        SIXPACK['2']['160']['rele'] = dato['sp2160r']

        for e in ('160', '80', '40', '20', '15', '10'):
            if STACKS[e]['salidas'] == 2:
                STACKS[e]['3']['estado'] = False
            elif STACKS[e]['salidas'] == 1:
                STACKS[e]['2']['estado'] = False
                STACKS[e]['3']['estado'] = False
            config_stack(e)

        STN1['netbios'] = str(dato['stn1-n'])
        STN2['netbios'] = str(dato['stn2-n'])

        RX1['1']['nombre'] = str(dato['r101'])
        RX1['1']['tta'] = str(dato['r101t'])
        RX1['1']['rele'] = str(dato['r101r'])
        RX1['2']['nombre'] = str(dato['r102'])
        RX1['2']['tta'] = str(dato['r102t'])
        RX1['2']['rele'] = str(dato['r102r'])
        RX1['3']['nombre'] = str(dato['r103'])
        RX1['3']['tta'] = str(dato['r103t'])
        RX1['3']['rele'] = str(dato['r103r'])
        RX1['4']['nombre'] = str(dato['r104'])
        RX1['4']['tta'] = str(dato['r104t'])
        RX1['4']['rele'] = str(dato['r104r'])
        RX1['5']['nombre'] = str(dato['r105'])
        RX1['5']['tta'] = str(dato['r105t'])
        RX1['5']['rele'] = str(dato['r105r'])
        RX1['6']['nombre'] = str(dato['r106'])
        RX1['6']['tta'] = str(dato['r106t'])
        RX1['6']['rele'] = str(dato['r106r'])

        RX2['1']['nombre'] = str(dato['r201'])
        RX2['1']['tta'] = str(dato['r201t'])
        RX2['1']['rele'] = str(dato['r201r'])
        RX2['2']['nombre'] = str(dato['r202'])
        RX2['2']['tta'] = str(dato['r202t'])
        RX2['2']['rele'] = str(dato['r202r'])
        RX2['3']['nombre'] = str(dato['r203'])
        RX2['3']['tta'] = str(dato['r203t'])
        RX2['3']['rele'] = str(dato['r203r'])
        RX2['4']['nombre'] = str(dato['r204'])
        RX2['4']['tta'] = str(dato['r204t'])
        RX2['4']['rele'] = str(dato['r204r'])
        RX2['5']['nombre'] = str(dato['r205'])
        RX2['5']['tta'] = str(dato['r205t'])
        RX2['5']['rele'] = str(dato['r205r'])
        RX2['6']['nombre'] = str(dato['r206'])
        RX2['6']['tta'] = str(dato['r206t'])
        RX2['6']['rele'] = str(dato['r206r'])

        SEGMENTOS['80']['1']['principio'] = dato['s801c']
        SEGMENTOS['80']['1']['fin'] = dato['s801f']
        SEGMENTOS['80']['1']['tta'] = str(dato['s801t'])
        SEGMENTOS['80']['1']['rele'] = dato['s801r']
        SEGMENTOS['80']['2']['principio'] = dato['s802c']
        SEGMENTOS['80']['2']['fin'] = dato['s802f']
        SEGMENTOS['80']['2']['tta'] = str(dato['s802t'])
        SEGMENTOS['80']['2']['rele'] = dato['s802r']
        SEGMENTOS['80']['3']['principio'] = dato['s803c']
        SEGMENTOS['80']['3']['fin'] = dato['s803f']
        SEGMENTOS['80']['3']['tta'] = str(dato['s803t'])
        SEGMENTOS['80']['3']['rele'] = dato['s803r']
        SEGMENTOS['80']['4']['principio'] = dato['s804c']
        SEGMENTOS['80']['4']['fin'] = dato['s804f']
        SEGMENTOS['80']['4']['tta'] = str(dato['s804t'])
        SEGMENTOS['80']['4']['rele'] = dato['s804r']

        SEGMENTOS['160']['1']['principio'] = dato['s1601c']
        SEGMENTOS['160']['1']['fin'] = dato['s1601f']
        SEGMENTOS['160']['1']['tta'] = str(dato['s1601t'])
        SEGMENTOS['160']['1']['rele'] = dato['s1601r']
        SEGMENTOS['160']['2']['principio'] = dato['s1602c']
        SEGMENTOS['160']['2']['fin'] = dato['s1602f']
        SEGMENTOS['160']['2']['tta'] = str(dato['s1602t'])
        SEGMENTOS['160']['2']['rele'] = dato['s1602r']
        SEGMENTOS['160']['3']['principio'] = dato['s1603c']
        SEGMENTOS['160']['3']['fin'] = dato['s1603f']
        SEGMENTOS['160']['3']['tta'] = str(dato['s1603t'])
        SEGMENTOS['160']['3']['rele'] = dato['s1603r']
        SEGMENTOS['160']['4']['principio'] = dato['s1604c']
        SEGMENTOS['160']['4']['fin'] = dato['s1604f']
        SEGMENTOS['160']['4']['tta'] = str(dato['s1604t'])
        SEGMENTOS['160']['4']['rele'] = dato['s1604r']

        with open('cfg/stacks.json', 'w') as fp:
            json.dump(STACKS, fp, indent=4, separators=(", ", ": "))
        with open('cfg/stn1.json', 'w') as fp:
            json.dump(STN1, fp, indent=4, separators=(", ", ": "))
        with open('cfg/stn2.json', 'w') as fp:
            json.dump(STN2, fp, indent=4, separators=(", ", ": "))
        with open('cfg/rx1.json', 'w') as fp:
            json.dump(RX1, fp, indent=4, separators=(", ", ": "))
        with open('cfg/rx2.json', 'w') as fp:
            json.dump(RX2, fp, indent=4, separators=(", ", ": "))
        with open('cfg/sixpack.json', 'w') as fp:
            json.dump(SIXPACK, fp, indent=4, separators=(", ", ": "))
        with open('cfg/segmentos.json', 'w') as fp:
            json.dump(SEGMENTOS, fp, indent=4, separators=(", ", ": "))

        status("pytoconfig")

    if msg.topic == "update":
        status("pytoconfig")

    status("pytofront")


mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 600)
status("pytofront")
status("pytoconfig")
clear_ant()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
