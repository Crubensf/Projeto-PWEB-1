// Mapa da página rotas.html: escuta 'rotas:atualizadas' (disparado pelo app.js)
// e desenha os trajetos seguindo as estradas (OSRM), com traço em camadas e
// marcadores: origens = pontos, campus (destino) = marcador-herói pulsante.
(function () {
  const mapaEl = document.getElementById('mapa-rotas');
  if (!mapaEl || typeof L === 'undefined') return;

  let mapa = null;
  let layer = null;

  function init() {
    if (mapa) return;
    mapa = L.map(mapaEl, { scrollWheelZoom: false, zoomControl: true }).setView(
      [-7.0773, -41.467],
      8
    );
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(mapa);
    layer = L.layerGroup().addTo(mapa);
  }

  function iconeOrigem() {
    return L.divIcon({
      className: 'pin',
      html: '<span class="pin-dot"></span>',
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });
  }

  function iconeCampus() {
    return L.divIcon({
      className: 'pin',
      html: '<span class="pin-campus"><span class="pin-campus-core"></span></span>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
  }

  function popupRota(r) {
    const motorista = r.motorista
      ? `${r.motorista.nome}${
          r.motorista.media_avaliacoes !== null
            ? ` · ★ ${r.motorista.media_avaliacoes.toFixed(1)}`
            : ''
        }`
      : 'Motorista';
    return (
      '<div class="popup-rota">' +
      `<strong>${r.nome}</strong>` +
      `<div>${r.origem} → ${r.destino}</div>` +
      `<small>Saída ${r.hora_ida} · R$ ${Number(r.preco).toFixed(2)}</small>` +
      `<div><small>${motorista}</small></div>` +
      '</div>'
    );
  }

  function render(rotas) {
    const comGeo = rotas.filter(
      (r) =>
        r.origem_lat != null &&
        r.origem_lng != null &&
        r.destino_lat != null &&
        r.destino_lng != null
    );
    if (!comGeo.length) {
      mapaEl.hidden = true;
      return;
    }
    mapaEl.hidden = false;
    init();
    layer.clearLayers();

    const bounds = [];
    const destinosVistos = new Set();

    comGeo.forEach((r) => {
      const o = [r.origem_lat, r.origem_lng];
      const d = [r.destino_lat, r.destino_lng];

      // Grupo próprio por rota — permite substituir o fallback pela estrada.
      const grupo = L.layerGroup().addTo(layer);
      let trajeto = desenharTrajeto(grupo, curvaSuave(o, d));

      // Marcador de origem (popup com os dados da rota)
      L.marker(o, { icon: iconeOrigem() }).bindPopup(popupRota(r)).addTo(grupo);

      // Campus (destino) — desenhado UMA vez, mesmo com várias rotas chegando.
      const chave = d[0].toFixed(4) + ',' + d[1].toFixed(4);
      if (!destinosVistos.has(chave)) {
        destinosVistos.add(chave);
        L.marker(d, { icon: iconeCampus() })
          .bindPopup(`<div class="popup-rota"><strong>${r.destino}</strong></div>`)
          .addTo(layer);
      }

      bounds.push(o, d);

      // Upgrade assíncrono: troca a curva pela geometria real da estrada.
      buscarRotaRodoviaria(o, d).then((pts) => {
        if (pts && mapa) {
          trajeto.forEach((l) => grupo.removeLayer(l));
          trajeto = desenharTrajeto(grupo, pts);
        }
      });
    });

    // Container saiu de hidden agora — recalcula tamanho ANTES do fitBounds.
    requestAnimationFrame(() => {
      mapa.invalidateSize(false);
      mapa.fitBounds(bounds, { padding: [55, 55], maxZoom: 12 });
    });
  }

  document.addEventListener('rotas:atualizadas', (ev) => {
    render(ev.detail.rotas || []);
  });
})();
