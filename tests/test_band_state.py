import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('band_state_test', Path(__file__).resolve().parents[1] / 'svc/flex-mqtt/band_state.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class BandTest(unittest.TestCase):
    def setUp(self):
        self.now, self.messages = 0, []
        self.publisher = module.BandPublisher('stn2', lambda *args: self.messages.append(args),
            lambda f: 20 if f > 13 else 40, lambda: self.now)
    def bands(self): return [payload for topic, payload in self.messages if topic.endswith('/band')]
    def test_slice_recreation_does_not_publish_zero_or_old_band(self):
        self.publisher.update(14.2)
        for i in range(1000):
            self.now = i / 10000
            self.publisher.update(None)
        self.publisher.update(7.1)
        self.assertEqual(self.bands(), ['20', '40'])
    def test_sustained_missing_frequency_publishes_zero_once_then_heartbeat(self):
        self.publisher.update(14.2); self.publisher.update(None)
        self.now = 2; self.publisher.update(None)
        for _ in range(1000): self.publisher.update(None)
        self.assertEqual(self.bands(), ['20', '0'])
    def test_knob_tuning_updates_frequency_without_band_command_flood(self):
        for i in range(1000): self.publisher.update(14 + i / 10000)
        self.assertEqual(self.bands(), ['20'])
        self.now = 2; self.publisher.update(14.1)
        self.assertEqual(self.bands(), ['20', '20'])
