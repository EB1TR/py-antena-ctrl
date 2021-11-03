""" Six Pack & Filter Control """
#
# Six Pack & Filter Control
#

# pylint: disable=invalid-name;
# pylint: disable=too-few-public-methods;
# pylint: disable=C0301, R0912, R0914, R0915, R1702, W0703

__author__ = 'EB1TR'
__date__ = "12/09/2020"

import json
import paho.mqtt.client as mqtt
import os

MQTT_HOST = "192.168.33.63"
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
        print("Datos de STNs cargados desde ficheros...")
except Exception as e:
    print("Error en los ficheros de configuracion: %s" % e)


def config_stack(band):

    if STACKS[str(band)]['balun'] == False:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['tta'], STACKS[str(band)]['rele'])
        mqtt_client.publish(topic, str(0))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (STACKS[str(band)]['tta'], STACKS[str(band)]['rele'])
        mqtt_client.publish(topic, str(1))  

    for e in STACKS[str(band)]:
        if e['estado'] == False:
            topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (e['tta'], e['rele'])
            mqtt_client.publish(topic, str(0))
        else:
            topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (e['tta'], e['rele'])
            mqtt_client.publish(topic, str(1))  


def assign_sixpack(stn, band):
    el = SIXPACK[str(stn)]
    if stn == 1:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (el[str(STN1['band'])]['tta'], el[str(STN1['band'])]['rele'])
        mqtt_client.publish(topic, str(0))
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (el[str(band)]['tta'], el[str(band)]['rele'])
        mqtt_client.publish(topic, str(1))
    else:
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (el[str(STN2['band'])]['tta'], el[str(STN2['band'])]['rele'])
        mqtt_client.publish(topic, str(0))
        topic = "SmartDEN_MQTT16R/%s/Set/RS%s" % (el[str(band)]['tta'], el[str(band)]['rele'])
        mqtt_client.publish(topic, str(1))
    config_stack(band)


def assign_stn(stn, band):
    global STN1
    global STN2
    if stn == 1:
        STNX = STN1
        STNY = STN2
    else:
        STNX = STN2
        STNY = STN1
    if band != STNY['band']:                    # Si la banda NO ESTA en uso
        if STNX['band'] != band:            # Si se trata de una banda DIFERENTE
            assign_sixpack(stn, band)
            pass
        STNX['ant'] = band                  # Guardo que tiene una antena asignada
        STNX['band'] = band                 # Guardo que tiene una banda asignada
    else:                                       # Si la banda ESTA en uso
        assign_sixpack(stn, 0)
        STNX['ant'] = 0                         # Guardo que no tiene antena asignada
        STNX['band'] = 0                        # Gusardo que no tiene banda asignada

    if stn == 1:
        STN1 = STNX
    if stn == 2:
        STN2 = STNX


def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    #print(output)


def status(topic):
    data_json = json.dumps(
        {
            'stn1': STN1,
            'stn2': STN2,
            'stacks': STACKS,
            'sixpack': SIXPACK,
            'rx1': RX1,
            'rx2': RX2
        }, sort_keys=False
    )
    #print(data_json)
    #  MQTT broker -------------------------------------------------------------------------------------
    #
    mqtt_client.publish(topic, str(data_json))


def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT")
    client.subscribe([
        ("stn1/radio1/band", 0),
        ("stn2/radio1/band", 0),
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
    if msg.topic == "stn1/radio1/band":
        if STN1['auto']:
            assign_stn(1, int(dato))

    if msg.topic == "stn2/radio1/band":
        if STN2['auto']:
            assign_stn(2, int(dato))

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
            assign_stn(1, 0)

    if msg.topic == "set/stn2/antm":
        if STN2['auto']:
            STN2['auto'] = False
        else:
            STN2['auto'] = True
            assign_stn(2, 0)

    if msg.topic == "set/rx1" and not STN1['band'] == 0:
        STN1['rx'][str(STN1['band'])] = dato

    if msg.topic == "set/rx2" and not STN2['band'] == 0:
        STN2['rx'][str(STN2['band'])] = dato

    if msg.topic == "set/stn1/stack" and int(STN1['band']) != 0:
        cc = 0
        if STACKS[str(STN1['band'])]['1']['estado']:
            cc = cc + 1
        if STACKS[str(STN1['band'])]['2']['estado']:
            cc = cc + 1
        if STACKS[str(STN1['band'])]['3']['estado']:
            cc = cc + 1
        if STACKS[str(STN1['band'])][str(dato)]['estado'] and cc > 1:
            STACKS[str(STN1['band'])][str(dato)]['estado'] = False
            cc = cc - 1
        else:
            STACKS[str(STN1['band'])][str(dato)]['estado'] = True
            cc = cc + 1
        if cc > 1:
            STACKS[str(STN1['band'])]['balun'] = False
        else:
            STACKS[str(STN1['band'])]['balun'] = True
        
        config_stack(str(STN1['band']))

    if msg.topic == "set/stn2/stack" and int(STN2['band']) != 0:
        cc = 0
        if STACKS[str(STN2['band'])]['1']['estado']:
            cc = cc + 1
        if STACKS[str(STN2['band'])]['2']['estado']:
            cc = cc + 1
        if STACKS[str(STN2['band'])]['3']['estado']:
            cc = cc + 1
        if STACKS[str(STN2['band'])][str(dato)]['estado'] and cc > 1:
            STACKS[str(STN2['band'])][str(dato)]['estado'] = False
            cc = cc - 1
        else:
            STACKS[str(STN2['band'])][str(dato)]['estado'] = True
            cc = cc + 1
        if cc > 1:
            STACKS[str(STN2['band'])]['balun'] = False
        else:
            STACKS[str(STN2['band'])]['balun'] = True

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

        status("pytoconfig")

    if msg.topic == "update":
        status("pytoconfig")

    status("pytofront")


mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 600)
status("pytofront")
status("pytoconfig")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
