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
#from gpiozero import LED

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

OUTS = {
    0: "N",
    160: "N",
    80: "N",
    40: "N",
    20: "N",
    15: "N",
    10: "N"
}
STACKS = {
    '0': {
        'salidas': 0,
        'balun': False,
        '1': {
            'estado': False,
            'nombre': "N/A"
        },
        '2': {
            'estado': False,
            'nombre': "N/A"
        },
        '3': {
            'estado': False,
            'nombre': "N/A"
        }
    },
    '160': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    },
    '80': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    },
    '40': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    },
    '20': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    },
    '15': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    },
    '10': {
        'salidas': 3,
        'balun': False,
        '1': {
            'estado': True,
            'nombre': "ANT1"
        },
        '2': {
            'estado': False,
            'nombre': "ANT2"
        },
        '3': {
            'estado': False,
            'nombre': "ANT3"
        }
    }
}
STN1 = {
    'netbios': "NETBIOS-STN1",
    'auto': True,
    'ant': 0,
    'band': 0,
    'rx': {
        '0': 0,
        '160': 0,
        '80': 0,
        '40': 0,
        '20': 0,
        '15': 0,
        '10': 0,
    }
}
STN2 = {
    'netbios': "NETBIOS-STN2",
    'auto': True,
    'ant': 0,
    'band': 0,
    'rx': {
        '0': 0,
        '160': 0,
        '80': 0,
        '40': 0,
        '20': 0,
        '15': 0,
        '10': 0,
    }
}

RX1 = {
    '1': "RX11",
    '2': "RX12",
    '3': "RX13",
    '4': "RX14",
    '5': "RX15",
    '6': "RX16",
}

RX2 = {
    '1': "RX21",
    '2': "RX22",
    '3': "RX23",
    '4': "RX24",
    '5': "RX25",
    '6': "RX26",
}

try:
    with open('cfg/stacks.json') as json_file:
        data = json.load(json_file)
        STACKS = dict(data)
        print("Datos de STACKS cargados desde fichero...")
except:
    if os.path.exists('cfg/stacks.json'):
        os.remove('cfg/stacks.json')
        print("Datos de STACKS autogenerados...")

try:
    with open('cfg/stn1.json') as json_file:
        data = json.load(json_file)
        STN1 = dict(data)
        print("Datos de STN1 cargados desde fichero...")
except:
    if os.path.exists('cfg/stn1.json'):
        os.remove('cfg/stn1.json')
        print("Datos de STN1 autogenerados...")

try:
    with open('cfg/stn2.json') as json_file:
        data = json.load(json_file)
        STN2 = dict(data)
        print("Datos de STN2 cargados desde fichero...")
except:
    if os.path.exists('cfg/stn2.json'):
        os.remove('cfg/stn2.json')
        print("Datos de STN1 autogenerados...")


try:
    with open('cfg/rx1.json') as json_file:
        data = json.load(json_file)
        RX1 = dict(data)
        print("Datos de STN1 cargados desde fichero...")
except:
    if os.path.exists('cfg/rx1.json'):
        os.remove('cfg/rx1.json')
        print("Datos de STN1 autogenerados...")

try:
    with open('cfg/rx2.json') as json_file:
        data = json.load(json_file)
        RX2 = dict(data)
        print("Datos de STN2 cargados desde fichero...")
except:
    if os.path.exists('cfg/stn2.json'):
        os.remove('cfg/rx2.json')
        print("Datos de STN1 autogenerados...")


