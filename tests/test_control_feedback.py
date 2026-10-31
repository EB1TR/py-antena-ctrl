"""Relay confirmation and break-before-make regression tests."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('control_feedback', ROOT / 'svc/control/controller.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FeedbackTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.messages = []
        cfg = SimpleNamespace(
            sixpack=json.loads((ROOT / 'cfg/sixpack.json').read_text()),
            stacks=json.loads((ROOT / 'cfg/stacks.json').read_text()),
            stn1={'auto': True, 'band': 0, 'rig': 0, 'rele': 'dtry/relay14475/in/r7'},
            stn2={'auto': True, 'band': 0, 'rig': 0, 'rele': 'dtry/relay14475/in/r8'})
        self.engine = module.Controller(cfg, lambda topic, payload: self.messages.append((topic, payload)), lambda: self.now)
        self.engine.reconnect()
        self.engine.handle('stn1/tx', '0'); self.engine.handle('stn2/tx', '0')

    def observe_all_off(self):
        for topic in self.engine.feedback: self.engine.handle(topic, 'OFF')

    def actions(self):
        return [(topic, payload) for topic, payload in self.messages if topic in self.engine.relays]

    def acknowledge(self):
        actions = self.actions()
        self.messages.clear()
        for topic, payload in actions: self.engine.handle(module.feedback_topic(topic), payload)
        return actions

    def band(self, station, band):
        self.engine.handle(f'{station}/band', str(band))

    def converge(self):
        for _ in range(5):
            self.engine.tick(); self.acknowledge()

    def test_startup_does_not_power_off_radios_or_assume_feedback(self):
        self.engine.tick()
        self.assertFalse(self.actions())
        self.assertIsNone(self.engine.confirmed_band('stn2'))
        self.assertNotEqual(self.engine.snapshot()['relay_sync']['missing_feedback'], [])

    def test_publishing_is_not_confirmation(self):
        self.observe_all_off(); self.band('stn2', 20)
        self.engine.tick()
        self.assertTrue(self.actions())
        self.assertEqual(self.engine.confirmed_band('stn2'), 0)
        self.assertFalse(self.engine.snapshot()['stacks']['20']['1']['estado'])
        self.converge()
        self.assertEqual(self.engine.confirmed_band('stn2'), 20)

    def test_band_change_waits_for_off_feedback_before_new_route(self):
        self.observe_all_off(); self.band('stn2', 20); self.converge()
        old, new = self.engine.route('stn2', 20), self.engine.route('stn2', 40)
        self.messages.clear(); self.band('stn2', 40); self.engine.tick()
        self.assertIn((old, '0'), self.actions())
        self.assertNotIn((new, '1'), self.actions())
        self.engine.tick(); self.assertNotIn((new, '1'), self.actions())
        self.acknowledge(); self.converge()
        self.assertEqual(self.engine.confirmed_band('stn2'), 40)

    def test_repeated_band_and_zero_do_not_emit_relay_storms(self):
        self.observe_all_off(); self.band('stn2', 0)
        for _ in range(500): self.band('stn2', 0); self.engine.tick()
        self.assertFalse(self.actions())
        self.band('stn2', 10); self.converge(); self.messages.clear()
        for _ in range(500): self.band('stn2', 10); self.engine.tick()
        self.assertFalse(self.actions())

    def test_missing_feedback_blocks_activation_and_bounds_retries(self):
        self.observe_all_off(); self.engine.tick()
        self.engine.handle('SmartDEN_MQTT16R/E8EADA0059F8/Get/Status', 'Disconnected')
        self.band('stn2', 20)
        for moment in (0, 1, 2, 4, 6, 8):
            self.now = moment; self.engine.handle('stn2/tx', '0'); self.band('stn2', 20); self.engine.tick()
        self.assertTrue(self.engine.faults)
        self.assertTrue(all(payload == '0' for _, payload in self.actions()))
        for topic in {topic for topic, _ in self.actions()}:
            self.assertLessEqual(sum(t == topic for t, _ in self.actions()), 3)

    def test_external_relay_drift_is_corrected_from_observed_state(self):
        self.observe_all_off(); self.band('stn2', 10); self.converge()
        wrong = self.engine.route('stn2', 40)
        self.engine.handle(module.feedback_topic(wrong), 'ON'); self.messages.clear()
        self.engine.tick(); self.assertIn((wrong, '0'), self.actions())
        self.acknowledge(); self.assertEqual(self.engine.confirmed_band('stn2'), 10)

    def test_manual_mode_and_return_to_auto_use_latest_radio_band(self):
        self.observe_all_off(); self.band('stn2', 20); self.converge()
        self.engine.handle('set/stn2/antm', '0'); self.band('stn2', 40)
        self.assertEqual(self.engine.requests['stn2'], 20)
        self.engine.handle('set/stn2/band', '10'); self.assertEqual(self.engine.requests['stn2'], 10)
        self.engine.handle('set/stn2/antm', '0'); self.assertEqual(self.engine.requests['stn2'], 40)

    def test_band_conflict_and_shared_multiplexer_are_preserved(self):
        self.band('stn1', 20); self.band('stn2', 20)
        self.assertEqual(self.engine.requests['stn2'], 0)
        self.band('stn1', 17); self.band('stn2', 12)
        self.assertEqual(self.engine.requests['stn2'], 0)
        self.assertTrue(self.engine.conflicts['stn2'])

    def test_new_route_waits_for_conflicting_other_station_physical_disconnect(self):
        self.observe_all_off(); self.band('stn1', 10); self.converge()
        self.engine.handle('stn1/tx', '1')
        self.engine.requests['stn1'] = 0
        self.band('stn2', 10); self.messages.clear(); self.engine.tick()
        self.assertNotIn((self.engine.route('stn2', 10), '1'), self.actions())
        self.engine.handle('stn1/tx', '0'); self.converge()
        self.assertEqual(self.engine.confirmed_band('stn2'), 10)

    def test_startup_preserves_existing_owner_until_both_radios_report_bands(self):
        self.observe_all_off()
        occupied = self.engine.route('stn2', 10)
        self.engine.handle(module.feedback_topic(occupied), 'ON')
        self.band('stn1', 10)
        self.assertEqual(self.engine.requests['stn1'], 0)
        self.band('stn2', 10)
        self.assertEqual(self.engine.requests['stn2'], 10)

    def test_transmitting_blocks_route_changes(self):
        self.observe_all_off(); self.band('stn2', 20); self.converge()
        self.engine.handle('stn2/tx', '1'); self.band('stn2', 40); self.messages.clear(); self.engine.tick()
        self.assertFalse(any(topic in self.engine.groups['stn2'] for topic, _ in self.actions()))
        self.engine.handle('stn2/tx', '0'); self.engine.tick()
        self.assertIn((self.engine.route('stn2', 20), '0'), self.actions())

    def test_cached_denkovi_feedback_is_not_accepted_as_live_proof(self):
        topic = next(topic for topic in self.engine.feedback if '/Get/' in topic)
        self.engine.handle(topic, 'On', retained=True)
        self.assertIsNone(self.engine.actual(self.engine.feedback[topic]))
        self.engine.handle(topic, 'On')
        self.assertTrue(self.engine.actual(self.engine.feedback[topic]))
        self.engine.handle(topic.rsplit('/Get/', 1)[0] + '/Get/Status', 'Disconnected', retained=True)
        self.assertTrue(self.engine.actual(self.engine.feedback[topic]))

    def test_dingtian_feedback_and_power_follow_real_state(self):
        self.engine.handle('dtry/relay14475/out/r8', 'ON', retained=True)
        self.assertEqual(self.engine.stations['stn2']['rig'], 1)
        self.engine.tick(); self.assertFalse(self.actions())
        self.engine.handle('set/stn2/rig', '0'); self.engine.tick()
        self.assertIn(('dtry/relay14475/in/r8', 'OFF'), self.actions())
        self.engine.handle('dtry/relay14475/out/r8', 'OFF')
        self.assertFalse(self.engine.power_targets)

    def test_board_offline_and_broker_reconnect_invalidate_actual_values(self):
        self.observe_all_off()
        self.engine.handle('SmartDEN_MQTT16R/E8EADA0059F8/Get/Status', 'Disconnected')
        self.assertIsNone(self.engine.actual(self.engine.route('stn2', 20)))
        self.engine.reconnect(); self.assertFalse(self.engine.observed)

    def test_broker_reconnect_waits_for_fresh_radio_inputs_without_clearing_live_route(self):
        self.observe_all_off(); self.band('stn2', 10); self.converge()
        actual = dict(self.engine.observed)
        self.engine.disconnect(); self.engine.reconnect(); self.messages.clear()
        for relay, value in actual.items():
            self.engine.handle(module.feedback_topic(relay), 'ON' if value else 'OFF')
        self.engine.handle('stn2/tx', '0'); self.engine.tick()
        self.assertFalse(self.actions())
        self.assertNotIn('stn2', self.engine.radio_bands)
        self.band('stn2', 10); self.engine.tick()
        self.assertFalse(self.actions())

    def test_stack_change_keeps_band_route_and_unchanged_antennas_in_place(self):
        self.observe_all_off(); self.band('stn2', 20); self.converge()
        selected = self.engine.stacks['20']['1']['rele']
        removed = self.engine.stacks['20']['2']['rele']
        balun = self.engine.stacks['20']['rele']
        self.messages.clear()
        self.engine.stack_change(20, 0)
        self.engine.tick()
        self.assertEqual(set(self.actions()), {(removed, '0'), (balun, '0')})
        self.assertFalse(any(topic in self.engine.groups['stn2'] for topic, _ in self.actions()))
        self.assertFalse(any(topic == selected for topic, _ in self.actions()))
        self.assertEqual(self.engine.confirmed_band('stn2'), 20)
        self.assertEqual(self.engine.snapshot()['stn2']['band'], 20)
        self.acknowledge(); self.converge()
        self.assertEqual(self.engine.confirmed_band('stn2'), 20)

    def test_stack_swap_only_opens_old_branch_then_closes_new_branch(self):
        self.observe_all_off(); self.band('stn2', 20)
        self.engine.stack_change(20, 0); self.converge(); self.messages.clear()
        first = self.engine.stacks['20']['1']['rele']
        second = self.engine.stacks['20']['2']['rele']
        self.engine.stack_change(20, 0); self.engine.tick()
        self.assertEqual(self.actions(), [(first, '0')])
        self.acknowledge(); self.engine.tick()
        self.assertEqual(self.actions(), [(second, '1')])
        self.acknowledge(); self.engine.tick(); self.assertFalse(self.actions())

    def test_stack_change_during_tx_does_not_actuate_connected_relays(self):
        self.observe_all_off(); self.band('stn2', 20); self.converge()
        self.messages.clear(); self.engine.handle('stn2/tx', '1')
        self.engine.stack_change(20, 0); self.engine.tick()
        self.assertFalse(self.actions())
        self.engine.handle('stn2/tx', '0'); self.engine.tick()
        self.assertEqual(len(self.actions()), 2)

    def test_scalar_band_and_legacy_upgrade_message_do_not_store_segment(self):
        self.engine.handle('stn2/band', '40')
        self.assertEqual(self.engine.requests['stn2'], 40)
        self.engine.handle('stn2/band', '[10, 5]')
        self.assertEqual(self.engine.requests['stn2'], 10)
        self.assertNotIn('segmento', self.engine.snapshot()['stn2'])
        for value in ('true', '"20"', '{}', 'null'):
            with self.assertRaises(ValueError): self.engine.handle('stn2/band', value)

    def test_stack_swap_and_last_antenna_rules(self):
        self.observe_all_off(); self.band('stn2', 20)
        self.engine.stack_change(20, 0)
        active = lambda: [i for i in (1, 2) if self.engine.stacks['20'][str(i)]['estado']]
        self.assertEqual(active(), [1])
        self.engine.stack_change(20, 1); self.assertEqual(active(), [1])
        self.engine.stack_change(20, 0); self.assertEqual(active(), [2])
        self.engine.stack_change(20, 1); self.assertEqual(active(), [1, 2])

    def test_startup_waits_for_complete_feedback_before_touching_antenna_routes(self):
        self.band('stn2', 20); self.engine.tick()
        self.assertFalse(self.actions())
        for relay in self.engine.groups['stn2']:
            self.engine.handle(module.feedback_topic(relay), 'OFF')
        self.engine.tick()
        self.assertFalse(self.actions())
        self.assertFalse(self.engine.baseline_ready)

    def test_startup_adopts_actual_stack_selection_without_restoring_old_json(self):
        selected = self.engine.stacks['20']['1']['rele']
        route = self.engine.route('stn2', 20)
        for feedback, command in self.engine.feedback.items():
            self.engine.handle(feedback, 'ON' if command in (selected, route) else 'OFF')
        self.assertFalse(self.engine.stacks['20']['2']['estado'])
        self.band('stn2', 20); self.engine.tick()
        self.assertFalse(self.actions())
        self.assertEqual(self.engine.confirmed_band('stn2'), 20)

    def test_observation_mode_does_not_actuate_or_report_simulated_retries(self):
        self.engine.actuation_enabled = False
        self.band('stn2', 20)
        for moment in (0, 2, 6, 10):
            self.now = moment; self.engine.handle('stn2/tx', '0'); self.engine.tick()
        self.assertFalse(self.actions())
        self.assertFalse(self.engine.sent)
        self.assertFalse(self.engine.faults)
        self.assertTrue(self.engine.snapshot()['relay_sync']['observe_only'])

    def test_retained_radio_tx_is_not_proof_that_switching_is_safe(self):
        self.observe_all_off(); self.band('stn2', 20)
        self.engine.tx.clear(); self.engine.tx_times.clear()
        self.engine.handle('stn2/tx', '0', retained=True)
        self.assertFalse(self.engine.receive_safe('stn2'))

    def test_retained_commands_are_ignored(self):
        self.engine.handle('set/stn2/antm', '0', retained=True)
        self.assertTrue(self.engine.stations['stn2']['auto'])


if __name__ == '__main__': unittest.main()
