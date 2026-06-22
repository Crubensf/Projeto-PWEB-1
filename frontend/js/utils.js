// Em produção: Apache serve o frontend e faz proxy de /api/ → backend (porta 8000 interna).
// Em dev local sem Docker: sete API_BASE para 'http://localhost:8000' manualmente.
const API_BASE = '';

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

async function apiRequest(path, { method = 'GET', body = null, isForm = false } = {}) {
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

  window._loadingShow();

  try {
    let resp;
    try {
      resp = await fetch(url, options);
    } catch {
      throw new Error(
        'Sem conexão com o servidor. Verifique sua internet e tente novamente.'
      );
    }

    let data = null;
    try {
      data = await resp.json();
    } catch {}

    if (!resp.ok) {
      const msg =
        (data && (data.detail || data.message)) || `Erro HTTP ${resp.status}`;

      // Sessão expirou — limpa auth local e manda pro login (uma única vez)
      if (
        resp.status === 401 &&
        msg === 'Sessão expirada' &&
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
    window._loadingHide();
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
