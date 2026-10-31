"""Derive split from live receiver and transmitter slice assignments."""

import re
from decimal import Decimal, InvalidOperation


class SplitState:
    def __init__(self):
        self.slices = {}
        self.transmitting = False

    def update(self, line):
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

    def plan(self, enabled, offset_hz):
        if self.transmitting:
            raise ValueError('radio_transmitting')
        receiver = self.receiver()
        if receiver is None:
            raise ValueError('ambiguous_or_missing_receive_slice')
        if not enabled:
            return [f'slice s {receiver} tx=1']
        if self.value() == 1:
            return [f'slice s {self.transmitter()} tx=1']
        fields = self.slices[receiver]
        try:
            frequency = Decimal(fields['RF_frequency']) + Decimal(offset_hz) / 1000000
            if not frequency.is_finite() or frequency <= 0:
                raise ValueError('invalid_receive_frequency')
        except (KeyError, InvalidOperation):
            raise ValueError('missing_receive_frequency') from None
        owner = fields.get('client_handle')
        candidates = [index for index, entry in self.slices.items()
                      if index != receiver and entry.get('client_handle') == owner]
        if len(candidates) > 1:
            raise ValueError('ambiguous_split_slice')
        target = str(candidates[0]) if candidates else '{created}'
        first = f'slice tune {target} {frequency:.6f}' if candidates else f'slice create clone_slice={receiver} freq={frequency:.6f}'
        return [first, f'slice s {receiver} active=1', f'slice s {target} tx=1']
