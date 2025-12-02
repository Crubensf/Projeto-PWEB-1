(function () {
  if (typeof hydrateHeader === 'function') { try { hydrateHeader(); } catch(e) {} }

  function ready(fn){ if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }

  ready(function(){
    const form = document.querySelector('.cadastro-form');
    if (!form) return;

    const senha = document.getElementById('senha');
    const confirmar = document.getElementById('confirmar');
    const perfil = document.getElementById('perfil');
    const blocoMotorista = document.getElementById('dados-motorista');
    const cnh = document.getElementById('cnh');
    const cnhImg = document.getElementById('cnh_imagem');
    const docVeicImg = document.getElementById('doc_veiculo_imagem');
    const msgConfirm = (confirmar && confirmar.parentElement) ? confirmar.parentElement.querySelector('.msg-erro') : null;

    const MAX_MB = 5;
    const MAX_BYTES = MAX_MB * 1024 * 1024;

    const styleEl = document.createElement('style');
    styleEl.textContent = '#dados-motorista.is-open{display:block!important}';
    document.head.appendChild(styleEl);

    function clearMsg(el) {
      if (!el) return;
      const wrap = el.parentElement;
      if (!wrap) return;
      const m = wrap.querySelector('.msg-erro');
      if (m) m.textContent = '';
    }

    function toggleCamposMotorista() {
      if (!blocoMotorista || !perfil) return;
      const isMotorista = perfil.value === 'motorista';

      blocoMotorista.classList.toggle('is-open', isMotorista);
      blocoMotorista.hidden = !isMotorista;
      blocoMotorista.style.setProperty('display', isMotorista ? 'block' : 'none', 'important');

      [cnh, cnhImg, docVeicImg].forEach(function (el) {
        if (!el) return;
        el.required = isMotorista;
        if (!isMotorista) {
          clearMsg(el);
          el.value = '';
        }
      });
    }

    if (perfil) {
      perfil.addEventListener('change', toggleCamposMotorista);
      toggleCamposMotorista();
    }

    if (cnh) {
      cnh.addEventListener('input', function () {
        cnh.value = cnh.value.replace(/\D/g, '').slice(0, 11);
        clearMsg(cnh);
      });
    }

    [cnhImg, docVeicImg].forEach(function (el) {
      if (!el) return;
      el.addEventListener('change', function () {
        clearMsg(el);
        const file = el.files && el.files[0];
        if (file && file.size > MAX_BYTES) {
          const wrap = el.parentElement;
          const m = wrap ? wrap.querySelector('.msg-erro') : null;
          if (m) m.textContent = 'Arquivo muito grande. Máx: ' + MAX_MB + ' MB.';
          el.value = '';
        }
      });
    });

    if (confirmar) {
      confirmar.addEventListener('input', function () {
        if (msgConfirm) msgConfirm.textContent = '';
      });
    }

    form.addEventListener('submit', function (e) {
      if (senha && confirmar && senha.value !== confirmar.value) {
        e.preventDefault();
        if (msgConfirm) msgConfirm.textContent = 'As senhas não coincidem.';
        confirmar.focus();
        return;
      }

      if (perfil && perfil.value === 'motorista' && cnh) {
        const wrap = cnh.parentElement;
        const m = wrap ? wrap.querySelector('.msg-erro') : null;
        if (!/^\d{11}$/.test(cnh.value)) {
          e.preventDefault();
          if (m) m.textContent = 'Informe os 11 dígitos da CNH (somente números).';
          cnh.focus();
          return;
        } else if (m) {
          m.textContent = '';
        }
      }

      if (perfil && perfil.value === 'motorista') {
        if (cnhImg) {
          const f = cnhImg.files && cnhImg.files[0];
          if (f && f.size > MAX_BYTES) {
            e.preventDefault();
            const m = cnhImg.parentElement ? cnhImg.parentElement.querySelector('.msg-erro') : null;
            if (m) m.textContent = 'Arquivo muito grande. Máx: ' + MAX_MB + ' MB.';
            cnhImg.focus();
            return;
          }
        }
        if (docVeicImg) {
          const f2 = docVeicImg.files && docVeicImg.files[0];
          if (f2 && f2.size > MAX_BYTES) {
            e.preventDefault();
            const m2 = docVeicImg.parentElement ? docVeicImg.parentElement.querySelector('.msg-erro') : null;
            if (m2) m2.textContent = 'Arquivo muito grande. Máx: ' + MAX_MB + ' MB.';
            docVeicImg.focus();
            return;
          }
        }
      }

      e.preventDefault();
      const d = new FormData(form);
      const user = {
        nome: d.get('nome') || '',
        email: d.get('email') || '',
        senha: d.get('senha') || '',
        perfil: d.get('perfil') || 'estudante'
      };

      if (typeof saveUsuario !== 'function' || typeof setSessao !== 'function') {
        alert('Erro interno: storage não carregado.');
        return;
      }
      saveUsuario(user);
      setSessao(user.email);
      alert('Cadastro concluído!');
      location.assign('index.html');
    });

    window.__toggleMotorista = function(){
      if (!perfil) return null;
      perfil.value = (perfil.value === 'motorista') ? 'estudante' : 'motorista';
      const ev = new Event('change', {bubbles:true});
      perfil.dispatchEvent(ev);
      return {
        perfil: perfil.value,
        display: getComputedStyle(blocoMotorista).display,
        hidden: blocoMotorista.hidden,
        class: blocoMotorista.className
      };
    };
  });
})();
