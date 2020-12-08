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
<<<<<<< HEAD
from gpiozero import LED
import os

import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c)



MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

try:
    with open('config.json') as json_file:
        data = json.load(json_file)
        CONFIG = dict(data)
        print("Datos de configuracion cargados desde fichero...")
except:
    if os.path.exists('cfg/stacks.json'):
        os.remove('cfg/stacks.json')
        print("Fallo en la carga de fichero de configuracion...")
=======
import os
#from gpiozero import LED

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
>>>>>>> monobanda

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

<<<<<<< HEAD
ANT = {
    6: CONFIG["nombre-antena6"],
    5: CONFIG["nombre-antena5"],
    4: CONFIG["nombre-antena4"],
    3: CONFIG["nombre-antena3"],
    2: CONFIG["nombre-antena2"],
    1: CONFIG["nombre-antena1"],
    0: "N/A"
}

ants10 = []
ants15 = []
ants20 = []
ants40 = []
ants80 = []
ants160 = []
for e in CONFIG["sp-10"]:
    ants10.append(e)
for e in CONFIG["sp-15"]:
    ants15.append(e)
for e in CONFIG["sp-20"]:
    ants20.append(e)
for e in CONFIG["sp-40"]:
    ants40.append(e)
for e in CONFIG["sp-80"]:
    ants80.append(e)
for e in CONFIG["sp-160"]:
    ants160.append(e)
SP = {
    10: ants10,
    15: ants15,
    20: ants20,
    40: ants40,
    80: ants80,
    160: ants160,
    0: [0]
}

# GPIOs al SixPack A
rpi_gpio1 = LED(4)
rpi_gpio2 = LED(17)
rpi_gpio3 = LED(27)
rpi_gpio4 = LED(22)
rpi_gpio5 = LED(10)
rpi_gpio6 = LED(9)
# GPIOs al SixPack B
rpi_gpio7 = LED(11)
rpi_gpio8 = LED(5)
rpi_gpio9 = LED(6)
rpi_gpio10 = LED(13)
rpi_gpio11 = LED(19)
rpi_gpio12 = LED(26)
# GPIOs a Filtros A
rpi_gpio13 = LED(14)
rpi_gpio14 = LED(15)
rpi_gpio15 = LED(18)
rpi_gpio16 = LED(23)
rpi_gpio17 = LED(24)
rpi_gpio18 = LED(25)
# GPIOs a Filtros B
rpi_gpio19 = LED(8)
rpi_gpio20 = LED(7)
rpi_gpio21 = LED(12)
rpi_gpio22 = LED(16)
rpi_gpio23 = LED(20)
rpi_gpio24 = LED(21)

# GPIOS expansion
ext_gpio0 = mcp.get_pin(0)
ext_gpio1 = mcp.get_pin(1)
ext_gpio2 = mcp.get_pin(2)
ext_gpio3 = mcp.get_pin(3)
ext_gpio4 = mcp.get_pin(4)
ext_gpio5 = mcp.get_pin(5)
ext_gpio6 = mcp.get_pin(6)
ext_gpio7 = mcp.get_pin(7)
ext_gpio8 = mcp.get_pin(8)
ext_gpio9 = mcp.get_pin(9)
ext_gpio10 = mcp.get_pin(10)
ext_gpio11 = mcp.get_pin(11)
ext_gpio12 = mcp.get_pin(12)
ext_gpio13 = mcp.get_pin(13)
ext_gpio14 = mcp.get_pin(14)
ext_gpio15 = mcp.get_pin(15)
ext_gpio0.switch_to_output(value=False)
ext_gpio1.switch_to_output(value=False)
ext_gpio2.switch_to_output(value=False)
ext_gpio3.switch_to_output(value=False)
ext_gpio4.switch_to_output(value=False)
ext_gpio5.switch_to_output(value=False)
ext_gpio6.switch_to_output(value=False)
ext_gpio7.switch_to_output(value=False)
ext_gpio8.switch_to_output(value=False)
ext_gpio9.switch_to_output(value=False)
ext_gpio10.switch_to_output(value=False)
ext_gpio11.switch_to_output(value=False)
ext_gpio12.switch_to_output(value=False)
ext_gpio13.switch_to_output(value=False)
ext_gpio14.switch_to_output(value=False)
ext_gpio15.switch_to_output(value=False)