def assign_stn(stn, band):
    global STN1
    global STN2
    global OUTS
    if stn == 1:
        STNX = STN1
        STNY = STN2
    if stn == 2:
        STNX = STN2
        STNY = STN1
    if band != STNY['band']:                    # Si la banda NO ESTÁ en uso
        if OUTS[band] == "N":                   # Si la salida NO ESTÁ bloqueada
            if STNX['band'] != band:            # Si se trata de una banda DIFERENTE
                #activate_ant_gpio(stn, band)   # Activo GPIO de antena
                pass
            OUTS[band] = str(stn)               # Bloqueo la salida para esa estación
            OUTS[STNX['ant']] = "N"             # Desbloquo la salida que tenía
            STNX['ant'] = band                  # Guardo que tiene una antena asignada
            STNX['band'] = band                 # Guardo que tiene una banda asignada
    else:                                       # Si la banda ESTÁ en uso
        #activate_ant_gpio(stn, 0)              # Desconecta antena
        OUTS[int(STNX['ant'])] = "N"            # Desbloquea la antena que tuviese asignada
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
    print(output)


def status(topic):
    data_json = json.dumps(
        {
            'stn1': STN1,
            'stn2': STN2,
            'stacks': STACKS,
            'rx1': RX1,
            'rx2': RX2
        }, sort_keys=False
    )
    print(data_json)
    #  MQTT broker -------------------------------------------------------------------------------------
    #
    mqtt_client.publish(topic, str(data_json))


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
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
        if STACKS[str(STN1['band'])]['1']['estado']: cc = cc + 1
        if STACKS[str(STN1['band'])]['2']['estado']: cc = cc + 1
        if STACKS[str(STN1['band'])]['3']['estado']: cc = cc + 1
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

    if msg.topic == "set/stn2/stack" and int(STN2['band']) != 0:
        cc = 0
        if STACKS[str(STN2['band'])]['1']['estado']: cc = cc + 1
        if STACKS[str(STN2['band'])]['2']['estado']: cc = cc + 1
        if STACKS[str(STN2['band'])]['3']['estado']: cc = cc + 1
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

    # Mensajes recibidos desde CONFIGURACION
    if msg.topic == "configtopy":
        dato = json.loads(dato)
        STACKS['160']['salidas'] = int(dato['a1600'])
        STACKS['160']['1']['nombre'] = dato['a1601']
        STACKS['160']['2']['nombre'] = dato['a1602']
        STACKS['160']['3']['nombre'] = dato['a1603']

        STACKS['80']['salidas'] = int(dato['a800'])
        STACKS['80']['1']['nombre'] = dato['a801']
        STACKS['80']['2']['nombre'] = dato['a802']
        STACKS['80']['3']['nombre'] = dato['a803']

        STACKS['40']['salidas'] = int(dato['a400'])
        STACKS['40']['1']['nombre'] = dato['a401']
        STACKS['40']['2']['nombre'] = dato['a402']
        STACKS['40']['3']['nombre'] = dato['a403']

        STACKS['20']['salidas'] = int(dato['a200'])
        STACKS['20']['1']['nombre'] = dato['a201']
        STACKS['20']['2']['nombre'] = dato['a202']
        STACKS['20']['3']['nombre'] = dato['a203']

        STACKS['15']['salidas'] = int(dato['a150'])
        STACKS['15']['1']['nombre'] = dato['a151']
        STACKS['15']['2']['nombre'] = dato['a152']
        STACKS['15']['3']['nombre'] = dato['a153']

        STACKS['10']['salidas'] = int(dato['a100'])
        STACKS['10']['1']['nombre'] = dato['a101']
        STACKS['10']['2']['nombre'] = dato['a102']
        STACKS['10']['3']['nombre'] = dato['a103']

        STN1['netbios'] = str(dato['stn1-n'])
        STN2['netbios'] = str(dato['stn2-n'])

        RX1['1'] = str(dato['r101'])
        RX1['2'] = str(dato['r102'])
        RX1['3'] = str(dato['r103'])
        RX1['4'] = str(dato['r104'])
        RX1['5'] = str(dato['r105'])
        RX1['6'] = str(dato['r106'])

        RX2['1'] = str(dato['r201'])
        RX2['2'] = str(dato['r202'])
        RX2['3'] = str(dato['r203'])
        RX2['4'] = str(dato['r204'])
        RX2['5'] = str(dato['r205'])
        RX2['6'] = str(dato['r206'])

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
