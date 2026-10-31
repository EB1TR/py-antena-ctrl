"""Wire-size, change-only publication and freshness contract regression tests."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'svc/control'))
from protocol import ControlPublisher
from test_control_storage import example
from controller import Controller


class ProtocolTest(unittest.TestCase):
    def setUp(self):
        self.now, self.messages = 0, []
        self.publisher = ControlPublisher(lambda t, p: self.messages.append((t, json.loads(p))), lambda: self.now)
        self.snapshot = Controller(example()[2], lambda *args: None).snapshot()

    def topic(self, topic):
        return [value for name, value in self.messages if name == topic]

    def test_idle_only_renews_small_heartbeat(self):
        self.publisher.tick(self.snapshot)
        self.assertEqual(len(self.topic('control/config')), 1)
        self.assertEqual(len(self.topic('pytofront')), 1)
        self.assertEqual(len(self.topic('control/health')), 1)
        for i in range(1, 151):
            self.now = i / 10
            self.publisher.tick(self.snapshot)
        self.assertEqual(len(self.topic('control/config')), 1)
        self.assertEqual(len(self.topic('pytofront')), 1)
        self.assertEqual(len(self.topic('control/health')), 1)
        self.assertEqual(len(self.topic('control/heartbeat')), 8)
        self.assertLess(len(json.dumps(self.topic('control/heartbeat')[0])), 50)
        self.assertLess(len(json.dumps(self.topic('pytofront')[0])), 1500)
        self.assertNotIn('sixpack', self.topic('pytofront')[0])
        self.assertNotIn('/Set/RS', json.dumps(self.topic('control/config')))

    def test_state_changes_are_immediate_and_catalog_stays_cached(self):
        self.publisher.tick(self.snapshot)
        self.snapshot['stn2']['auto'] = False
        self.publisher.tick(self.snapshot)
        self.assertEqual(len(self.topic('control/config')), 1)
        self.assertEqual(len(self.topic('pytofront')), 2)
        self.assertEqual([x['r'] for x in self.topic('pytofront')], [1, 2])
        self.assertEqual(self.topic('control/heartbeat')[-1]['r'], 2)
        self.assertEqual(len(self.topic('control/health')), 1)

    def test_unknown_antennas_are_not_encoded_as_false(self):
        self.snapshot['stacks']['20']['1']['confirmed'] = False
        self.publisher.tick(self.snapshot)
        self.assertIsNone(self.topic('pytofront')[0]['stacks']['20'][0])

    def test_config_identity_and_session_change_reject_old_cached_state(self):
        self.publisher.tick(self.snapshot)
        before = self.topic('pytofront')[-1]
        self.snapshot['stacks']['20']['1']['nombre'] = 'NEW'
        self.publisher.tick(self.snapshot)
        self.assertNotEqual(before['c'], self.topic('pytofront')[-1]['c'])
        self.publisher.reset(); self.publisher.tick(self.snapshot)
        self.assertNotEqual(before['s'], self.topic('pytofront')[-1]['s'])
        self.assertEqual(self.topic('pytofront')[-1]['r'], 1)

    def test_explicit_refresh_resends_but_does_not_increment_revision(self):
        self.publisher.tick(self.snapshot)
        self.publisher.force = True
        self.publisher.tick(self.snapshot)
        self.assertEqual(len(self.topic('pytofront')), 2)
        self.assertEqual(self.topic('pytofront')[0], self.topic('pytofront')[1])


if __name__ == '__main__':
    unittest.main()
