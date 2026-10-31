"""Exercise MQTT callbacks and actual TCP bytes without keying a real radio."""
import ast
import re
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'svc/flex-mqtt'))

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

    def prepare_split(self, second=False):
        self.bridge.status('S123|slice 4 in_use=1 active=1 tx=1 index_letter=A RF_frequency=14.100000 client_handle=0xA pan=0x40000000')
        if second:
            self.bridge.status('S123|slice 7 in_use=1 active=0 tx=0 index_letter=B RF_frequency=14.105000 client_handle=0xA pan=0x40000000')

    def prepare_letters(self):
        self.prepare_split(second=True)
        self.bridge.status('S123|slice 4 index_letter=A audio_mute=0')
        self.bridge.status('S123|slice 7 index_letter=B audio_mute=1')

    def test_slice_buttons_resolve_letters_and_never_key_radio(self):
        self.prepare_letters()
        for action, value, expected in [('mutea', b'1', 'slice s 4 audio_mute=1'),
                                        ('muteb', b'0', 'slice s 7 audio_mute=0'),
                                        ('rxa', b'1', 'slice remove 4'),
                                        ('rxb', b'1', 'slice remove 7'),
                                        ('txa', b'1', 'slice s 4 tx=1'),
                                        ('txb', b'1', 'slice s 7 tx=1'),
                                        ('a_eq_b', b'1', 'slice tune 7 14.100000')]:
            self.send(action, value)
            self.assertEqual(self.acknowledge(), expected)
            self.assertEqual(self.result()['status'], 'accepted')

    def test_slice_buttons_reject_missing_ambiguous_retained_and_transmitting(self):
        self.prepare_letters()
        self.send('txb', b'1', retain=True)
        self.assertEqual(self.result()['status'], 'retained_rejected')
        self.send('rxb', b'0')
        self.assertEqual(self.result()['status'], 'invalid_payload')
        self.bridge.status('S123|slice 9 active=0 client_handle=0xA index_letter=B')
        self.send('muteb', b'1')
        self.assertEqual(self.result()['status'], 'ambiguous_or_missing_slice_b')
        self.bridge.status('S123|slice 9 removed')
        self.bridge.status('S123|interlock state=TRANSMITTING')
        self.send('txa', b'1')
        self.assertEqual(self.result()['status'], 'radio_transmitting')
        self.assertEqual(self.bridge.sequence, 2000)

    def test_slice_telemetry_and_letter_owner_isolation(self):
        self.prepare_letters()
        self.bridge.status('S123|slice 9 active=0 tx=0 index_letter=B client_handle=0xB')
        self.assertEqual(self.bridge.split.button_states()['muteb'], '1')
        self.assertEqual(self.bridge.split.button_states()['a_eq_b'], '0')
        self.bridge.status('S123|slice 7 RF_frequency=14.100000')
        self.assertEqual(self.bridge.split.button_states()['a_eq_b'], '1')
        self.bridge.last_split_publish = 0
        self.bridge.last_button_publish = 0
        self.bridge.status('S123|slice 7 active=0')
        self.assertIn(unittest.mock.call('stn1/muteb', '1', retain=True), self.publish.call_args_list)

    def test_split_applies_audio_to_created_b_before_tx(self):
        self.prepare_letters()
        self.bridge.status('S123|slice 7 removed')
        self.send('split', b'{"enabled":1,"volume_a":0,"volume_b":75,"balance_a":0,"balance_b":100,"mute_b":false}')
        self.assertIn('clone_slice=4', self.acknowledge('8'))
        self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
        self.assertEqual(self.acknowledge(), 'slice s 4 audio_level=0 audio_pan=0')
        self.assertEqual(self.acknowledge(), 'slice s 8 audio_level=75 audio_pan=100')
        self.assertEqual(self.acknowledge(), 'slice s 8 audio_mute=0')
        self.assertEqual(self.acknowledge(), 'slice s 8 tx=1')

    def test_split_audio_existing_disable_invalid_and_error(self):
        self.prepare_letters()
        for value in (-1, 101, True, None, 1.5, '50'):
            self.send('split', json.dumps({'enabled':1,'volume_a':value}).encode())
            self.assertEqual(self.result()['status'], 'invalid_payload')
        self.send('split', b'{"enabled":0,"volume_a":20,"balance_b":100}')
        self.assert_disable_sequence()
        self.send('split', b'{"enabled":1,"volume_b":50,"balance_a":50}')
        self.assertEqual(self.acknowledge(), 'slice tune 7 14.101000')
        self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
        self.assertEqual(self.radio.recv(1024).decode().split('|',1)[1].strip(), 'slice s 4 audio_pan=50')
        self.bridge.response(f'R{self.bridge.sequence}|50000042|error')
        self.assertIsNone(self.bridge.split_job)
        self.assertEqual(self.result()['status'], 'error')

    def test_mute_ack_requests_real_snapshot_and_snapshot_updates_buttons(self):
        self.prepare_letters()
        self.assertFalse(self.bridge.take_audio_refresh())
        self.send('mutea', b'1')
        self.assertEqual(self.acknowledge(), 'slice s 4 audio_mute=1')
        self.assertTrue(self.bridge.take_audio_refresh())
        self.assertFalse(self.bridge.take_audio_refresh())
        self.publish.reset_mock()
        self.bridge.status('S123|slice 4 audio_mute=1')
        self.assertIn(unittest.mock.call('stn1/mutea', '1', retain=True), self.publish.call_args_list)
        self.publish.reset_mock()
        self.bridge.status('S123|slice 7 audio_mute=0')
        self.assertIn(unittest.mock.call('stn1/muteb', '0', retain=True), self.publish.call_args_list)

    def assert_disable_sequence(self, b=True):
        expected = ['slice s 4 audio_pan=50']
        if b: expected += ['slice s 7 audio_pan=50']
        expected += ['slice s 4 active=1', 'slice s 4 tx=1']
        if b: expected += ['slice remove 7']
        for command in expected:
            self.assertEqual(self.acknowledge(), command)

    def test_disable_split_from_active_b_selects_a_and_closes_b(self):
        self.prepare_letters()
        self.bridge.status('S123|slice 4 active=0 tx=0 audio_pan=0')
        self.bridge.status('S123|slice 7 active=1 tx=1 audio_pan=100')
        self.send('split', b'0')
        self.assert_disable_sequence()
        self.assertEqual(self.result()['status'], 'accepted')
        self.assertTrue(self.bridge.take_audio_refresh())

    def test_disable_split_handles_missing_b_and_protects_other_client(self):
        self.prepare_split()
        self.bridge.status('S123|slice 9 index_letter=B active=0 client_handle=0xB')
        self.send('split', b'0')
        self.assert_disable_sequence(b=False)
        self.assertIn(9, self.bridge.split.slices)

    def test_disable_split_does_not_close_b_after_a_command_fails(self):
        self.prepare_letters()
        self.send('split', b'0')
        self.assertEqual(self.acknowledge(), 'slice s 4 audio_pan=50')
        self.assertEqual(self.acknowledge(), 'slice s 7 audio_pan=50')
        self.assertEqual(self.radio.recv(1024).decode().split('|',1)[1].strip(), 'slice s 4 active=1')
        self.bridge.response(f'R{self.bridge.sequence}|50000042|error')
        self.assertIsNone(self.bridge.split_job)
        self.assertEqual(self.result()['status'], 'error')

    def test_missing_slice_distinct_from_unknown_and_other_clients(self):
        self.assertEqual(self.bridge.split.button_states()['muteb'], 'unknown')
        self.prepare_split()
        self.assertEqual(self.bridge.split.button_states()['muteb'], 'absent')
        self.bridge.status('S123|slice 9 index_letter=B active=0 client_handle=0xB')
        self.assertEqual(self.bridge.split.button_states()['muteb'], 'absent')
        self.bridge.status('R999|0|')
        self.assertEqual(self.bridge.split.button_states()['mutea'], 'absent')
        self.assertEqual(self.bridge.split.button_states()['muteb'], 'absent')

    def maestro_pan(self, second=False):
        self.bridge.status('S123|client 0xA connected client_id=gui program=SmartSDR-Maestro')
        self.bridge.status('S123|display pan 0x40000000 client_handle=0xA center=14.100000')
        if second:
            self.bridge.status('S123|display pan 0x40000001 client_handle=0xA center=7.100000')
        self.bridge.status('R999|0|' + ' '.join(str(i) for i in self.bridge.split.slices))

    def test_maestro_rx_a_creates_from_zero_b_requires_a(self):
        self.maestro_pan()
        self.send('rxb', b'1')
        self.assertEqual(self.result()['status'], 'create_a_first')
        self.send('rxa', b'1')
        self.assertEqual(self.acknowledge('4'), 'slice create pan=0x40000000 freq=14.100000')
        self.assertEqual(self.result()['status'], 'accepted')

    def test_maestro_rx_b_opens_without_stealing_focus_and_both_rx_are_green(self):
        self.prepare_split()
        self.maestro_pan()
        self.send('rxb', b'1')
        self.assertEqual(self.acknowledge('7'), 'slice create clone_slice=4 pan=0x40000000')
        self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
        self.bridge.status('S123|slice 7 in_use=1 index_letter=B active=0 tx=0 audio_mute=1 client_handle=0xA pan=0x40000000')
        state = self.bridge.split.button_states()
        self.assertEqual((state['rxa'], state['rxb'], state['txa'], state['txb']), ('1', '1', '1', '0'))
        self.send('rxb', b'1')
        self.assertEqual(self.acknowledge(), 'slice remove 7')

    def test_maestro_tx_b_creates_split_mode_offset_and_restores_focus(self):
        self.prepare_split()
        for mode, frequency in [('USB', '14.105000'), ('CW', '14.101000')]:
            self.bridge.status(f'S123|slice 4 mode={mode}')
            self.send('txb', b'1')
            self.assertEqual(self.acknowledge('7'), f'slice create clone_slice=4 pan=0x40000000 freq={frequency}')
            self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
            self.assertEqual(self.acknowledge(), 'slice s 7 tx=1')
            self.assertEqual(self.result()['status'], 'accepted')

    def test_maestro_two_pan_cycle_recreates_and_preserves_settings(self):
        self.prepare_letters()
        self.maestro_pan(second=True)
        self.bridge.status('S123|slice 7 mode=USB audio_level=30 audio_pan=100 audio_mute=1')
        self.send('rxb', b'1')
        self.assertEqual(self.acknowledge(), 'slice remove 7')
        self.assertEqual(self.acknowledge('7'), 'slice create pan=0x40000001 freq=14.105000 mode=USB')
        restored = self.acknowledge()
        for field in ('audio_level=30', 'audio_pan=100', 'audio_mute=1', 'tx=0', 'active=0'):
            self.assertIn(field, restored)
        self.bridge.status('S123|slice 7 pan=0x40000001')
        self.send('rxb', b'1')
        self.assertEqual(self.acknowledge(), 'slice remove 7')

    def test_maestro_create_error_does_not_assign_tx_or_queue_steps(self):
        self.prepare_split()
        self.send('txb', b'1')
        self.assertIn('slice create', self.radio.recv(1024).decode())
        self.bridge.response(f'R{self.bridge.sequence}|50000042|error')
        self.assertIsNone(self.bridge.split_job)
        self.assertEqual(self.result()['status'], 'error')

    def acknowledge(self, payload=''):
        command = self.radio.recv(1024).decode().split('|', 1)[1].strip()
        self.bridge.response(f'R{self.bridge.sequence}|0|{payload}')
        return command

    def test_split_creates_offset_slice_then_restores_receiver_and_assigns_tx(self):
        self.prepare_split()
        self.send('split', b'{"enabled":1,"offset_hz":5000}')
        self.assertEqual(self.acknowledge('7'), 'slice create clone_slice=4 pan=0x40000000 freq=14.105000')
        self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
        self.assertEqual(self.acknowledge(), 'slice s 7 tx=1')
        self.assertEqual(self.result()['status'], 'accepted')

    def test_split_mutes_created_b_before_assigning_tx(self):
        self.prepare_split()
        self.send('split', b'{"enabled":1,"offset_hz":1000,"mute_b":true}')
        self.assertEqual(self.acknowledge('7'), 'slice create clone_slice=4 pan=0x40000000 freq=14.101000')
        self.assertEqual(self.acknowledge(), 'slice s 4 active=1')
        self.assertEqual(self.acknowledge(), 'slice s 7 audio_mute=1')
        self.assertEqual(self.acknowledge(), 'slice s 7 tx=1')
        self.assertEqual(self.result()['status'], 'accepted')

    def test_split_unmutes_existing_b_when_no_is_selected(self):
        self.prepare_split(second=True)
        self.send('split', b'{"enabled":1,"offset_hz":1000,"mute_b":false}')
        self.acknowledge(); self.acknowledge()
        self.assertEqual(self.acknowledge(), 'slice s 7 audio_mute=0')
        self.assertEqual(self.acknowledge(), 'slice s 7 tx=1')

    def test_split_disable_centers_balances_restores_a_and_closes_b(self):
        self.prepare_split(second=True)
        self.send('split', b'{"enabled":0,"offset_hz":1000,"mute_b":true}')
        self.assert_disable_sequence()
        self.assertFalse(self.bridge.pending)

    def test_split_rejects_non_boolean_mute_preference(self):
        self.prepare_split()
        for value in ('yes', 1, None):
            self.send('split', json.dumps({'enabled':1,'mute_b':value}).encode())
            self.assertEqual(self.result()['status'], 'invalid_payload')
        self.assertFalse(self.bridge.pending)

    def test_split_mute_error_does_not_assign_b_tx(self):
        self.prepare_split(second=True)
        self.send('split', b'{"enabled":1,"mute_b":true}')
        self.acknowledge(); self.acknowledge()
        self.assertEqual(self.radio.recv(1024).decode().split('|',1)[1].strip(), 'slice s 7 audio_mute=1')
        self.bridge.response(f'R{self.bridge.sequence}|5000002D|Bad field')
        self.assertEqual(self.result()['status'], 'error')
        self.assertFalse(self.bridge.pending)

    def test_split_existing_slice_negative_offset_and_disable(self):
        self.prepare_split(second=True)
        self.send('split', b'{"enabled":1,"offset_hz":-2500}')
        self.assertEqual(self.acknowledge(), 'slice tune 7 14.097500')
        self.acknowledge(); self.acknowledge()
        self.bridge.status('S123|slice 4 tx=0')
        self.bridge.status('S123|slice 7 tx=1')
        self.send('split', b'0')
        self.assert_disable_sequence()

    def test_split_does_not_pick_other_client_or_assume_zero_one_indices(self):
        self.prepare_split()
        self.bridge.status('S123|slice 1 active=0 tx=1 client_handle=0xB')
        self.send('split', b'1')
        self.assertEqual(self.acknowledge('8'), 'slice create clone_slice=4 pan=0x40000000 freq=14.101000')
        self.acknowledge();self.acknowledge()

    def test_split_does_not_reuse_slice_from_different_waterfall(self):
        self.prepare_split(second=True)
        self.bridge.status('S123|slice 7 pan=0x40000001')
        self.send('split', b'1')
        self.assertEqual(self.acknowledge('8'), 'slice create clone_slice=4 pan=0x40000000 freq=14.101000')
        self.acknowledge();self.acknowledge()

    def test_split_requires_known_waterfall_before_creation(self):
        self.prepare_split()
        self.bridge.status('S123|slice 4 pan=unknown')
        self.send('split', b'1')
        self.assertEqual(self.result()['status'], 'missing_receive_panadapter')
        self.assertFalse(self.bridge.pending)

    def test_split_creation_error_never_assigns_tx(self):
        self.prepare_split()
        self.send('split', b'1')
        self.radio.recv(1024)
        self.bridge.response(f'R{self.bridge.sequence}|50000001|No resources')
        self.assertIsNone(self.bridge.split_job)
        self.assertEqual(self.result()['status'], 'error')
        self.assertFalse(self.bridge.pending)

    def test_split_rejects_invalid_offsets_busy_transmitting_and_missing_data(self):
        self.send('split', b'1')
        self.assertEqual(self.result()['status'], 'ambiguous_or_missing_receive_slice')
        for offset in (0, 100001, True, '1000'):
            self.send('split', json.dumps({'enabled': 1, 'offset_hz': offset}).encode())
            self.assertEqual(self.result()['status'], 'invalid_payload')
        self.prepare_split()
        self.bridge.status('S123|interlock state=TRANSMITTING')
        self.send('split', b'1')
        self.assertEqual(self.result()['status'], 'radio_transmitting')
        self.bridge.status('S123|interlock state=READY')
        self.send('split', b'1')
        self.send('split', b'1')
        self.assertEqual(self.result()['status'], 'busy')

    def test_switching_active_slice_uses_its_cached_frequency(self):
        self.prepare_split(second=True)
        self.assertEqual(str(self.bridge.split.frequency()), '14.100000')
        self.bridge.status('S123|slice 4 active=0')
        self.bridge.status('S123|slice 7 active=1')
        self.assertEqual(str(self.bridge.split.frequency()), '14.105000')

    def test_split_state_follows_external_tx_changes_and_slice_removal(self):
        self.prepare_split(second=True)
        self.assertEqual(self.bridge.split.value(), 0)
        self.bridge.status('S123|slice 4 tx=0')
        self.bridge.status('S123|slice 7 tx=1')
        self.assertEqual(self.bridge.split.value(), 1)
        self.bridge.status('S123|slice 7 removed')
        self.assertIsNone(self.bridge.split.value())
        self.bridge.status('S123|slice 4 tx=1')
        self.bridge.status('R999|0||')
        self.assertIsNone(self.bridge.split.receiver())

    def test_unrelated_response_does_not_ack_command(self):
        self.send('mox', b'1')
        self.bridge.response('R999|0|0 1')
        self.publish.assert_not_called()
        self.assertEqual(len(self.bridge.pending), 1)


