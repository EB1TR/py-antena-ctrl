"""Derive split from live receiver and transmitter slice assignments."""

import re
from decimal import Decimal, InvalidOperation


class SplitState:
    def __init__(self):
        self.slices = {}
        self.panadapters = {}
        self.clients = {}
        self.transmitting = False
        self.slice_list_known = False

    def update(self, line):
        client = re.match(r'^S[0-9a-fA-F]+\|client (0x[0-9a-fA-F]+) (.+)$', line)
        if client:
            if client[2].startswith('disconnected'):
                self.clients.pop(client[1], None)
            elif client[2].startswith('connected'):
                self.clients[client[1]] = dict(part.split('=', 1) for part in client[2].split() if '=' in part)
        pan = re.match(r'^S[0-9a-fA-F]+\|display pan (0x[0-9a-fA-F]+) (.+)$', line)
        if pan:
            if pan[2] == 'removed':
                self.panadapters.pop(pan[1], None)
            else:
                self.panadapters.setdefault(pan[1], {}).update(part.split('=', 1) for part in pan[2].split() if '=' in part)
        interlock = re.match(r'^S[0-9a-fA-F]+\|interlock\s+(.+)$', line)
        if interlock:
            fields = dict(part.split('=', 1) for part in interlock[1].split() if '=' in part)
            state = fields.get('state')
            if state in ('TRANSMITTING', 'PTT_REQUESTED', 'UNKEY_REQUESTED'):
                self.transmitting = True
            elif state in ('READY', 'RECEIVE', 'NOT_READY', 'TX_FAULT', 'TIMEOUT', 'STUCK_INPUT'):
                self.transmitting = False
        match = re.match(r'^S[0-9a-fA-F]+\|slice (\d+)\s+(.+)$', line)
        if match:
            index, text = int(match[1]), match[2]
            fields = dict(part.split('=', 1) for part in text.split() if '=' in part)
            if text == 'removed' or fields.get('in_use') == '0':
                self.slices.pop(index, None)
            else:
                self.slices.setdefault(index, {}).update(fields)
        listing = re.match(r'^R999\|0\|([^|]*)', line)
        if listing:
            self.slice_list_known = True
            ids = {int(value) for value in listing[1].split() if value.isdecimal()}
            self.slices = {index: fields for index, fields in self.slices.items() if index in ids}

    def receiver(self):
        active = [index for index, fields in self.slices.items() if fields.get('active') == '1']
        return active[0] if len(active) == 1 else None

    def transmitter(self):
        receiver = self.receiver()
        if receiver is None:
            return None
        owner = self.slices[receiver].get('client_handle')
        targets = [index for index, fields in self.slices.items()
                   if fields.get('client_handle') == owner and fields.get('tx') == '1']
        return targets[0] if len(targets) == 1 else None

    def value(self):
        receiver, transmitter = self.receiver(), self.transmitter()
        return None if receiver is None or transmitter is None else int(receiver != transmitter)

    def frequency(self):
        try:
            frequency = Decimal(self.slices[self.receiver()]['RF_frequency'])
            return frequency if frequency.is_finite() and frequency > 0 else None
        except (KeyError, InvalidOperation):
            return None

    def plan(self, enabled, offset_hz, mute_b=None, audio=None):
        if self.transmitting:
            raise ValueError('radio_transmitting')
        receiver = self.receiver()
        if receiver is None:
            raise ValueError('ambiguous_or_missing_receive_slice')
        if not enabled:
            a = self.letter_slice('A')
            owner = self.slices[a]['client_handle']
            candidates = [index for index, fields in self.slices.items()
                          if fields.get('client_handle') == owner and fields.get('index_letter') == 'B']
            if len(candidates) > 1:
                raise ValueError('ambiguous_or_missing_slice_b')
            steps = [f'slice s {a} audio_pan=50']
            if candidates:
                steps.append(f'slice s {candidates[0]} audio_pan=50')
            steps += [f'slice s {a} active=1', f'slice s {a} tx=1']
            if candidates:
                steps.append(f'slice remove {candidates[0]}')
            return steps
        if audio:
            receiver = self.letter_slice('A')
        fields = self.slices[receiver]
        try:
            frequency = Decimal(fields['RF_frequency']) + Decimal(offset_hz) / 1000000
            if not frequency.is_finite() or frequency <= 0:
                raise ValueError('invalid_receive_frequency')
        except (KeyError, InvalidOperation):
            raise ValueError('missing_receive_frequency') from None
        owner = fields.get('client_handle')
        pan = fields.get('pan', '')
        if not re.fullmatch(r'0x[0-9a-fA-F]+', pan):
            raise ValueError('missing_receive_panadapter')
        if self.value() == 1 and self.transmitter() != receiver and self.slices[self.transmitter()].get('pan') == pan:
            target = self.transmitter()
            if audio and self.slices[target].get('index_letter') != 'B':
                raise ValueError('ambiguous_or_missing_slice_b')
            mute = [] if mute_b is None else [f'slice s {target} audio_mute={int(mute_b)}']
            return self.audio_steps(receiver, target, audio) + mute + [f'slice s {target} tx=1']
        candidates = [index for index, entry in self.slices.items()
                      if index != receiver and entry.get('client_handle') == owner and entry.get('pan') == pan]
        if audio and candidates and (len(candidates) != 1 or self.slices[candidates[0]].get('index_letter') != 'B'):
            raise ValueError('ambiguous_or_missing_slice_b')
        if len(candidates) > 1:
            raise ValueError('ambiguous_split_slice')
        target = str(candidates[0]) if candidates else '{created}'
        first = f'slice tune {target} {frequency:.6f}' if candidates else f'slice create clone_slice={receiver} pan={pan} freq={frequency:.6f}'
        mute = [] if mute_b is None else [f'slice s {target} audio_mute={int(mute_b)}']
        return [first, f'slice s {receiver} active=1'] + self.audio_steps(receiver, target, audio) + mute + [f'slice s {target} tx=1']

    def owner(self):
        receiver = self.receiver()
        if receiver is not None and self.slices[receiver].get('client_handle'):
            return self.slices[receiver]['client_handle']
        owners = {entry.get('client_handle') for entry in self.slices.values()} - {None, '0x00000000'}
        if len(owners) == 1:
            return owners.pop()
        if not owners and len(self.clients) == 1:
            return next(iter(self.clients))
        raise ValueError('ambiguous_or_missing_receive_slice')

    def optional_letter(self, letter):
        owner = self.owner()
        matches = [index for index, fields in self.slices.items()
                   if fields.get('client_handle') == owner and fields.get('index_letter') == letter]
        if len(matches) > 1:
            raise ValueError('ambiguous_or_missing_slice_' + letter.lower())
        return matches[0] if matches else None

    def letter_slice(self, letter):
        target = self.optional_letter(letter)
        if target is None:
            raise ValueError('ambiguous_or_missing_slice_' + letter.lower())
        return target

    def maestro_plan(self, action):
        if self.transmitting:
            raise ValueError('radio_transmitting')
        letter = action[-1].upper()
        target = self.optional_letter(letter)
        owner = self.owner()
        pans = [index for index, fields in self.panadapters.items() if fields.get('client_handle') == owner]
        if len(pans) > 2:
            raise ValueError('unsupported_panadapter_layout')
        if action.startswith('tx'):
            if target is not None:
                return [f'slice s {target} tx=1']
            if letter != 'B':
                raise ValueError('ambiguous_or_missing_slice_a')
            a = self.letter_slice('A')
            fields = self.slices[a]
            offset = 1000 if fields.get('mode', '').upper() in ('CW', 'RTTY', 'DIGL', 'DIGU') else 5000
            frequency = self.valid_frequency(fields.get('RF_frequency')) + Decimal(offset) / 1000000
            pan = fields.get('pan', '')
            self.valid_pan(pan)
            return [f'slice create clone_slice={a} pan={pan} freq={frequency:.6f}',
                    f'slice s {a} active=1', 'slice s {created} tx=1']
        if target is not None:
            fields = self.slices[target]
            # Maestro cycles first pan -> second pan -> closed.
            if len(pans) == 2 and fields.get('pan') == pans[0]:
                frequency = self.valid_frequency(fields.get('RF_frequency'))
                mode = fields.get('mode', '')
                if not re.fullmatch(r'[A-Za-z0-9]+', mode):
                    raise ValueError('missing_slice_mode')
                steps = [f'slice remove {target}', f'slice create pan={pans[1]} freq={frequency:.6f} mode={mode}']
                # Restore settings after recreation, including the original TX/focus assignment.
                values = []
                for key in ('audio_level', 'audio_pan', 'audio_mute', 'filter_lo', 'filter_hi', 'agc_threshold', 'agc_off_level', 'step', 'rit_on', 'rit_freq', 'xit_on', 'xit_freq', 'tx', 'active'):
                    if re.fullmatch(r'-?\d+', fields.get(key, '')):
                        values.append(f'{key}={fields[key]}')
                for key in ('rxant', 'txant', 'agc_mode'):
                    if re.fullmatch(r'[A-Za-z0-9_]+', fields.get(key, '')):
                        values.append(f'{key}={fields[key]}')
                if values:
                    steps.append('slice s {created} ' + ' '.join(values))
                return steps
            return [f'slice remove {target}']
        if not self.slice_list_known:
            raise ValueError('waiting_slice_snapshot')
        a = self.optional_letter('A')
        if letter == 'B' and a is None:
            raise ValueError('create_a_first')
        if not pans:
            raise ValueError('missing_receive_panadapter')
        pan = pans[0]
        self.valid_pan(pan)
        if a is not None:
            return [f'slice create clone_slice={a} pan={pan}', f'slice s {a} active=1']
        frequency = self.valid_frequency(self.panadapters[pan].get('center'))
        return [f'slice create pan={pan} freq={frequency:.6f}']

    @staticmethod
    def valid_pan(pan):
        if not re.fullmatch(r'0x[0-9a-fA-F]+', pan):
            raise ValueError('missing_receive_panadapter')

    @staticmethod
    def valid_frequency(value):
        try:
            result = Decimal(value)
            if result.is_finite() and result > 0:
                return result
        except (InvalidOperation, TypeError):
            pass
        raise ValueError('missing_receive_frequency')

    def slice_command(self, action, value):
        if self.transmitting:
            raise ValueError('radio_transmitting')
        if action == 'a_eq_b':
            source, target = self.letter_slice('A'), self.letter_slice('B')
            try:
                frequency = Decimal(self.slices[source]['RF_frequency'])
                if not frequency.is_finite() or frequency <= 0:
                    raise ValueError('invalid_source_frequency')
            except (KeyError, InvalidOperation):
                raise ValueError('missing_source_frequency') from None
            return f'slice tune {target} {frequency:.6f}'
        target = self.letter_slice(action[-1].upper())
        field = 'audio_mute' if action.startswith('mute') else 'active' if action.startswith('rx') else 'tx'
        return f'slice s {target} {field}={value}'

    def button_states(self):
        result = {}
        for letter in ('a', 'b'):
            try:
                fields = self.slices[self.letter_slice(letter.upper())]
            except ValueError:
                receiver = self.receiver()
                if not self.slices and self.slice_list_known:
                    missing = True
                elif receiver is not None and self.slices[receiver].get('client_handle'):
                    owner = self.slices[receiver]['client_handle']
                    missing = not any(entry.get('client_handle') == owner and entry.get('index_letter') == letter.upper()
                                      for entry in self.slices.values())
                else:
                    missing = False
                fields = dict.fromkeys(('audio_mute', 'active', 'tx'), 'absent' if missing else 'unknown')
            for prefix, field in (('mute', 'audio_mute'), ('rx', 'active'), ('tx', 'tx')):
                result[prefix + letter] = ('1' if fields.get('index_letter') == letter.upper() else fields.get(field, 'unknown')) if prefix == 'rx' else fields.get(field, 'unknown')
        try:
            a, b = self.letter_slice('A'), self.letter_slice('B')
            result['a_eq_b'] = str(int(Decimal(self.slices[a]['RF_frequency']) == Decimal(self.slices[b]['RF_frequency'])))
        except (ValueError, KeyError, InvalidOperation):
            result['a_eq_b'] = 'unknown'
        return result

    @staticmethod
    def audio_steps(receiver, target, audio):
        steps = []
        for suffix, index in (('a', receiver), ('b', target)):
            fields = []
            for name, field in (('volume', 'audio_level'), ('balance', 'audio_pan')):
                value = (audio or {}).get(f'{name}_{suffix}')
                if value is not None:
                    fields.append(f'{field}={value}')
            if fields:
                steps.append(f'slice s {index} ' + ' '.join(fields))
        return steps
