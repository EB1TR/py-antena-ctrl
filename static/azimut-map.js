(() => {
  const SIZE = 720;
  const MID = SIZE / 2;
  const SCALE = 111;
  const EARTH_RADIUS_KM = 6371.0088;
  const DIRECTION_ARC_LENGTH = Math.PI * SCALE - 1;
  const LABEL_RADIUS = 341;
  const center = window.AZIMUT_CENTER || [-5, 43.5];
  const rotors = window.AZIMUT_ROTORS || [];
  const mapStates = new Map();
  let countryLabels = [];
  let cityLabels = [];
  const projection = d3.geoAzimuthalEquidistant()
    .rotate([-center[0], -center[1]]).translate([MID, MID]).scale(SCALE).clipAngle(179.9);
  const path = d3.geoPath(projection);

  function polarPoint(azimuth, radius) {
    const angle = (azimuth - 90) * Math.PI / 180;
    return [MID + Math.cos(angle) * radius, MID + Math.sin(angle) * radius];
  }

  function bearingFromPoint(x, y) {
    return (Math.atan2(y - MID, x - MID) * 180 / Math.PI + 450) % 360;
  }

  function compassPoint(degrees) {
    const points = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return points[Math.round(degrees / 22.5) % points.length];
  }

  function countryBorderWidth(zoomLevel) {
    return Math.min(.95, .38 + Math.log2(zoomLevel) * .13);
  }

  function directionArcPath(degrees) {
    const origin = [MID, MID];
    const left = polarPoint(degrees - 6, DIRECTION_ARC_LENGTH);
    const right = polarPoint(degrees + 6, DIRECTION_ARC_LENGTH);
    return `M${origin[0]},${origin[1]} L${left[0]},${left[1]} A${DIRECTION_ARC_LENGTH},${DIRECTION_ARC_LENGTH} 0 0 1 ${right[0]},${right[1]} Z`;
  }

  function labelIsFree(box, occupied) {
    const padding = 3;
    const overlaps = occupied.some(other => !(
      box.x2 + padding < other.x1 || box.x1 - padding > other.x2 ||
      box.y2 + padding < other.y1 || box.y1 - padding > other.y2
    ));
    if (!overlaps) occupied.push(box);
    return !overlaps;
  }

  function renderMapLabels(state) {
    const { labelLayer, currentTransform } = state;
    labelLayer.selectAll('*').remove();
    const zoomLevel = currentTransform.k;
    const occupied = [];
    const countryAreaLimit = zoomLevel < 1.7 ? .018 : zoomLevel < 3 ? .006 : zoomLevel < 7 ? .0012 : .00015;

    countryLabels
      .filter(country => country.area >= countryAreaLimit)
      .forEach(country => {
        const [x, y] = currentTransform.apply(country.point);
        const name = country.name;
        const width = Math.max(28, name.length * 5.8);
        const box = { x1: x - width / 2, x2: x + width / 2, y1: y - 7, y2: y + 7 };
        if (x < 18 || x > SIZE - 18 || y < 18 || y > SIZE - 18 || !labelIsFree(box, occupied)) return;
        labelLayer.append('text').attr('class', 'country-label').attr('x', x).attr('y', y).text(name);
      });

    if (zoomLevel < 2.1) return;
    const cityRankLimit = zoomLevel < 3.2 ? 2 : zoomLevel < 5 ? 4 : zoomLevel < 9 ? 6 : zoomLevel < 14 ? 8 : 10;
    cityLabels
      .filter(city => city.rank <= cityRankLimit)
      .forEach(city => {
        const [x, y] = currentTransform.apply(city.point);
        const name = city.name;
        if (!name || x < 22 || x > SIZE - 70 || y < 18 || y > SIZE - 18) return;
        const width = Math.max(24, name.length * 5.2);
        const box = { x1: x + 5, x2: x + 9 + width, y1: y - 7, y2: y + 7 };
        if (!labelIsFree(box, occupied)) return;
        labelLayer.append('circle').attr('class', 'city-dot').attr('cx', x).attr('cy', y).attr('r', 2.3);
        labelLayer.append('text').attr('class', 'city-label').attr('x', x + 5).attr('y', y + 3).text(name);
      });
  }

  function updateRay(id, degrees) {
    if (!Number.isFinite(degrees)) return;
    const normalized = ((degrees % 360) + 360) % 360;
    const rounded = Math.round(normalized) % 360;
    const readout = document.getElementById(`${id}-bearing`);
    if (readout) readout.textContent = `${String(rounded).padStart(3, '0')}° · ${compassPoint(normalized)}`;
    d3.select(`#${id}-map .bearing-cone`).style('display', null).attr('d', directionArcPath(normalized));
  }

  function addDefs(svg, rotorId, rotorColor) {
    const defs = svg.append('defs');
    const ids = {
      ocean: `${rotorId}-ocean-gradient`,
      land: `${rotorId}-land-gradient`,
      coast: `${rotorId}-coast-glow`,
      direction: `${rotorId}-direction-gradient`,
      station: `${rotorId}-station-glow`
    };
    const ocean = defs.append('radialGradient').attr('id', ids.ocean);
    ocean.append('stop').attr('offset', '0%').attr('stop-color', '#102b40');
    ocean.append('stop').attr('offset', '68%').attr('stop-color', '#081a2a');
    ocean.append('stop').attr('offset', '100%').attr('stop-color', '#030b13');
    const land = defs.append('linearGradient').attr('id', ids.land).attr('x2', '0').attr('y2', '1');
    land.append('stop').attr('stop-color', '#486b80');
    land.append('stop').attr('offset', '42%').attr('stop-color', '#294b61');
    land.append('stop').attr('offset', '100%').attr('stop-color', '#142d40');
    const coastGlow = defs.append('filter').attr('id', ids.coast);
    coastGlow.append('feGaussianBlur').attr('stdDeviation', '1.1').attr('result', 'blur');
    const coastMerge = coastGlow.append('feMerge');
    coastMerge.append('feMergeNode').attr('in', 'blur');
    coastMerge.append('feMergeNode').attr('in', 'SourceGraphic');
    const direction = defs.append('radialGradient').attr('id', ids.direction)
      .attr('gradientUnits', 'userSpaceOnUse').attr('cx', MID).attr('cy', MID).attr('r', DIRECTION_ARC_LENGTH);
    [0, .1, .25, .5, .75, 1].forEach(position => {
      const alpha = .03 + .57 * (1 - Math.log1p(position * 9) / Math.log(10));
      direction.append('stop').attr('offset', `${position * 100}%`)
        .attr('stop-color', rotorColor).attr('stop-opacity', alpha);
    });
    const stationGlow = defs.append('filter').attr('id', ids.station);
    stationGlow.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur');
    const stationMerge = stationGlow.append('feMerge');
    stationMerge.append('feMergeNode').attr('in', 'blur');
    stationMerge.append('feMergeNode').attr('in', 'SourceGraphic');
    return ids;
  }

  function buildMap(rotor) {
    const box = document.createElement('section');
    box.className = 'rotor-map';
    const heading = rotor.embedded ? '' : `<header class="map-heading"><h2 class="antenna-name" style="color:${rotor.color}">${rotor.name}</h2>` +
      `<output class="bearing-readout" id="${rotor.id}-bearing" aria-label="Dirección actual de ${rotor.name}">---°</output></header>`;
    box.innerHTML = heading + `<svg class="az-map" id="${rotor.id}-map" viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="Mapa azimutal real de ${rotor.name}, centrado en IN73. Rueda para ampliar y doble clic para restablecer."></svg>`;
    document.getElementById(rotor.containerId || 'az-maps').appendChild(box);

    const svg = d3.select(`#${rotor.id}-map`);
    const ids = addDefs(svg, rotor.id, rotor.color);
    const zoomLayer = svg.append('g').attr('class', 'zoom-layer');
    zoomLayer.append('path').datum({ type: 'Sphere' }).attr('class', 'sphere')
      .attr('fill', `url(#${ids.ocean})`).attr('d', path);
    zoomLayer.append('path').datum(d3.geoGraticule10()).attr('class', 'graticule').attr('d', path);
    zoomLayer.append('g').attr('class', 'land-layer');

    for (let azimuth = 0; azimuth < 360; azimuth += 30) {
      const [x2, y2] = polarPoint(azimuth, 327);
      zoomLayer.append('line').attr('class', 'az-spoke').attr('x1', MID).attr('y1', MID).attr('x2', x2).attr('y2', y2);
      const [x, y] = polarPoint(azimuth, LABEL_RADIUS);
      if (azimuth % 90 !== 0) {
        zoomLayer.append('text').attr('class', 'az-label')
          .attr('x', x).attr('y', y).text(`${azimuth}°`);
      }
    }

    [5000, 10000, 15000, 20000].forEach(distanceKm => {
      const radius = SCALE * distanceKm / EARTH_RADIUS_KM;
      if (radius >= 351) return;
      zoomLayer.append('circle').attr('class', 'az-ring').attr('cx', MID).attr('cy', MID).attr('r', radius);
      if (radius < 327) {
        zoomLayer.append('text').attr('class', 'distance-label').attr('x', MID + 8).attr('y', MID - radius - 5)
          .text(`${distanceKm.toLocaleString('es-ES')} km`);
      }
    });

    zoomLayer.append('path').attr('class', 'bearing-cone').attr('fill', `url(#${ids.direction})`)
      .attr('d', directionArcPath(0)).style('display', 'none');
    zoomLayer.append('circle').attr('class', 'station-halo').attr('cx', MID).attr('cy', MID).attr('r', 11);
    zoomLayer.append('circle').attr('class', 'station-core').attr('cx', MID).attr('cy', MID).attr('r', 4.5)
      .attr('filter', `url(#${ids.station})`);

    const pointerBearing = svg.append('g').attr('class', 'pointer-bearing').style('display', 'none');
    pointerBearing.append('circle').attr('r', 5);
    const readout = pointerBearing.append('g').attr('class', 'pointer-readout');
    readout.append('rect').attr('x', -42).attr('y', -15).attr('width', 84).attr('height', 30).attr('rx', 7);
    readout.append('text').attr('y', 1);

    let currentTransform = d3.zoomIdentity;
    const labelLayer = svg.insert('g', '.pointer-bearing').attr('class', 'map-labels');
    const state = { labelLayer, currentTransform };
    mapStates.set(rotor.id, state);
    const zoom = d3.zoom().scaleExtent([1, 20]).translateExtent([[0, 0], [SIZE, SIZE]])
      .on('zoom', event => {
        currentTransform = event.transform;
        state.currentTransform = currentTransform;
        zoomLayer.attr('transform', currentTransform);
        zoomLayer.select('.country-borders').style('stroke-width', `${countryBorderWidth(currentTransform.k)}px`);
        zoomLayer.select('.land').style('filter', currentTransform.k > 1.5 ? 'none' : null);
        zoomLayer.select('.station-halo').attr('r', 11 / currentTransform.k);
        zoomLayer.select('.station-core').attr('r', 4.5 / currentTransform.k)
          .style('filter', currentTransform.k > 1.5 ? 'none' : null);
        zoomLayer.selectAll('.az-label, .distance-label').style('display', currentTransform.k > 2 ? 'none' : null);
        renderMapLabels(state);
      });
    svg.call(zoom).on('dblclick.zoom', null);

    svg.on('pointermove.azimuth', event => {
      const screenPoint = d3.pointer(event);
      const mapPoint = currentTransform.invert(screenPoint);
      const degrees = bearingFromPoint(mapPoint[0], mapPoint[1]);
      const rounded = Math.round(degrees) % 360;
      const labelX = Math.max(48, Math.min(SIZE - 48, screenPoint[0] + (screenPoint[0] > SIZE - 110 ? -54 : 54)));
      const labelY = Math.max(22, Math.min(SIZE - 22, screenPoint[1] - 24));
      pointerBearing.style('display', null).select('circle').attr('cx', screenPoint[0]).attr('cy', screenPoint[1]);
      readout.attr('transform', `translate(${labelX},${labelY})`)
        .select('text').text(`${String(rounded).padStart(3, '0')}° · ${compassPoint(degrees)}`);
    }).on('pointerleave.azimuth', () => pointerBearing.style('display', 'none'));

    svg.on('click', event => {
      if (event.defaultPrevented) return;
      const [x, y] = currentTransform.invert(d3.pointer(event));
      const degrees = bearingFromPoint(x, y);
      if (typeof window.AZIMUT_SEND_COMMAND === 'function') window.AZIMUT_SEND_COMMAND(`${rotor.id}/set/deg`, Math.round(degrees));
      else if (typeof send_command === 'function') send_command(`${rotor.id}/set/deg`, Math.round(degrees));
    });
    svg.on('dblclick.reset', event => {
      event.preventDefault();
      svg.transition().duration(250).call(zoom.transform, d3.zoomIdentity);
    });
  }

  document.documentElement.style.setProperty('--map-count', rotors.length);
  rotors.forEach(buildMap);
  Promise.all([
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
      .then(response => { if (!response.ok) throw new Error(`Cartografía HTTP ${response.status}`); return response.json(); }),
    fetch('https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_110m_populated_places_simple.geojson')
      .then(response => { if (!response.ok) throw new Error(`Ciudades HTTP ${response.status}`); return response.json(); })
  ])
    .then(([world, places]) => {
      const land = topojson.feature(world, world.objects.land);
      countryLabels = topojson.feature(world, world.objects.countries).features
        .map(feature => ({
          name: feature.properties?.name,
          area: d3.geoArea(feature),
          point: projection(d3.geoCentroid(feature))
        }))
        .filter(country => country.name && country.point)
        .sort((a, b) => b.area - a.area);
      cityLabels = places.features
        .map(feature => ({
          name: feature.properties?.name || feature.properties?.nameascii,
          rank: Number(feature.properties?.scalerank ?? 99),
          point: projection(feature.geometry.coordinates)
        }))
        .filter(city => city.name && city.point)
        .sort((a, b) => a.rank - b.rank);
      const borders = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);
      rotors.forEach(rotor => {
        const layer = d3.select(`#${rotor.id}-map .land-layer`);
        const zoomLevel = mapStates.get(rotor.id)?.currentTransform.k || 1;
        layer.append('path').datum(land).attr('class', 'land')
          .attr('fill', `url(#${rotor.id}-land-gradient)`)
          .attr('filter', `url(#${rotor.id}-coast-glow)`).attr('d', path)
          .style('filter', zoomLevel > 1.5 ? 'none' : null);
        layer.append('path').datum(borders).attr('class', 'country-borders').attr('d', path)
          .style('stroke-width', `${countryBorderWidth(zoomLevel)}px`);
      });
      mapStates.forEach(renderMapLabels);
    })
    .catch(error => console.warn('No se pudo cargar la cartografía:', error));

  rotors.forEach(rotor => {
    const source = document.getElementById(rotor.sourceId || rotor.id);
    if (!source) return;
    const sync = () => updateRay(rotor.id, Number.parseFloat(source.textContent));
    new MutationObserver(sync).observe(source, { childList: true, characterData: true, subtree: true });
    sync();
  });
})();