class HeartbeatTest(unittest.TestCase):
    def test_idle_tcp_responses_refresh_confirmed_tx_not_previous_session(self):
        now = [0]
        class Stop(BaseException):
            pass
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def write(self, data): pass
            def read_until(self, *args, **kwargs):
                now[0] += 1
                if now[0] == 1: return b'R12|0|\n'
                if now[0] == 2: return b'S123|interlock state=READY\n'
                if now[0] == 4: raise Stop()
                return b'R12|0|\n'
        publish = Mock()
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'svc/flex-mqtt/app.py').read_text())
        names = {'telnet_listener', 'publish_transmit_state', 'update_transmit_state', 'parse_key_values', 'normalize_tx_state'}
        code = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
        from band_state import BandPublisher
        scope = dict(LOG=Mock(), BandPublisher=BandPublisher, obtain_band=lambda _: 20, re=re, time=SimpleNamespace(monotonic=lambda: now[0], sleep=lambda _: None),
                     FlexConnection=lambda *args: Connection(), command_bridge=Mock(split=SimpleNamespace(receiver=lambda: 0, frequency=lambda: None)), mqtt_client=SimpleNamespace(publish=publish),
                     TELNET_HOST='fake', TELNET_PORT=4992, TELNET_TIMEOUT=1, SUBSCRIBE_MESSAGES=[], TX_QUERY_MESSAGES=[],
                     TX_QUERY_INTERVAL_SECONDS=2, TX_HEARTBEAT_INTERVAL_SECONDS=1, STN='stn1',
                     LAST_TRANSMITTING=True, LAST_TX_PUBLISH_TIME=0)
        exec(compile(code, 'app-test', 'exec'), scope)
        with self.assertRaises(Stop): scope['telnet_listener']()
        tx = [call for call in publish.call_args_list if call.args[0] == 'stn1/tx']
        self.assertEqual(len(tx), 2)
        self.assertTrue(all(call.args[1] == '0' for call in tx))


if __name__ == '__main__':
    unittest.main()
