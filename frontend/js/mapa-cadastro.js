// Mapa de cadastro de rota: clica para fixar origem (1ª) e destino (2ª),
// arrasta para ajustar. Geocoding reverso preenche os inputs de texto.
(function () {
  const mapaEl = document.getElementById('mapa-cadastro');
  if (!mapaEl || typeof L === 'undefined') return;

  // Centro inicial: Teresina–PI (fallback)
  const centroDefault = [-7.0773, -41.4670];
  const mapa = L.map(mapaEl, { scrollWheelZoom: false }).setView(centroDefault, 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(mapa);

  const inputOrigem = document.getElementById('origem');
  const inputDestino = document.getElementById('destino');
  const inOrigLat = document.getElementById('origem_lat');
  const inOrigLng = document.getElementById('origem_lng');
  const inDestLat = document.getElementById('destino_lat');
  const inDestLng = document.getElementById('destino_lng');

  const iconeBase = (cor) =>
    L.divIcon({
      className: 'marker-pin',
      html: `<div style="background:${cor};color:${cor}"></div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });

  let markerOrigem = null;
  let markerDestino = null;

  // Cache anti-thrashing — não chama nominatim se posição não mudou o suficiente
  let lastGeocode = { lat: 0, lng: 0, key: '' };

  async function geocodeReverso(lat, lng) {
    const key = `${lat.toFixed(4)},${lng.toFixed(4)}`;
    if (key === lastGeocode.key) return null;
    lastGeocode.key = key;
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=14&addressdetails=1`;
      const resp = await fetch(url, { headers: { 'Accept-Language': 'pt-BR' } });
      if (!resp.ok) return null;
      const data = await resp.json();
      const addr = data.address || {};
      // Prioridade: bairro → cidade
      const lugar = addr.suburb || addr.neighbourhood || addr.village ||
                    addr.town || addr.city || addr.municipality;
      const cidade = addr.city || addr.town || addr.municipality || addr.state;
      if (lugar && cidade && lugar !== cidade) return `${lugar}, ${cidade}`;
      return lugar || cidade || data.display_name?.split(',').slice(0, 2).join(', ');
    } catch {
      return null;
    }
  }

  let trajetoLayer = null;

  function desenharLinha() {
    if (!trajetoLayer) trajetoLayer = L.layerGroup().addTo(mapa);
    trajetoLayer.clearLayers();
    if (!(markerOrigem && markerDestino)) return;

    const o = [markerOrigem.getLatLng().lat, markerOrigem.getLatLng().lng];
    const d = [markerDestino.getLatLng().lat, markerDestino.getLatLng().lng];

    // Mostra a curva na hora; troca pela estrada quando o OSRM responde.
    desenharTrajeto(trajetoLayer, curvaSuave(o, d));
    buscarRotaRodoviaria(o, d).then((pts) => {
      if (pts) {
        trajetoLayer.clearLayers();
        desenharTrajeto(trajetoLayer, pts);
      }
    });
  }

  async function setOrigem(latlng) {
    if (markerOrigem) {
      markerOrigem.setLatLng(latlng);
    } else {
      markerOrigem = L.marker(latlng, { draggable: true, icon: iconeBase('#15803D') }).addTo(mapa);
      markerOrigem.on('dragend', () => setOrigem(markerOrigem.getLatLng()));
    }
    inOrigLat.value = latlng.lat.toFixed(6);
    inOrigLng.value = latlng.lng.toFixed(6);
    const nome = await geocodeReverso(latlng.lat, latlng.lng);
    if (nome && inputOrigem && !inputOrigem.dataset.editadoManualmente) {
      inputOrigem.value = nome;
    }
    desenharLinha();
  }

  async function setDestino(latlng) {
    if (markerDestino) {
      markerDestino.setLatLng(latlng);
    } else {
      markerDestino = L.marker(latlng, { draggable: true, icon: iconeBase('#B91C1C') }).addTo(mapa);
      markerDestino.on('dragend', () => setDestino(markerDestino.getLatLng()));
    }
    inDestLat.value = latlng.lat.toFixed(6);
    inDestLng.value = latlng.lng.toFixed(6);
    const nome = await geocodeReverso(latlng.lat, latlng.lng);
    if (nome && inputDestino && !inputDestino.dataset.editadoManualmente) {
      inputDestino.value = nome;
    }
    desenharLinha();
  }

  mapa.on('click', (ev) => {
    if (!markerOrigem) setOrigem(ev.latlng);
    else setDestino(ev.latlng);
  });

  // Se o usuário digita manualmente, paramos de sobrescrever
  [inputOrigem, inputDestino].forEach((el) => {
    if (el) el.addEventListener('input', () => { el.dataset.editadoManualmente = '1'; });
  });
})();
