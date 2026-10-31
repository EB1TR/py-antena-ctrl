"""Exercise MQTT callbacks and actual TCP bytes without keying a real radio."""
import importlib.util
import json
from pathlib import Path
import socket
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('flex_commands', Path(__file__).resolve().parents[1] / 'svc/flex-mqtt/commands.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CommandsTest(unittest.TestCase):
    def setUp(self):
        self.publish = Mock()
        self.bridge = module.CommandBridge('stn1', self.publish)
        self.writer, self.radio = socket.socketpair()
        self.radio.settimeout(1)
        self.addCleanup(self.writer.close)
        self.addCleanup(self.radio.close)
        self.bridge.attach(SimpleNamespace(write=self.writer.sendall))

    def send(self, action, value, station='stn1', retain=False):
        self.bridge.on_message(None, None, SimpleNamespace(
            topic=f'set/{station}/{action}', payload=value, retain=retain))

    def result(self):
        return json.loads(self.publish.call_args.args[1])

    def test_mox_and_tune_on_off_and_acknowledgments(self):
        for action, value, command in [('mox', b'1', 'xmit 1'), ('mox', b'0', 'xmit 0'),
                                       ('tune', b'1', 'transmit tune on'), ('tune', b'0', 'transmit tune off')]:
            self.send(action, value)
            line = self.radio.recv(1024).decode()
            self.assertEqual(line, f'C{self.bridge.sequence}|{command}\n')
            self.bridge.response(f'R{self.bridge.sequence}|0|')
            self.assertEqual(self.result()['status'], 'accepted')
            self.assertFalse(self.publish.call_args.kwargs['retain'])

    def test_invalid_and_retained_commands_do_not_reach_tcp(self):
        for value in (b'', b'on', b'1\nxmit 1', b'\xff'):
            self.send('mox', value)
            self.assertEqual(self.result()['status'], 'invalid_payload')
        self.send('tune', b'1', retain=True)
        self.assertEqual(self.result()['status'], 'retained_rejected')
        self.assertEqual(self.bridge.sequence, 2000)

    def test_station_isolation(self):
        self.send('mox', b'1', station='stn2')
        self.assertEqual(self.bridge.sequence, 2000)
        self.publish.assert_not_called()

    def test_radio_error_timeout_and_disconnect(self):
        self.send('tune', b'1')
        self.bridge.response(f'R{self.bridge.sequence}|50000042|Not ready')
        self.assertEqual(self.result()['status'], 'error')
        self.send('mox', b'1')
        with patch.object(module.time, 'monotonic', return_value=time.monotonic()+6):
            self.bridge.expire()
        self.assertEqual(self.result()['status'], 'timeout')
        self.send('tune', b'0')
        self.bridge.detach()
        self.assertEqual(self.result()['status'], 'disconnected')
        self.send('mox', b'1')
        self.assertEqual(self.result()['status'], 'unavailable')
        self.bridge.attach(SimpleNamespace(write=self.writer.sendall))
        self.assertFalse(self.bridge.pending)

    def test_atu_start_bypass_and_short_response(self):
        for value in (b'start', b'bypass'):
            self.send('atu', value)
            self.assertEqual(self.radio.recv(1024).decode(), f'C{self.bridge.sequence}|atu {value.decode()}\n')
            self.bridge.response(f'R{self.bridge.sequence}|0')
            self.assertEqual(self.result()['status'], 'accepted')
        self.send('atu', b'enable')
        self.assertEqual(self.result()['status'], 'invalid_payload')

    def test_actual_atu_and_tune_status_are_published(self):
        self.bridge.status('S123|atu status=TUNE_IN_PROGRESS atu_enabled=0')
        self.assertEqual(self.publish.call_args.args[0], 'stn1/atu/state')
        self.bridge.status('S123|atu status=TUNE_SUCCESS atu_enabled=1')
        self.assertEqual(json.loads(self.publish.call_args.args[1])['atu_enabled'], '1')
        self.bridge.status('S123|transmit tunepower=10 tune=0')
        self.assertEqual(self.publish.call_args.args, ('stn1/tune', '0'))

    def test_unrelated_response_does_not_ack_command(self):
        self.send('mox', b'1')
        self.bridge.response('R999|0|0 1')
        self.publish.assert_not_called()
        self.assertEqual(len(self.bridge.pending), 1)


if __name__ == '__main__':
    unittest.main()
