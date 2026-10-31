"""MQTT commands sent over the existing FlexRadio TCP session."""

import json
import re
import threading
import time

from split import SplitState


class CommandBridge:
    def __init__(self, station, publish):
        self.station = station
        self.publish = publish
        self.lock = threading.Lock()
        self.connection = None
        self.sequence = 2000
        self.pending = {}
        self.atu_state = {}
        self.split = SplitState()
        self.split_job = None
        self.last_split_value = None
        self.last_split_publish = 0.0

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
            self.split = SplitState()
            self.last_split_value = None
            self.last_split_publish = 0.0

    def detach(self):
        with self.lock:
            self.connection = None
            self.split_job = None
            pending, self.pending = self.pending, {}
        for sequence, (action, value, _) in pending.items():
            self.result(action, value, "disconnected", sequence=sequence)

    def on_message(self, client, userdata, message):
        prefix = f"set/{self.station}/"
        if message.topic not in (prefix + "mox", prefix + "tune", prefix + "atu", prefix + "split"):
            return
        action = message.topic[len(prefix):]
        try:
            value = message.payload.decode("ascii").strip()
        except UnicodeDecodeError:
            value = ""
        offset_hz = 1000
        if action == "split" and value.startswith("{"):
            try:
                request = json.loads(value)
                enabled = request["enabled"]
                offset_hz = request.get("offset_hz", 1000)
                if type(enabled) is not int or enabled not in (0, 1) or type(offset_hz) is not int or not 1 <= abs(offset_hz) <= 100000:
                    raise ValueError()
                value = str(enabled)
            except (ValueError, KeyError, TypeError):
                self.result(action, value, "invalid_payload")
                return
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
            if action == "split":
                if self.split_job is not None:
                    self.result(action, value, "busy")
                    return
                try:
                    steps = self.split.plan(value == "1", offset_hz)
                except ValueError as error:
                    self.result(action, value, str(error))
                    return
                self.split_job = {"steps": steps, "created": None}
                command = self.split_job["steps"].pop(0)
            self._send(action, value, command)

    def _send(self, action, value, command):
        self.sequence += 1
        sequence = self.sequence
        self.pending[sequence] = (action, value, time.monotonic())
        if action == "split":
            self.split_job["command"] = command
        try:
            self.connection.write(f"C{sequence}|{command}\n".encode("ascii"))
        except OSError:
            self.pending.pop(sequence)
            if action == "split":
                self.split_job = None
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
            with self.lock:
                if action == "split" and self.split_job is not None:
                    job = self.split_job
                    if int(match[2], 16) != 0:
                        self.split_job = None
                    else:
                        if job["command"].startswith("slice create "):
                            created = (match[3] or "").split("|", 1)[0].strip()
                            if not created.isdecimal():
                                self.split_job = None
                                self.result(action, value, "invalid_create_response", sequence=sequence)
                                return
                            job["created"] = created
                        if job["steps"]:
                            command = job["steps"].pop(0).replace("{created}", str(job["created"]))
                            self._send(action, value, command)
                            return
                        self.split_job = None
            self.result(action, value, "accepted" if int(match[2], 16) == 0 else "error",
                        sequence=sequence, code=match[2], message=match[3] or "")

    def status(self, line):
        with self.lock:
            self.split.update(line)
            split_value = self.split.value()
        payload = "unknown" if split_value is None else str(split_value)
        now = time.monotonic()
        if payload != self.last_split_value or now - self.last_split_publish >= 2:
            self.publish(f"{self.station}/split", payload, retain=True)
            self.last_split_value, self.last_split_publish = payload, now
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
            if action == "split":
                with self.lock:
                    self.split_job = None
            self.result(action, value, "timeout", sequence=sequence)
