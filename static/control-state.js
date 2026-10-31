(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ControlState = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const TOPICS = ['control/config', 'pytofront', 'control/heartbeat', 'control/availability'];
  function createConsumer(onState, onFreshness = function () {}, options = {}) {
    const now = options.now || Date.now;
    const schedule = options.setTimeout || setTimeout, cancel = options.clearTimeout || clearTimeout;
    let catalog = null, state = null, heartbeat = null, timer = null, fresh = false, last = null;
    let heartbeatAt = -Infinity;
    const ttl = 5000;
    function freshness(value) {
      if (fresh !== value) { fresh = value; onFreshness(value); }
    }
    function expire() { timer = null; freshness(false); }
    function arm() { if (timer !== null) cancel(timer); timer = schedule(expire, ttl); }
    function render() {
      if (!catalog || !state || !heartbeat || state.c !== catalog.id || state.s !== heartbeat.s || state.r < heartbeat.r || now() - heartbeatAt >= ttl) {
        freshness(false); return;
      }
      const signature = state.s + ':' + state.r + ':' + catalog.id;
      const recovered = !fresh;
      freshness(true);
      if (signature === last && !recovered) return;
      const result = { stacks: {}, relay_sync: state.sync };
      for (const station of ['stn1', 'stn2']) result[station] = Object.assign({}, catalog.stations[station], state.stations[station]);
      for (const [band, description] of Object.entries(catalog.stacks)) {
        const values = state.stacks[band];
        if (!Array.isArray(values) || values.length !== description.salidas || values.some(v => v !== null && typeof v !== 'boolean')) { freshness(false); return; }
        const stack = result.stacks[band] = { salidas: description.salidas };
        for (let i = 1; i <= 3; i++) {
          stack[i] = Object.assign({ nombre: '', tw: 0, haz: null }, description[i] || {}, { estado: values[i - 1] === true, confirmed: i > description.salidas || values[i - 1] !== null });
        }
      }
      for (const station of ['stn1', 'stn2']) if (!result.stacks[String(result[station].band)]) { freshness(false); return; }
      last = signature; onState(result);
    }
    function receive(topic, payload) {
      if (!TOPICS.includes(topic)) return false;
      try {
        if (topic === 'control/availability') {
          if (payload === 'offline') disconnect();
          return true;
        }
        const data = JSON.parse(payload);
        if (!data || typeof data !== 'object') return true;
        if (topic === 'control/config') {
          if (data.v !== 2 || typeof data.id !== 'string' || !data.stations || !data.stacks) return true;
          for (const name of ['stn1', 'stn2']) if (!data.stations[name] || typeof data.stations[name].netbios !== 'string') return true;
          for (const item of Object.values(data.stacks)) if (!item || !Number.isInteger(item.salidas) || item.salidas < 0 || item.salidas > 3) return true;
          catalog = data; render();
        } else if (topic === 'pytofront') {
          // New consumers can be installed before control during a rolling deployment.
          if (data.v === undefined && data.stn1 && data.stn2 && data.stacks) {
            freshness(true); arm(); onState(data); return true;
          }
          if (data.v !== 2 || typeof data.c !== 'string' || typeof data.s !== 'string' || !Number.isInteger(data.r) || data.r < 1 || !data.stations || !data.stacks) return true;
          for (const name of ['stn1', 'stn2']) if (!data.stations[name] || !Number.isInteger(data.stations[name].band) || typeof data.stations[name].auto !== 'boolean') return true;
          if (state && data.s === state.s && data.r < state.r) return true;
          state = data; render();
        } else if (topic === 'control/heartbeat') {
          if (typeof data.s !== 'string' || !Number.isInteger(data.r) || data.r < 1) return true;
          if (heartbeat && data.s === heartbeat.s && data.r < heartbeat.r) return true;
          heartbeat = data; heartbeatAt = now(); arm(); render();
        }
      } catch (_) { /* Invalid input must not refresh liveness or change the interface. */ }
      return true;
    }
    function disconnect() {
      if (timer !== null) cancel(timer);
      timer = null; heartbeat = null; heartbeatAt = -Infinity; freshness(false);
    }
    onFreshness(false);
    return { receive, disconnect, isFresh: () => fresh };
  }
  return { TOPICS, createConsumer };
});
