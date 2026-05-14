const API_BASE = 'http://127.0.0.1:8000';

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
      throw new Error(msg);
    }

    return data;
  } finally {
    window._loadingHide();
  }
}

function saveAuth(usuario) {
  if (usuario) localStorage.setItem('usuario', JSON.stringify(usuario));
}

function getUsuario() {
  try {
    const raw = localStorage.getItem('usuario');
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
