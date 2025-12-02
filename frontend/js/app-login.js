import { findUsuarioByEmail, setSessao } from './storage.js';
import { hydrateHeader } from './auth.js';

(function () {
  hydrateHeader();

  const form = document.querySelector('form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const d = new FormData(form);
    const email = d.get('email') || '';
    const senha = d.get('senha') || '';

    const u = findUsuarioByEmail(email);

    if (!u || u.senha !== senha) {
      alert('Credenciais inválidas.');
      return;
    }

    setSessao(email);
    location.assign('rotas.html');
  });
})();
