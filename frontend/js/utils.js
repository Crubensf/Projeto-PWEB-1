// Em produção (Apache em :80/:443) o /api/ é proxy interno → string vazia.
// Em dev local (http.server em :5500 ou outra porta) aponta pro uvicorn.
// Porta lida de localStorage.api_port (default 8000).
const API_BASE = (() => {
  const port = window.location.port;
  const apacheLike = port === '' || port === '80' || port === '443';
  if (apacheLike) return '';
  // ?api=8001 na URL persiste em localStorage pra próximas páginas
  const url = new URL(window.location.href);
  const paramApi = url.searchParams.get('api');
  if (paramApi) {
    try { localStorage.setItem('api_port', paramApi); } catch {}
  }
  const apiPort = localStorage.getItem('api_port') || '8000';
  return `http://${window.location.hostname}:${apiPort}`;
})();

// Loading overlay — injetado automaticamente no body
(function () {
  const style = document.createElement('style');
  style.textContent =
    '#api-loading{display:none;position:fixed;inset:0;background:rgba(0,0,0,.30);' +
    'z-index:9999;align-items:center;justify-content:center}' +
    '#api-loading span{width:42px;height:42px;border:4px solid #fff;' +
    'border-top-color:transparent;border-radius:50%;' +
    'animation:api-spin .7s linear infinite}' +
    '@keyframes api-spin{to{transform:rotate(360deg)}}';
  document.head.appendChild(style);

  const overlay = document.createElement('div');
  overlay.id = 'api-loading';
  overlay.setAttribute('aria-label', 'Carregando');
  overlay.setAttribute('aria-live', 'polite');
  overlay.innerHTML = '<span></span>';

  let pending = 0;

  window._loadingShow = function () {
    if (++pending === 1) overlay.style.display = 'flex';
  };

  window._loadingHide = function () {
    if (--pending <= 0) {
      pending = 0;
      overlay.style.display = 'none';
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(overlay);
  });
})();

// Promise compartilhada de refresh — evita N requests paralelos disparando N refreshes.
let _refreshInflight = null;

async function _tentarRefresh() {
  if (_refreshInflight) return _refreshInflight;
  _refreshInflight = (async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      return resp.ok;
    } catch {
      return false;
    } finally {
      _refreshInflight = null;
    }
  })();
  return _refreshInflight;
}

async function _doFetch(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error(
      'Sem conexão com o servidor. Verifique sua internet e tente novamente.'
    );
  }
}

