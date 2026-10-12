(() => {
  const slots = document.querySelectorAll('[data-map-slot]');
  function warn(message) {
    slots.forEach(slot => {
      const warning = document.createElement('p');
      warning.className = 'map-warning';
      warning.textContent = message;
      slot.replaceChildren(warning);
    });
  }
  if (!window.d3 || !window.topojson) {
    warn('No se pudo cargar el mapa. Los controles del rotor siguen disponibles.');
    return;
  }
  window.AZIMUT_CENTER = [-5, 43.5];
  window.AZIMUT_ROTORS = [
    { id: 'tw3', name: 'C31XR', color: '#ffb000' },
    { id: 'tw1', name: 'MB7', color: '#a3e635' },
    { id: 'tw2', name: 'MB4', color: '#ff4f87' }
  ].map(rotor => ({ ...rotor, embedded: true, containerId: `${rotor.id}-map-slot`, sourceId: `${rotor.id}-position` }));
  const script = document.createElement('script');
  script.src = 'azimut-map.js';
  script.onerror = () => warn('No se pudo cargar el mapa. Los controles del rotor siguen disponibles.');
  document.head.appendChild(script);
})();
