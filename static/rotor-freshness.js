/* Position telemetry is the heartbeat: unchanged bearings must still be published. */
(() => {
  const MAX_AGE_MS = 5000;
  const readings = new Map();
  const listeners = new Map();
  function notify(id, fresh) {
    for (const listener of listeners.get(id) || []) listener(fresh);
  }
  function check() {
    for (const [id, reading] of readings) {
      if (reading.fresh && Date.now() - reading.time >= MAX_AGE_MS) {
        reading.fresh = false;
        notify(id, false);
      }
    }
  }
  window.ROTOR_FRESHNESS = {
    watch(id, listener) {
      if (!listeners.has(id)) listeners.set(id, []);
      listeners.get(id).push(listener);
      listener(readings.get(id)?.fresh === true);
    },
    position(id, payload) {
      if (String(payload).trim() === '' || !Number.isFinite(Number(payload))) return false;
      const wasFresh = readings.get(id)?.fresh;
      readings.set(id, { time: Date.now(), fresh: true });
      if (!wasFresh) notify(id, true);
      return true;
    },
    disconnect() {
      readings.clear();
      for (const id of listeners.keys()) notify(id, false);
    }
  };
  setInterval(check, 250);
})();
