/* Local property inspector: no external component library is required. */
(() => {
  let socket, context, settings = {}, pending;
  const ids = ['station', 'offsetKhz', 'showTitle', 'showValue', 'showStation'];
  function render() {
    document.getElementById('station').value = settings.station === 'stn1' ? 'stn1' : 'stn2';
    const offset = document.getElementById('offsetKhz');
    if (offset) offset.value = settings.offsetKhz ?? 1;
    for (const id of ids.slice(2)) document.getElementById(id).checked = settings[id] !== 'hide' && settings[id] !== false;
  }
  function initialize() {
    render();
    for (const id of ids) {
      const control = document.getElementById(id);
      if (!control) continue;
      control.addEventListener('change', () => {
        if (!socket || socket.readyState !== 1) return;
        if (id === 'offsetKhz' && (!control.checkValidity() || !Number.isFinite(Number(control.value)) || Number(control.value) === 0)) return;
        settings[id] = control.type === 'checkbox' ? (control.checked ? 'show' : 'hide') : control.value;
        pending = JSON.stringify(settings);
        socket.send(JSON.stringify({ event: 'setSettings', context, payload: settings }));
      });
    }
  }
  window.connectElgatoStreamDeckSocket = (port, uuid, registerEvent, info, actionInfo) => {
    context = uuid;
    settings = JSON.parse(actionInfo).payload.settings || {};
    pending = undefined;
    render();
    socket = new WebSocket(`ws://127.0.0.1:${port}`);
    socket.onopen = () => {
      socket.send(JSON.stringify({ event: registerEvent, uuid }));
      document.getElementById('status').textContent = 'Configuración de esta tecla';
    };
    socket.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.event !== 'didReceiveSettings') return;
      const incoming = message.payload.settings || {};
      if (pending && JSON.stringify(incoming) !== pending) return;
      pending = undefined;
      settings = incoming; render();
    };
  };
  initialize();
})();
