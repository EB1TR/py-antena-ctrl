"""MQTT adapter for the feedback-driven antenna controller."""

import json
import logging
import os
import queue
import sys
import threading
import time

import paho.mqtt.client as mqtt

import settings
from controller import Controller
from state_store import StateStore


LOG = logging.getLogger('control')


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    config = settings.load_config()
    observe_only = os.environ.get('CONTROL_OBSERVE_ONLY', '0') == '1'
    events = queue.Queue(maxsize=2048)
    overflow = threading.Event()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clean_session=True)
    last_warning = {}

    def publish(topic, payload):
        if observe_only:
            if topic in ('pytofront', 'control/health', 'control/config', 'control/heartbeat', 'control/availability'):
                topic = 'control/shadow/' + ('state' if topic == 'pytofront' else topic.split('/')[-1])
            elif not topic.endswith('/Set/GetStatus'):
                return
        retained = topic == 'pytofront' or topic.endswith(('/config', '/health', '/availability', '/state'))
        client.publish(topic, payload, retain=retained)

    controller = Controller(config, publish, actuation_enabled=not observe_only)
    store = StateStore(config.state_path)
    saved_state = store.load()
    if saved_state is not None:
        controller.restore_state(saved_state)
        LOG.info('Estado operativo recuperado de %s; pendiente de confirmar hardware', config.state_path)

    def persist_state():
        if observe_only or not controller.connected or not controller.baseline_ready:
            return
        try:
            store.save(controller.export_state())
        except OSError as error:
            now = time.monotonic()
            if now - last_warning.get('state_storage', -100) >= 5:
                LOG.error('No se puede guardar el estado en %s: %s', config.state_path, error)
                last_warning['state_storage'] = now

    def enqueue(event):
        try:
            events.put_nowait(event)
        except queue.Full:
            if not overflow.is_set():
                LOG.error('Cola MQTT llena: se invalida el estado y se reconecta para releer los relés')
            overflow.set()

    def on_connect(client, userdata, flags, code, properties):
        if code != 0:
            LOG.error('MQTT rechazó la conexión: %s', code)
            return
        subscriptions = ['stn1/band', 'stn2/band', 'stn1/tx', 'stn2/tx',
                         'set/#', 'update', 'control/resync']
        subscriptions.extend(sorted(controller.feedback))
        subscriptions.extend(board + '/Get/Status' for board in controller.boards)
        subscriptions.extend(sorted({relay.split('/in/')[0] + '/out/lwt_availability'
                                     for relay in controller.relays if '/in/' in relay}))
        client.subscribe([(topic, 0) for topic in subscriptions])
        publish('control/availability', 'online')
        enqueue(('connect',))

    def on_disconnect(client, userdata, flags, code, properties):
        enqueue(('disconnect',))

    def on_message(client, userdata, message):
        enqueue(('message', message.topic, message.payload, message.retain))

    client.on_connect, client.on_disconnect, client.on_message = on_connect, on_disconnect, on_message
    client.will_set('control/shadow/availability' if observe_only else 'control/availability', 'offline', retain=True)
    client.connect_async(config.mqtt_host, config.mqtt_port, config.mqtt_keepalive)
    client.loop_start()
    LOG.info('Control con feedback iniciado%s', ' en observación (sin accionar relés)' if observe_only else '')
    previous = None
    try:
        while True:
            if overflow.is_set():
                controller.disconnect()
                client.disconnect(); client.loop_stop()
                while not events.empty():
                    try: events.get_nowait()
                    except queue.Empty: break
                overflow.clear()
                client.connect_async(config.mqtt_host, config.mqtt_port, config.mqtt_keepalive)
                client.loop_start()
                continue
            try:
                event = events.get(timeout=.1)
            except queue.Empty:
                event = None
            if event:
                if event[0] == 'connect':
                    controller.reconnect(); LOG.info('MQTT conectado; solicitando estado real de los relés')
                elif event[0] == 'disconnect':
                    controller.disconnect(); LOG.warning('MQTT desconectado; confirmaciones invalidadas')
                else:
                    try:
                        controller.handle(*event[1:])
                    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
                        now = time.monotonic()
                        if now - last_warning.get(event[1], -100) >= 5:
                            LOG.warning('Mensaje inválido en %s: %s', event[1], error)
                            last_warning[event[1]] = now
            # Checkpoint changed preferences before asking hardware to follow them;
            # checkpoint the resulting observations/diagnostics after alignment.
            persist_state()
            controller.tick()
            persist_state()
            summary = tuple((station, controller.requests[station], controller.confirmed_band(station))
                            for station in controller.stations)
            if summary != previous:
                LOG.info('Bandas (estación, solicitada, confirmada): %s', summary)
                previous = summary
    except KeyboardInterrupt:
        LOG.info('Finalizando control')
    finally:
        publish('control/availability', 'offline')
        client.disconnect(); client.loop_stop()


if __name__ == '__main__':
    main()