async function apiRequest(path, { method = 'GET', body = null, isForm = false, skipOverlay = false } = {}) {
  const url = `${API_BASE}${path}`;
  const options = {
    method,
    headers: {},
    credentials: 'include',
  };
  if (body) {
    if (isForm) {
      options.body = body;
    } else {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
  }

  if (!skipOverlay) window._loadingShow();
  try {
    let resp = await _doFetch(url, options);

    // Access expirado → tenta refresh transparente uma vez, depois retry.
    // Evita loop: não tenta refresh nos próprios endpoints de auth.
    const isAuthEndpoint = path.startsWith('/api/auth/');
    if (resp.status === 401 && !isAuthEndpoint) {
      const ok = await _tentarRefresh();
      if (ok) resp = await _doFetch(url, options);
    }

    let data = null;
    try { data = await resp.json(); } catch {}

    if (!resp.ok) {
      const msg = (data && (data.detail || data.message)) || `Erro HTTP ${resp.status}`;
      if (
        resp.status === 401 &&
        !isAuthEndpoint &&
        !window._sessaoExpiradaRedirecionando
      ) {
        window._sessaoExpiradaRedirecionando = true;
        clearAuth();
        alert('Sua sessão expirou. Faça login novamente.');
        window.location.href = 'login.html';
      }
      throw new Error(msg);
    }

    return data;
  } finally {
    if (!skipOverlay) window._loadingHide();
  }
}

// ==================== AUTH STORAGE ====================
// localStorage guarda apenas dados de exibição (não-sensíveis).
// O token de sessão fica no cookie HttpOnly — inacessível ao JavaScript.

const AUTH_KEY = 'usuario';
const AUTH_TS_KEY = 'usuario_ts';
const AUTH_MAX_AGE_MS = 8 * 60 * 60 * 1000; // 8h, casa com a expiração do JWT

function saveAuth(usuario) {
  if (!usuario) return;
  // Filtra: só guarda o que a UI realmente usa
  const safe = {
    nome: usuario.nome || '',
    perfil: usuario.perfil || '',
  };
  try {
    localStorage.setItem(AUTH_KEY, JSON.stringify(safe));
    localStorage.setItem(AUTH_TS_KEY, String(Date.now()));
  } catch (e) {
    console.warn('Não foi possível salvar dados do usuário:', e);
  }
}

function getUsuario() {
  try {
    const ts = parseInt(localStorage.getItem(AUTH_TS_KEY) || '0', 10);
    if (ts && Date.now() - ts > AUTH_MAX_AGE_MS) {
      clearAuth();
      return null;
    }
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function clearAuth() {
  try {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(AUTH_TS_KEY);
  } catch {}
}

// ==================== SESSION STORAGE ====================
// Filtros da busca de rotas — persistem por aba enquanto o usuário navega.

const FILTROS_ROTAS_KEY = 'filtros_rotas';

function saveFiltrosRotas(filtros) {
  try {
    sessionStorage.setItem(FILTROS_ROTAS_KEY, JSON.stringify(filtros));
  } catch {}
}

function getFiltrosRotas() {
  try {
    const raw = sessionStorage.getItem(FILTROS_ROTAS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// Formata minutos como "1h27" ou "45 min".
function formatarDuracao(minutos) {
  if (!minutos || minutos < 1) return '';
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h}h`;
  return `${h}h${String(m).padStart(2, '0')}`;
}

// ==================== MAPA — TRAJETOS RODOVIÁRIOS ====================
// Helpers compartilhados pelos mapas (listagem + cadastro). Usam Leaflet (L),
// então só são chamados em páginas que carregam o leaflet.js.

// Busca a geometria da rota seguindo as estradas via OSRM (servidor público).
// Recebe [lat, lng]; retorna array de [lat, lng] ou null se falhar.
async function buscarRotaRodoviaria(origem, destino) {
  const url =
    'https://router.project-osrm.org/route/v1/driving/' +
    `${origem[1]},${origem[0]};${destino[1]},${destino[0]}` +
    '?overview=full&geometries=geojson';
  try {
    const resp = await fetch(url);
    if (!resp.ok) return null;
    const data = await resp.json();
    const coords = data && data.routes && data.routes[0] && data.routes[0].geometry.coordinates;
    if (!coords || !coords.length) return null;
    // GeoJSON vem como [lng, lat]; Leaflet quer [lat, lng]
    return coords.map(([lng, lat]) => [lat, lng]);
  } catch {
    return null;
  }
}

// Curva suave (bézier quadrática) entre dois pontos — fallback elegante quando
// o roteamento por estrada não está disponível. Bem melhor que uma reta crua.
function curvaSuave(a, b, curvatura = 0.16) {
  const [lat1, lng1] = a;
  const [lat2, lng2] = b;
  const mlat = (lat1 + lat2) / 2;
  const mlng = (lng1 + lng2) / 2;
  const dlat = lat2 - lat1;
  const dlng = lng2 - lng1;
  const ctrl = [mlat - dlng * curvatura, mlng + dlat * curvatura];
  const pts = [];
  const N = 36;
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const u = 1 - t;
    pts.push([
      u * u * lat1 + 2 * u * t * ctrl[0] + t * t * lat2,
      u * u * lng1 + 2 * u * t * ctrl[1] + t * t * lng2,
    ]);
  }
  return pts;
}

// Desenha um trajeto em 3 camadas (casing branco + núcleo + energia animada).
// Retorna as polylines pra poder remover/substituir depois.
function desenharTrajeto(layerGroup, pontos, opts = {}) {
  const cor = opts.cor || '#15803D';
  // smoothFactor baixo preserva as curvas da estrada mesmo com o mapa afastado.
  const casing = L.polyline(pontos, {
    color: '#ffffff',
    weight: 8,
    opacity: 0.9,
    lineCap: 'round',
    lineJoin: 'round',
    smoothFactor: 0.6,
    className: 'rota-casing',
    interactive: false,
  }).addTo(layerGroup);
  const core = L.polyline(pontos, {
    color: cor,
    weight: 4,
    opacity: 0.95,
    lineCap: 'round',
    lineJoin: 'round',
    smoothFactor: 0.6,
    className: 'rota-core',
    interactive: false,
  }).addTo(layerGroup);
  const flow = L.polyline(pontos, {
    color: '#9BF5BE',
    weight: 4,
    opacity: 0.9,
    lineCap: 'round',
    lineJoin: 'round',
    smoothFactor: 0.6,
    dashArray: '1 14',
    className: 'rota-flow',
    interactive: false,
  }).addTo(layerGroup);
  return [casing, core, flow];
}

// ==================== TEMA (dark mode) ====================
const TEMA_KEY = 'tema';

function aplicarTema(tema) {
  document.documentElement.setAttribute('data-theme', tema);
}

function temaInicial() {
  try {
    const salvo = localStorage.getItem(TEMA_KEY);
    if (salvo === 'dark' || salvo === 'light') return salvo;
  } catch {}
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function alternarTema() {
  const atual = document.documentElement.getAttribute('data-theme') || 'light';
  const novo = atual === 'dark' ? 'light' : 'dark';
  aplicarTema(novo);
  try { localStorage.setItem(TEMA_KEY, novo); } catch {}
  document.querySelectorAll('.btn-tema').forEach((b) => atualizarLabelBotaoTema(b, novo));
}

function atualizarLabelBotaoTema(btn, tema) {
  btn.textContent = tema === 'dark' ? '☀' : '☾';
  btn.setAttribute('aria-label', tema === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro');
}

(function () {
  aplicarTema(temaInicial());
  document.addEventListener('DOMContentLoaded', function () {
    const containers = document.querySelectorAll('.acoes-header');
    containers.forEach((c) => {
      if (c.querySelector('.btn-tema')) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-tema';
      atualizarLabelBotaoTema(btn, document.documentElement.getAttribute('data-theme'));
      btn.addEventListener('click', alternarTema);
      c.insertBefore(btn, c.firstChild);
    });
  });
})();

// ==================== PWA — Service Worker ====================
// Em dev (localhost / http server na porta 5500), o SW só atrapalha: serve
// HTML/CSS/JS antigos em cache, mascarando mudanças. Então NÃO registramos —
// e se houver um SW antigo registrado, removemos e limpamos os caches.
// Em produção (Apache HTTPS no mesmo domínio), registramos pro PWA funcionar.
if ('serviceWorker' in navigator) {
  const host = location.hostname;
  const portaApache = location.port === '' || location.port === '80' || location.port === '443';
  const ehProducao = location.protocol === 'https:' && portaApache;

  if (ehProducao) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.warn('Service worker não registrado:', err);
      });
    });
  } else {
    // Dev: auto-limpeza de SW + caches antigos (resolve mapa/CSP em cache).
    navigator.serviceWorker.getRegistrations().then((regs) => {
      regs.forEach((r) => r.unregister());
    });
    if (window.caches) {
      caches.keys().then((nomes) => nomes.forEach((n) => caches.delete(n)));
    }
  }
}
