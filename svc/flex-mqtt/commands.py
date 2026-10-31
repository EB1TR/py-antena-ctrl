"""MQTT commands sent over the existing FlexRadio TCP session."""

import json
import re
import threading
import time


class CommandBridge:
    def __init__(self, station, publish):
        self.station = station
        self.publish = publish
        self.lock = threading.Lock()
        self.connection = None
        self.sequence = 2000
        self.pending = {}
        self.atu_state = {}

    def result(self, action, value, status, **details):
        self.publish(
            f"{self.station}/{action}/result",
            json.dumps(dict(value=value, status=status, **details)),
            retain=False,
        )

    def attach(self, connection):
        with self.lock:
            self.connection = connection
            self.atu_state = {}

    def detach(self):
        with self.lock:
            self.connection = None
            pending, self.pending = self.pending, {}
        for sequence, (action, value, _) in pending.items():
            self.result(action, value, "disconnected", sequence=sequence)

    def on_message(self, client, userdata, message):
        prefix = f"set/{self.station}/"
        if message.topic not in (prefix + "mox", prefix + "tune", prefix + "atu"):
            return
        action = message.topic[len(prefix):]
        try:
            value = message.payload.decode("ascii").strip()
        except UnicodeDecodeError:
            value = ""
        if message.retain:
            self.result(action, value, "retained_rejected")
            return
        allowed = ("start", "bypass") if action == "atu" else ("0", "1")
        if value not in allowed:
            self.result(action, value, "invalid_payload")
            return
        if action == "atu":
            command = f"atu {value}"
        else:
            command = f"xmit {value}" if action == "mox" else f"transmit tune {'on' if value == '1' else 'off'}"
        with self.lock:
            if self.connection is None:
                self.result(action, value, "unavailable")
                return
            self.sequence += 1
            sequence = self.sequence
            self.pending[sequence] = (action, value, time.monotonic())
            try:
                self.connection.write(f"C{sequence}|{command}\n".encode("ascii"))
            except OSError:
                self.pending.pop(sequence)
                self.result(action, value, "send_error", sequence=sequence)

    def response(self, line):
        match = re.match(r"^R(\d+)\|([0-9a-fA-F]+)(?:\|(.*))?$", line)
        if not match:
            return
        sequence = int(match[1])
        with self.lock:
            pending = self.pending.pop(sequence, None)
        if pending:
            action, value, _ = pending
            self.result(action, value, "accepted" if int(match[2], 16) == 0 else "error",
                        sequence=sequence, code=match[2], message=match[3] or "")

    def status(self, line):
        match = re.match(r"^S[0-9a-fA-F]+\|atu\s+(.+)$", line)
        if match:
            self.atu_state.update(part.split("=", 1) for part in match[1].split() if "=" in part)
            self.publish(f"{self.station}/atu/state", json.dumps(self.atu_state), retain=True)
        tune = re.match(r"^S[0-9a-fA-F]+\|transmit\s+(.+)$", line)
        if tune:
            fields = dict(part.split("=", 1) for part in tune[1].split() if "=" in part)
            if fields.get("tune") in ("0", "1"):
                self.publish(f"{self.station}/tune", fields["tune"], retain=True)

    def expire(self):
        with self.lock:
            expired = [(seq, self.pending.pop(seq)) for seq, item in list(self.pending.items())
                       if time.monotonic() - item[2] >= 5]
        for sequence, (action, value, _) in expired:
            self.result(action, value, "timeout", sequence=sequence)