def activate_ant_gpio(stn, new):
    if stn == 1:
        rpi_gpio1.off()
        rpi_gpio2.off()
        rpi_gpio3.off()
        rpi_gpio4.off()
        rpi_gpio5.off()
        rpi_gpio6.off()
        if new == 1:
            rpi_gpio1.on()
        if new == 2:
            rpi_gpio2.on()
        if new == 3:
            rpi_gpio3.on()
        if new == 4:
            rpi_gpio4.on()
        if new == 5:
            rpi_gpio5.on()
        if new == 6:
            rpi_gpio6.on()
    if stn == 2:
        rpi_gpio7.off()
        rpi_gpio8.off()
        rpi_gpio9.off()
        rpi_gpio10.off()
        rpi_gpio11.off()
        rpi_gpio12.off()
        if new == 1:
            rpi_gpio7.on()
        if new == 2:
            rpi_gpio8.on()
        if new == 3:
            rpi_gpio9.on()
        if new == 4:
            rpi_gpio10.on()
        if new == 5:
            rpi_gpio11.on()
        if new == 6:
            rpi_gpio12.on()


def activate_fil_gpio(stn, new):
    if stn == 1:
        rpi_gpio13.off()
        rpi_gpio14.off()
        rpi_gpio15.off()
        rpi_gpio16.off()
        rpi_gpio17.off()
        rpi_gpio18.off()
        if new == 1:
            rpi_gpio13.on()
        if new == 2:
            rpi_gpio14.on()
        if new == 3:
            rpi_gpio15.on()
        if new == 4:
            rpi_gpio16.on()
        if new == 5:
            rpi_gpio17.on()
        if new == 6:
            rpi_gpio18.on()
    if stn == 2:
        rpi_gpio19.off()
        rpi_gpio20.off()
        rpi_gpio21.off()
        rpi_gpio22.off()
        rpi_gpio23.off()
        rpi_gpio24.off()
        if new == 1:
            rpi_gpio19.on()
        if new == 2:
            rpi_gpio20.on()
        if new == 3:
            rpi_gpio21.on()
        if new == 4:
            rpi_gpio22.on()
        if new == 5:
            rpi_gpio23.on()
        if new == 6:
            rpi_gpio24.on()


def rpi(cmd):
    if cmd == "reboot":
        print("Reiniciando")
        os.system('sudo shutdown -r now')
    elif cmd == "shutdown":
        print("Apagando")
        os.system('sudo shutdown -h now')


def swap(stn):
    global STN1
    global STN2
    global OUTS
    global SP

    stn1_pre_swap = STN1['ant']
    stn2_pre_swap = STN2['ant']

    if STN1['ant'] in SP[STN2['band']] and STN2['ant'] in SP[STN1['band']]:
        STN1['ant'] = stn2_pre_swap
        activate_ant_gpio(1, stn2_pre_swap)
        OUTS[stn2_pre_swap] = "1"
        STN2['ant'] = stn1_pre_swap
        OUTS[stn1_pre_swap] = "2"
        activate_ant_gpio(2, stn1_pre_swap)

    elif int(stn) == 1 and len(SP[STN1['band']]) == 2 and int(STN2['ant']) not in SP[STN1['band']]:
        if STN1['ant'] == SP[STN1['band']][0]:
            STN1['ant'] = SP[STN1['band']][1]
            OUTS[SP[STN1['band']][0]] = "N"
            OUTS[SP[STN1['band']][1]] = "1"
            activate_ant_gpio(stn, SP[STN1['band']][1])
        elif STN1['ant'] == SP[STN1['band']][1]:
            STN1['ant'] = SP[STN1['band']][0]
            OUTS[SP[STN1['band']][1]] = "N"
            OUTS[SP[STN1['band']][0]] = "1"
            activate_ant_gpio(stn, SP[STN1['band']][0])

    elif int(stn) == 2 and len(SP[STN2['band']]) == 2 and int(STN1['ant']) not in SP[STN2['band']]:
        if STN2['ant'] == SP[STN2['band']][0]:
            STN2['ant'] = SP[STN2['band']][1]
            OUTS[SP[STN2['band']][0]] = "N"
            OUTS[SP[STN2['band']][1]] = "2"
            activate_ant_gpio(stn, SP[STN2['band']][1])
        elif STN2['ant'] == SP[STN2['band']][1]:
            STN2['ant'] = SP[STN2['band']][0]
            OUTS[SP[STN2['band']][1]] = "N"
            OUTS[SP[STN2['band']][0]] = "2"
            activate_ant_gpio(stn, SP[STN2['band']][0])
=======
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
>>>>>>> monobanda


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
<<<<<<< HEAD
    if band in SP and band != STNY['band']:
        if not STNX['ant'] in SP[band] or STNX['band'] != band:
            for e in SP[band]:
                if OUTS[e] == "N":
                    if STNX['band'] != band:
                        activate_ant_gpio(stn, e)
                    OUTS[e] = str(stn)
                    OUTS[STNX['ant']] = "N"
                    STNX['ant'] = e
                    STNX['antname'] = ANT[e]
                    STNX['band'] = band
                    break
                elif OUTS[e] == str(stn):
                    STNX['band'] = band
                    break
        else:
            STNX['band'] = band
    else:
        activate_ant_gpio(stn, 0)
        OUTS[STNX['ant']] = "N"
        STNX['ant'] = 0
        STNX['antname'] = "--"
        STNX['band'] = 0
