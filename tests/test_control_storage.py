"""Migration, crash-safe storage, recovery and unchanged consumer contract."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'svc/control'))
from config_layout import compose, migrate, split_legacy
from state_store import StateStore
from controller import Controller

spec = importlib.util.spec_from_file_location('control_settings_storage', ROOT / 'svc/control/settings.py')
settings = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = settings
spec.loader.exec_module(settings)


def example():
    installation = json.loads((ROOT / 'cfg/control/installation.example.json').read_text())
    initial = json.loads((ROOT / 'cfg/control/initial-state.example.json').read_text())
    stations, stacks, sixpack = compose(installation, initial)
    return installation, initial, SimpleNamespace(stn1=stations['stn1'], stn2=stations['stn2'], stacks=stacks, sixpack=sixpack)


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.installation, self.initial, self.config = example()

    def legacy(self):
        documents = {'control.json': {'mqtt_host': 'mqtt', 'mqtt_port': 1883, 'mqtt_keepalive': 60},
                     'stn1.json': self.config.stn1, 'stn2.json': self.config.stn2,
                     'stacks.json': self.config.stacks, 'sixpack.json': self.config.sixpack}
        for name, value in documents.items():
            (self.folder / name).write_text(json.dumps(value))
        return documents

    def test_migration_keeps_originals_and_consumer_snapshot_identical(self):
        documents = self.legacy()
        old = settings.load_config(self.folder)
        migrate(self.folder)
        new = settings.load_config(self.folder)
        self.assertEqual(Controller(old, lambda *args: None).snapshot(), Controller(new, lambda *args: None).snapshot())
        for name, value in documents.items():
            self.assertEqual(json.loads((self.folder / name).read_text()), value)
        permanent = json.loads((self.folder / 'control/installation.json').read_text())
        self.assertNotIn('auto', permanent['stations']['stn1'])
        self.assertNotIn('estado', permanent['stacks']['20']['1'])
        self.assertNotIn('balun', permanent['stacks']['20'])
        with self.assertRaises(RuntimeError):
            migrate(self.folder)

    def test_partial_new_layout_never_silently_falls_back_to_legacy(self):
        self.legacy()
        (self.folder / 'control').mkdir()
        (self.folder / 'control/installation.json').write_text(json.dumps(self.installation))
        with self.assertRaises(RuntimeError):
            settings.load_config(self.folder)

    def test_atomic_save_only_writes_changes_and_survives_failed_replace(self):
        store = StateStore(self.folder / 'data/state.json')
        self.assertIsNone(store.load())
        old = {'schema_version': 1, 'value': 'original'}
        self.assertTrue(store.save(old))
        self.assertFalse(store.save(old))
        with patch('state_store.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                store.save({'schema_version': 1, 'value': 'new'})
        self.assertEqual(StateStore(store.path).load(), old)
        self.assertEqual(list(store.path.parent.glob('.state-*.tmp')), [])

    def test_corrupt_file_and_unknown_schema_are_not_overwritten(self):
        path = self.folder / 'state.json'
        for content in ('{"schema_version":', '{"schema_version":99}'):
            path.write_text(content)
            with self.assertRaises(RuntimeError):
                StateStore(path).load()
            self.assertEqual(path.read_text(), content)

    def test_restore_manual_band_stack_and_do_not_trust_saved_hardware(self):
        engine = Controller(self.config, lambda *args: None)
        engine.stations['stn2']['auto'] = False
        engine.requests['stn2'] = 20
        engine.stacks['20']['1']['estado'] = True
        engine.stacks['20']['2']['estado'] = False
        engine.stack_change(20, 2)
        saved = engine.export_state()
        saved['observed']['relays'] = {relay: True for relay in engine.relays}
        saved['observed']['transmitting'] = {'stn1': False, 'stn2': False}
        saved['desired']['power_commands'] = {'dtry/relay14475/in/r8': False}
        restored = Controller(self.config, lambda *args: None)
        restored.restore_state(saved)
        self.assertEqual(restored.requests['stn2'], 20)
        self.assertFalse(restored.stations['stn2']['auto'])
        self.assertTrue(restored.stacks['20']['2']['estado'])
        self.assertEqual(restored.observed, {})
        self.assertEqual(restored.tx, {})
        self.assertEqual(restored.power_targets, {})
        self.assertIsNone(restored.confirmed_band('stn2'))

    def test_recovery_matching_relays_sends_no_unnecessary_commands(self):
        engine = Controller(self.config, lambda *args: None, clock=lambda: 0)
        engine.stations['stn1']['auto'] = False
        engine.stations['stn2']['auto'] = False
        engine.requests['stn2'] = 20
        targets = engine.stack_plan()
        targets.update({relay: relay == engine.route(name, engine.requests[name]) for name in engine.stations for relay in engine.groups[name]})
        saved = engine.export_state()
        sent = []
        restored = Controller(self.config, lambda *args: sent.append(args), clock=lambda: 0)
        restored.restore_state(saved)
        restored.reconnect()
        restored.tick()
        self.assertFalse([topic for topic, value in sent if topic in restored.relays])
        for topic, relay in restored.feedback.items():
            restored.handle(topic, 'ON' if targets.get(relay, False) else 'OFF')
        restored.handle('stn1/tx', '0'); restored.handle('stn2/tx', '0')
        restored.tick()
        self.assertTrue(restored.snapshot()['relay_sync']['aligned'])
        self.assertFalse([topic for topic, value in sent if topic in restored.relays])

    def test_restored_selection_waits_for_rx_before_correcting_hardware(self):
        engine = Controller(self.config, lambda *args: None, clock=lambda: 0)
        engine.stations['stn1']['auto'] = False
        engine.stations['stn2']['auto'] = False
        engine.requests['stn2'] = 20
        saved = engine.export_state()
        sent = []
        restored = Controller(self.config, lambda *args: sent.append(args), clock=lambda: 0)
        restored.restore_state(saved)
        restored.reconnect()
        for topic, relay in restored.feedback.items():
            restored.handle(topic, 'ON' if relay == restored.route('stn2', 20) else 'OFF')
        restored.handle('stn1/tx', '0'); restored.handle('stn2/tx', '1')
        restored.tick()
        self.assertFalse([topic for topic, value in sent if topic in restored.relays])
        self.assertEqual(restored.requests['stn2'], 20)
        restored.handle('stn2/tx', '0')
        restored.tick()
        self.assertTrue([topic for topic, value in sent if topic in restored.relays])

    def test_bad_recovery_cannot_partially_change_the_live_configuration(self):
        engine = Controller(self.config, lambda *args: None)
        saved = engine.export_state()
        saved['desired']['stations']['stn1']['auto'] = False
        saved['desired']['stations']['stn2']['band'] = 999
        before = deepcopy(engine.stations)
        with self.assertRaises(ValueError):
            engine.restore_state(saved)
        self.assertEqual(engine.stations, before)


if __name__ == '__main__':
    unittest.main()
