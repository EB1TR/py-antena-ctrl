"""Feedback-driven antenna selection. Publishing a command never confirms a relay."""

from copy import deepcopy
import json
import logging
import re
import time

from protocol import ControlPublisher


LOG = logging.getLogger('control.relays')


def real_topic(topic):
    return bool(topic and topic != 'rele_dummy')


def feedback_topic(topic):
    if re.search(r'/Set/RS\d+$', topic):
        return re.sub(r'/Set/RS(\d+)$', r'/Get/R\1', topic)
    if re.search(r'/in/r\d+$', topic):
        return topic.replace('/in/', '/out/')
    raise ValueError(f'Relé sin protocolo de feedback conocido: {topic}')


def boolean(payload):
    value = str(payload).strip().lower()
    if value in ('1', 'on', 'true'):
        return True
    if value in ('0', 'off', 'false'):
        return False
    return None


class Controller:
    def __init__(self, config, publish, clock=time.monotonic, actuation_enabled=True):
        self.publish, self.clock = publish, clock
        self.output = ControlPublisher(publish, clock)
        self.actuation_enabled = actuation_enabled
        self.stations = {'stn1': deepcopy(config.stn1), 'stn2': deepcopy(config.stn2)}
        for state in self.stations.values(): state.pop('segmento', None)
        self.sixpack, self.stacks = deepcopy(config.sixpack), deepcopy(config.stacks)
        self.requests = {s: int(state.get('band', 0)) for s, state in self.stations.items()}
        self.radio_bands, self.band_times, self.tx, self.tx_times = {}, {}, {}, {}
        self.groups = {s: {v['rele'] for v in self.sixpack[str(i)].values() if real_topic(v['rele'])}
                       for i, s in enumerate(self.stations, 1)}
        self.stack_relays = {}
        for band, stack in self.stacks.items():
            self.stack_relays[int(band)] = {entry['rele'] for entry in [stack] + [stack[str(i)] for i in range(1, 4)]
                                            if real_topic(entry['rele'])}
        self.relays = set().union(*self.groups.values(), *self.stack_relays.values())
        self.power_relays = {s: state['rele'] for s, state in self.stations.items() if real_topic(state.get('rele'))}
        self.relays.update(self.power_relays.values())
        self.feedback = {feedback_topic(topic): topic for topic in self.relays}
        self.boards = {topic.split('/Set/')[0] for topic in self.relays if '/Set/' in topic}
        self.observed, self.observed_at, self.online = {}, {}, {}
        self.sent, self.faults, self.conflicts, self.power_targets = {}, {}, {}, {}
        self.prepared = set()
        self.initialized_stacks = set()
        self.last_poll = -100
        self.last_snapshot, self.last_status_time = None, -100
        self.connected = False
        self.baseline_ready = False
        self.changed_boards = set()

    def actual(self, topic):
        if topic not in self.observed:
            return None
        if '/Set/' in topic and self.clock() - self.observed_at.get(topic, -100) > 15:
            return None
        return self.observed[topic]

    def reconnect(self):
        self.output.reset()
        self.connected = True
        self.baseline_ready = False
        self.observed.clear(); self.observed_at.clear(); self.sent.clear(); self.faults.clear()
        self.online.clear(); self.last_poll = -100
        self.radio_bands.clear(); self.band_times.clear(); self.tx.clear(); self.tx_times.clear()

    def disconnect(self):
        self.connected = False
        self.baseline_ready = False
        self.observed.clear(); self.observed_at.clear()
        self.radio_bands.clear(); self.band_times.clear(); self.tx.clear(); self.tx_times.clear()

    def route(self, station, band):
        entry = self.sixpack[station[-1]].get(str(band))
        return entry['rele'] if entry and real_topic(entry['rele']) else None

    def receive_safe(self, station):
        return self.tx.get(station) is False and self.clock() - self.tx_times.get(station, -100) < 5

    def request_band(self, station, band):
        if type(band) is not int or str(band) not in self.sixpack[station[-1]]:
            raise ValueError('Banda no configurada')
        other = 'stn2' if station == 'stn1' else 'stn1'
        other_band = self.requests[other]
        multiplex = self.sixpack[station[-1]][str(band)]['multiplex']
        other_multiplex = self.sixpack[other[-1]][str(other_band)]['multiplex']
        observed_other_claim = False
        if self.stations[other]['auto'] and other not in self.radio_bands and band:
            selector = self.route(other, band)
            observed_other_claim = selector is not None and self.actual(selector) is True
        conflict = band != 0 and (observed_other_claim or band == other_band or (multiplex and other_multiplex))
        self.requests[station] = 0 if conflict else band
        self.conflicts[station] = 'Banda o multiplexor ocupado por la otra estación' if conflict else None

    def stack_change(self, band, output):
        self.initialized_stacks.add(band)
        stack = self.stacks[str(band)]
        count = int(stack['salidas'])
        if not 0 <= output <= count:
            raise ValueError('Salida no configurada')
        active = [i for i in range(1, count + 1) if stack[str(i)]['estado']]
        if output:
            if output not in active:
                stack[str(output)]['estado'] = True
            elif len(active) > 1:
                stack[str(output)]['estado'] = False
        elif count > 1:
            selected = active[0] % count + 1 if len(active) == 1 else 1
            for i in range(1, count + 1):
                stack[str(i)]['estado'] = i == selected
        self.prepared.add(band)

    def handle(self, topic, payload, retained=False):
        now = self.clock()
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        # Device state is the only source of actual relay values.
        command_topic = self.feedback.get(topic)
        if command_topic:
            board = command_topic.split('/in/')[0] if '/in/' in command_topic else command_topic.split('/Set/')[0]
            if retained and self.online.get(board) is False:
                return
            if retained and '/Set/' in command_topic:
                return  # Denkovi cached states must be refreshed by GetStatus.
            value = boolean(payload)
            if value is None:
                raise ValueError('Feedback inválido')
            previous = self.actual(command_topic)
            self.observed[command_topic], self.observed_at[command_topic] = value, now
            if previous is not None and previous != value:
                LOG.info('Feedback %s: %s -> %s', command_topic, int(previous), int(value))
            if not retained: self.online[board] = True
            # Bootstrap stack preferences once from real relay states, not stale JSON.
            for band, stack in self.stacks.items():
                number = int(band)
                if number in self.initialized_stacks: continue
                outputs = [stack[str(i)] for i in range(1, int(stack['salidas']) + 1)]
                if not outputs or not any(entry['rele'] == command_topic for entry in outputs): continue
                values = [self.actual(entry['rele']) if real_topic(entry['rele']) else bool(entry['estado']) for entry in outputs]
                if any(item is None for item in values): continue
                if any(values):
                    for entry, actual in zip(outputs, values): entry['estado'] = bool(actual)
                self.initialized_stacks.add(number)
            if self.sent.get(command_topic, (None,))[0] == value:
                LOG.info('Orden confirmada: %s=%s', command_topic, int(value))
                self.sent.pop(command_topic, None); self.faults.pop(command_topic, None)
            for station, power in self.power_relays.items():
                if power == command_topic:
                    self.stations[station]['rig'] = int(value)
                    if self.power_targets.get(power) == value:
                        self.power_targets.pop(power, None)
            return
        if topic.endswith('/Get/Status') or topic.endswith('/out/lwt_availability'):
            if retained and topic.endswith('/Get/Status'):
                return  # A stale Disconnected LWT is not proof of current disconnection.
            board = topic.rsplit('/Get/', 1)[0] if '/Get/' in topic else topic.rsplit('/out/', 1)[0]
            state = payload.strip().lower()
            if state in ('disconnected', 'offline', 'rebooted'):
                self.online[board] = False
                for relay in self.relays:
                    if relay.startswith(board + '/'):
                        self.observed.pop(relay, None); self.observed_at.pop(relay, None)
            elif state in ('connected', 'online'):
                if self.online.get(board) is not True:
                    for relay in list(self.sent):
                        if relay.startswith(board + '/'):
                            self.sent.pop(relay, None); self.faults.pop(relay, None)
                    self.last_poll = -100
                self.online[board] = True
            return
        if retained and (topic.startswith('set/') or topic == 'control/resync'):
            return
        match = re.fullmatch(r'(stn[12])/(band|tx)', topic)
        if match:
            if retained: return  # Cached radio state is not current proof that it is safe to switch.
            station, field = match.groups()
            if field == 'tx':
                value = boolean(payload)
                if value is None: raise ValueError('Estado TX inválido')
                self.tx[station], self.tx_times[station] = value, now
            else:
                data = json.loads(payload)
                # Read older publishers during a rolling update; never store a segment.
                band = data[0] if isinstance(data, list) and len(data) == 2 else data
                if type(band) is not int:
                    raise ValueError('La banda debe ser un entero')
                if str(band) not in self.sixpack[station[-1]]: raise ValueError('Banda desconocida')
                self.radio_bands[station], self.band_times[station] = band, now
                if self.stations[station]['auto']: self.request_band(station, band)
            return
        match = re.fullmatch(r'set/(stn[12])/(antm|band|stack|nostack|rig)', topic)
        if match:
            station, action = match.groups()
            if action == 'antm':
                self.stations[station]['auto'] = not self.stations[station]['auto']
                if self.stations[station]['auto'] and station in self.radio_bands:
                    self.request_band(station, self.radio_bands[station] if now - self.band_times.get(station, -100) < 5 else 0)
            elif action == 'band' and not self.stations[station]['auto']:
                self.request_band(station, int(payload))
            elif action in ('stack', 'nostack') and self.requests[station]:
                self.stack_change(self.requests[station], int(payload) if action == 'stack' else 0)
            elif action == 'rig':
                relay = self.power_relays[station]
                current = self.actual(relay)
                if current is None: raise ValueError('Sin feedback del relé de alimentación')
                self.power_targets[relay] = not current
            # An explicit user command allows a new, bounded alignment attempt.
            self.sent.clear(); self.faults.clear()
            return
        match = re.fullmatch(r'set/stack(\d+)', topic)
        if match:
            band = int(match[1])
            if band not in self.requests.values() and str(band) in self.stacks:
                self.stack_change(band, int(payload))
                self.sent.clear(); self.faults.clear()
        if topic == 'control/resync':
            self.sent.clear(); self.faults.clear(); self.last_poll = -100
        if topic == 'update':
            self.output.force = True
            self.last_status_time = -100

    def stack_targets(self, band):
        stack = self.stacks[str(band)]
        result = {}
        active = sum(bool(stack[str(i)]['estado']) for i in range(1, int(stack['salidas']) + 1))
        for i in range(1, 4):
            entry = stack[str(i)]
            if real_topic(entry['rele']):
                result[entry['rele']] = i <= int(stack['salidas']) and bool(entry['estado'])
        stack['balun'] = active > 1
        if real_topic(stack['rele']): result[stack['rele']] = active > 1
        return result

    def is_multiplex(self, band):
        return any(self.sixpack[str(i)].get(str(band), {}).get('multiplex') for i in (1, 2))

    def stack_plan(self):
        bands = {band for band in self.requests.values() if band} | {band for band in self.prepared if not self.is_multiplex(band)}
        result = {}
        if any(self.is_multiplex(band) for band in bands):
            for band in map(int, self.stacks):
                if self.is_multiplex(band):
                    result.update({relay: False for relay in self.stack_relays[band]})
        for band in sorted(bands): result.update(self.stack_targets(band))
        return result

    def matches(self, targets):
        return all(self.actual(relay) == value for relay, value in targets.items())

    def _send(self, relay, value):
        if not self.actuation_enabled: return
        if not self.baseline_ready and relay not in self.power_relays.values(): return
        if self.actual(relay) == value:
            self.sent.pop(relay, None); self.faults.pop(relay, None)
            return
        now = self.clock()
        previous = self.sent.get(relay)
        attempts = previous[2] if previous and previous[0] == value else 0
        if attempts >= 3:
            if relay not in self.faults:
                LOG.warning('Sin confirmación de %s tras 3 intentos; esperado=%s actual=%s', relay, value, self.actual(relay))
            self.faults[relay] = 'Sin confirmación tras 3 intentos'
            return
        if previous and previous[0] == value and now - previous[1] < 2 ** attempts:
            return
        payload = ('ON' if value else 'OFF') if '/in/' in relay else str(int(value))
        LOG.info('Orden %s=%s; actual=%s; intento=%d/3', relay, payload, self.actual(relay), attempts + 1)
        self.publish(relay, payload)
        if '/Set/' in relay: self.changed_boards.add(relay.split('/Set/')[0])
        self.sent[relay] = value, now, attempts + 1

    def selectors_for_stack(self, band):
        return {self.route(station, band) for station in self.stations} - {None}

    def tick(self):
        if not self.connected: return
        now = self.clock()
        if now - self.last_poll >= 5:
            for board in sorted(self.boards): self.publish(board + '/Set/GetStatus', '0')
            self.last_poll = now
        for station, state in self.stations.items():
            if state['auto'] and station in self.band_times and now - self.band_times[station] > 5:
                self.requests[station] = 0
        if not self.baseline_ready and all(self.actual(relay) is not None for relay in self.relays):
            self.baseline_ready = True
            LOG.info('Estado inicial confirmado: %d relés; habilitada la alineación', len(self.relays))
        self.changed_boards.clear()
        stack_plan = self.stack_plan()
        route_plan = {}
        for station, state in self.stations.items():
            if state['auto'] and station not in self.radio_bands:
                continue  # Wait for the radio before touching its existing antenna route.
            band = self.requests[station]
            ready = not band or self.matches(self.stack_targets(band))
            target = self.route(station, band) if band else None
            route_plan.update({relay: relay == target for relay in self.groups[station]})
            if not self.receive_safe(station): continue
            for relay in sorted(self.groups[station]):
                if relay != target: self._send(relay, False)
            other = 'stn2' if station == 'stn1' else 'stn1'
            conflicting_route = self.route(other, band) if band else None
            other_disconnected = conflicting_route is None or self.actual(conflicting_route) is False
            if target and ready and other_disconnected and all(self.actual(relay) is False for relay in self.groups[station] if relay != target):
                self._send(target, True)
        # Keep unchanged routing relays in place; an attached station must be confirmed in RX.
        bands = {band for band in self.requests.values() if band} | {band for band in self.prepared if not self.is_multiplex(band)}
        for band in sorted(bands):
            targets = self.stack_targets(band)
            if self.is_multiplex(band):
                targets = {relay: value for relay, value in stack_plan.items()
                           if any(relay in self.stack_relays[b] for b in self.stack_relays if self.is_multiplex(b))}
            selectors = {station: self.route(station, band) for station in self.stations}
            can_adjust = all(relay is None or self.actual(relay) is False or
                             (self.actual(relay) is True and self.receive_safe(station))
                             for station, relay in selectors.items())
            if not can_adjust: continue
            for relay, value in sorted(targets.items()):
                if not value: self._send(relay, False)
            if all(self.actual(relay) is False for relay, value in targets.items() if not value):
                for relay, value in sorted(targets.items()):
                    if value: self._send(relay, True)
        for relay, value in list(self.power_targets.items()): self._send(relay, value)
        for board in sorted(self.changed_boards):
            self.publish(board + '/Set/GetStatus', '0')
        snapshot = self.snapshot(route_plan, stack_plan)
        serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        self.output.tick(snapshot)
        self.last_snapshot, self.last_status_time = serialized, now

    def confirmed_band(self, station):
        group = self.groups[station]
        if any(self.actual(relay) is None for relay in group): return None
        active = [relay for relay in group if self.actual(relay)]
        if not active: return 0
        if len(active) != 1: return None
        bands = [int(band) for band, entry in self.sixpack[station[-1]].items()
                 if entry['rele'] == active[0]]
        if len(bands) == 1: return bands[0]
        requested = self.requests[station]
        return requested if requested in bands and self.matches(self.stack_targets(requested)) else None

    def snapshot(self, route_plan=None, stack_plan=None):
        route_plan, stack_plan = route_plan or {}, stack_plan or {}
        desired = dict(stack_plan, **route_plan)
        actual = {relay: self.actual(relay) for relay in sorted(self.relays)}
        missing = [relay for relay, value in actual.items() if value is None]
        pending = {relay: {'desired': value, 'actual': actual[relay]} for relay, value in desired.items()
                   if actual[relay] != value}
        result = {'stacks': deepcopy(self.stacks), 'sixpack': self.sixpack}
        for stack in result['stacks'].values():
            for i in range(1, 4):
                entry = stack[str(i)]
                entry['requested_estado'] = entry['estado']
                if real_topic(entry['rele']):
                    value = self.actual(entry['rele'])
                    entry['estado'] = value is True
                    entry['confirmed'] = value is not None
            if real_topic(stack['rele']):
                stack['requested_balun'] = stack['balun']
                stack['balun'] = self.actual(stack['rele']) is True
        for station, state in self.stations.items():
            confirmed = self.confirmed_band(station)
            result[station] = dict(state, band=self.requests[station],
                                   requested_band=self.requests[station], confirmed_band=confirmed,
                                   relay_status='unknown' if confirmed is None else 'waiting_radio' if state['auto'] and station not in self.radio_bands else 'pending' if pending or confirmed != self.requests[station] else 'aligned',
                                   conflict=self.conflicts.get(station))
        waiting = [s for s, state in self.stations.items() if state['auto'] and s not in self.radio_bands]
        confirmed_targets = all(self.confirmed_band(s) == self.requests[s] for s in self.stations)
        result['relay_sync'] = {'observe_only': not self.actuation_enabled, 'aligned': not pending and not missing and not waiting and confirmed_targets,
                                'waiting_for_radio': waiting,
                                'actual': actual, 'desired': desired, 'pending': pending,
                                'missing_feedback': missing, 'faults': dict(self.faults),
                                'tx_blocked': [s for s in self.stations if not self.receive_safe(s)]}
        return result

    def export_state(self):
        """Persist preferences and observations, without treating the latter as proof on restart."""
        diagnostics = json.loads(self.last_snapshot)['relay_sync'] if self.last_snapshot else {}
        return {
            'schema_version': 1,
            'desired': {
                'stations': {name: {'auto': state['auto'], 'band': self.requests[name]}
                             for name, state in self.stations.items()},
                'stacks': {band: {'outputs': {str(i): stack[str(i)]['estado'] for i in range(1, 4)}}
                           for band, stack in self.stacks.items()},
                'prepared_bands': sorted(self.prepared),
                'power_commands': dict(self.power_targets),
            },
            'observed': {
                'relays': {relay: self.actual(relay) for relay in sorted(self.relays)},
                'stations': {name: {'rig': state['rig'], 'confirmed_band': self.confirmed_band(name)}
                             for name, state in self.stations.items()},
                'radio_bands': dict(self.radio_bands), 'transmitting': dict(self.tx),
                'boards_online': dict(self.online), 'diagnostics': diagnostics,
            },
        }

    def restore_state(self, document):
        """Restore operating preferences only; always reconfirm hardware and radio inputs."""
        try:
            if document.get('schema_version') != 1:
                raise ValueError('Versión de estado incompatible')
            desired = document['desired']
            stations, stacks = desired['stations'], desired['stacks']
            if set(stations) != set(self.stations) or set(stacks) != set(self.stacks):
                raise ValueError('El estado no corresponde a las estaciones/bandas configuradas')
            requests = {}
            for name, saved in stations.items():
                if type(saved['auto']) is not bool or type(saved['band']) is not int:
                    raise ValueError('Modo o banda guardados inválidos')
                if str(saved['band']) not in self.sixpack[name[-1]]:
                    raise ValueError('Banda guardada no configurada')
                requests[name] = saved['band']
            for band, saved in stacks.items():
                if set(saved['outputs']) != {'1', '2', '3'} or any(type(value) is not bool for value in saved['outputs'].values()):
                    raise ValueError('Selección guardada inválida')
            prepared = desired.get('prepared_bands', [])
            if not isinstance(prepared, list) or any(type(band) is not int or str(band) not in self.stacks for band in prepared):
                raise ValueError('Bandas preparadas inválidas')
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise ValueError(f'No se puede restaurar el estado de control: {error}') from error
        # Apply only after the entire recoverable state has passed validation.
        for name, saved in stations.items():
            self.stations[name]['auto'] = saved['auto']
        self.requests = requests
        for band, saved in stacks.items():
            for index, value in saved['outputs'].items():
                self.stacks[band][index]['estado'] = value
            self.stacks[band]['balun'] = sum(saved['outputs'][str(i)] for i in range(1, int(self.stacks[band]['salidas']) + 1)) > 1
        self.prepared = set(prepared)
        self.initialized_stacks = {int(band) for band in stacks}
        # Relays, rig power, TX, faults, retries and queued power commands are historical
        # observations, not authorization to replay physical commands after a restart.