=======
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
>>>>>>> monobanda

    if stn == 1:
        STN1 = STNX
    if stn == 2:
        STN2 = STNX


<<<<<<< HEAD
def assign_filter(stn, band):
    global STN1
    global STN2
    global FIL
    if stn == 1:
        STNX = STN1
    if stn == 2:
        STNX = STN2
    if band in FIL:
        if STNX['fil'] != FIL[band]:
            activate_fil_gpio(stn, FIL[band])
            STNX['fil'] = FIL[band]
    else:
        activate_fil_gpio(stn, FIL[band])
        STNX['fil'] = 0
    if stn == 1:
        STN1 = STNX
    if stn == 2:
        STN2 = STNX
=======
def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)
>>>>>>> monobanda


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
    print("CTL " + str(data_json))
    #  MQTT broker -------------------------------------------------------------------------------------
    #
    mqtt_client.publish(topic, str(data_json))


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe([
        ("stn1/radio1/band", 0),
        ("stn2/radio1/band", 0),
<<<<<<< HEAD
        ("set/stn1/ant", 0),
        ("set/stn1/fil", 0),
        ("set/stn2/ant", 0),
        ("set/stn2/fil", 0),
        ("set/stn1/antm", 0),
        ("set/stn2/antm", 0),
        ("set/stn1/film", 0),
        ("set/stn2/film", 0),
        ("set/stn1/band", 0),
        ("set/stn2/band", 0),
        ("set/stn1/swap", 0),
        ("set/stn2/swap", 0),
        ("set/rpi", 0),
        ("update", 0)
=======
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
>>>>>>> monobanda
    ])


def on_message(client, userdata, msg):
    global STN1
    global STN2
<<<<<<< HEAD
    global OUTS
    global FIL
    global SP

    dato = msg.payload.decode('utf-8')

    try:
        dato = int(dato)
    except:
        pass

    if msg.topic == "stn1/radio1/band":
        if STN1['auto']:
            assign_stn(1, dato)
        if STN1['bpf']:
            assign_filter(1, dato)

    if msg.topic == "stn2/radio1/band":
        if STN2['auto']:
            assign_stn(2, dato)
        if STN2['bpf']:
            assign_filter(2, dato)

    if not STN1['auto'] and msg.topic == "set/stn1/ant":
        if OUTS[dato] == "N" or dato == 0:
            activate_ant_gpio(1, dato)
            OUTS[dato] = "1"
            OUTS[STN1['ant']] = "N"
            STN1['ant'] = dato
            STN1['antname'] = ANT[dato]
            STN1['band'] = 0

    if not STN2['auto'] and msg.topic == "set/stn2/ant":
        if OUTS[dato] == "N" or dato == 0:
            activate_ant_gpio(2, dato)
            OUTS[dato] = "2"
            OUTS[STN2['ant']] = "N"
            STN2['ant'] = dato
            STN2['antname'] = ANT[dato]
            STN2['band'] = 0
=======
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
>>>>>>> monobanda

    # Mensajes recibidos desde FRONT
    if not STN1['auto'] and msg.topic == "set/stn1/band":
        assign_stn(1, dato)

    if not STN2['auto'] and msg.topic == "set/stn2/band":
        assign_stn(2, dato)

<<<<<<< HEAD
    if not STN1['bpf'] and msg.topic == "set/stn1/fil":
        assign_filter(1, dato)

    if not STN2['bpf'] and msg.topic == "set/stn2/fil":
        assign_filter(2, dato)

=======
>>>>>>> monobanda
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
<<<<<<< HEAD

    if msg.topic == "set/stn1/film":
        if STN1['bpf']:
            STN1['bpf'] = False
            assign_filter(1, 0)
        else:
            STN1['bpf'] = True

    if msg.topic == "set/stn2/film":
        if STN2['bpf']:
            STN2['bpf'] = False
            assign_filter(2, 0)
        else:
            STN2['bpf'] = True

    if msg.topic == "set/stn1/swap":
        swap(1)

    if msg.topic == "set/stn2/swap":
        swap(2)
    
    if msg.topic == "set/rpi":
        rpi(dato)

    status()
=======
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
>>>>>>> monobanda


mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 600)
status("pytofront")
status("pytoconfig")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_forever()
