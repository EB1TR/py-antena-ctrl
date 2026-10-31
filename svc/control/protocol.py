"""Small retained catalog/state, change-only diagnostics and a live heartbeat."""
import hashlib
import json
import time
import uuid


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class ControlPublisher:
    def __init__(self, publish, clock=time.monotonic):
        self.publish, self.clock = publish, clock
        self.reset()

    def reset(self):
        self.session = uuid.uuid4().hex[:12]
        self.catalog_cache = self.state_cache = self.health_cache = None
        self.revision = 0
        self.last_heartbeat = -100
        self.force = False

    def tick(self, snapshot):
        catalog = {'v': 2, 'stations': {s: {'netbios': snapshot[s].get('netbios', s.upper())} for s in ('stn1', 'stn2')}, 'stacks': {}}
        outputs = {}
        for band, stack in snapshot['stacks'].items():
            count = int(stack['salidas'])
            catalog['stacks'][band] = {'salidas': count, **{str(i): {k: stack[str(i)].get(k) for k in ('nombre', 'tw', 'haz')} for i in range(1, count + 1)}}
            outputs[band] = [None if stack[str(i)].get('confirmed') is False else stack[str(i)]['estado'] for i in range(1, count + 1)]
        catalog['id'] = hashlib.sha256(encode(catalog).encode()).hexdigest()[:12]
        health = snapshot['relay_sync']
        state = {'v': 2, 'c': catalog['id'], 's': self.session,
                 'stations': {s: {k: snapshot[s][k] for k in ('auto', 'band', 'rig', 'confirmed_band', 'relay_status', 'conflict')} for s in ('stn1', 'stn2')},
                 'stacks': outputs,
                 'sync': {'aligned': health['aligned'], 'pending': len(health['pending']), 'missing': len(health['missing_feedback']),
                          'faults': len(health['faults']), 'waiting': health['waiting_for_radio'], 'tx_blocked': health['tx_blocked']}}
        catalog_text, state_text, health_text = encode(catalog), encode(state), encode(health)
        if catalog_text != self.catalog_cache or self.force:
            self.publish('control/config', catalog_text)
            self.catalog_cache = catalog_text
        changed = state_text != self.state_cache
        if changed:
            self.revision += 1
            self.state_cache = state_text
        if changed or self.force:
            self.publish('pytofront', encode(dict(state, r=self.revision)))
        if health_text != self.health_cache or self.force:
            self.publish('control/health', health_text)
            self.health_cache = health_text
        now = self.clock()
        if changed or self.force or now - self.last_heartbeat >= 2:
            self.publish('control/heartbeat', encode({'s': self.session, 'r': self.revision}))
            self.last_heartbeat = now
        self.force = False
