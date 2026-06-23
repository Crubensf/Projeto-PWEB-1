(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  async function logout() {
    try {
      await apiRequest('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }

    clearAuth();
    window.location.href = 'index.html';
  }

  function formatDateBr(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const ano = d.getFullYear();
    return `${dia}/${mes}/${ano}`;
  }

  function initHeaderPainelUsuario() {
    const user = getUsuario();

    const btnPainel = document.getElementById('btn-painel-usuario');
    const btnLogin = document.getElementById('btn-login-link');
    const btnCadastrar = document.getElementById('btn-cadastrar-link');
    const btnSair = document.getElementById('btn-sair');

    if (user) {
      if (btnPainel) {
        btnPainel.style.display = 'inline-flex';
        btnPainel.textContent = user.perfil === 'motorista' ? 'Painel do motorista' : 'Meu painel';
      }
      if (btnLogin) btnLogin.style.display = 'none';
      if (btnCadastrar) btnCadastrar.style.display = 'none';
      if (btnSair) btnSair.style.display = 'inline-flex';
    } else {
      if (btnPainel) btnPainel.style.display = 'none';
      if (btnSair) btnSair.style.display = 'none';
    }
  }

  // ===================== HOME: CARD HERO AO VIVO =====================

  function initHeroPreviewLive() {
    const elPartida = document.getElementById('hero-partida-hora');
    const elChegada = document.getElementById('hero-chegada-hora');
    const elCountdown = document.getElementById('hero-countdown');
    if (!elPartida && !elChegada && !elCountdown) return;

    const DURACAO_MIN = 75; // 1h15, igual ao card

    function fmtHora(d) {
      return (
        String(d.getHours()).padStart(2, '0') +
        ':' +
        String(d.getMinutes()).padStart(2, '0')
      );
    }

    function atualizar() {
      const agora = new Date();

      // Próxima partida: próximo múltiplo de 15 min, com 8+ min de antecedência
      const partida = new Date(agora);
      partida.setSeconds(0, 0);
      partida.setMinutes(
        partida.getMinutes() + (15 - (partida.getMinutes() % 15))
      );
      while (partida.getTime() - agora.getTime() < 8 * 60000) {
        partida.setMinutes(partida.getMinutes() + 15);
      }

      const chegada = new Date(partida.getTime() + DURACAO_MIN * 60000);
      const minutos = Math.round(
        (partida.getTime() - agora.getTime()) / 60000
      );

      if (elPartida) elPartida.textContent = fmtHora(partida);
      if (elChegada) elChegada.textContent = fmtHora(chegada);
      if (elCountdown) {
        elCountdown.textContent =
          minutos <= 1 ? 'Sai agora' : 'Sai em ' + minutos + ' min';
      }
    }

    atualizar();
    setInterval(atualizar, 30000);
  }

  // ===================== HOME: ROTAS EM DESTAQUE =====================

  function criarCardRotaDestaque(rota) {
    const article = document.createElement('article');
    article.className = 'cartao rota';

    // Banner de paisagem com overlay de origem → destino
    const banner = document.createElement('div');
    banner.className = 'cartao-banner';
    banner.setAttribute('aria-hidden', 'true');

    const overlay = document.createElement('div');
    overlay.className = 'cartao-banner-overlay';

    const spanOrigem = document.createElement('span');
    spanOrigem.className = 'cbo-origem';
    spanOrigem.textContent = rota.origem;

    const spanSeta = document.createElement('span');
    spanSeta.className = 'cbo-seta';
    spanSeta.setAttribute('aria-hidden', 'true');
    spanSeta.textContent = '→';

    const spanDestino = document.createElement('span');
    spanDestino.className = 'cbo-destino';
    spanDestino.textContent = rota.destino;

    overlay.appendChild(spanOrigem);
    overlay.appendChild(spanSeta);
    overlay.appendChild(spanDestino);
    banner.appendChild(overlay);
    article.appendChild(banner);

    const titulo = document.createElement('h3');
    titulo.textContent = `${rota.origem} → ${rota.destino}`;

    const lista = document.createElement('ul');
    lista.className = 'lista-chip';

    const chipIda = document.createElement('li');
    chipIda.className = 'chip';

    const horaIda = ((rota.hora_ida ?? '') + '').trim();
    chipIda.textContent =
      horaIda && horaIda !== 'null' && horaIda !== 'undefined'
        ? `saída ${horaIda}`
        : 'horário a combinar';

    const chipChegada = document.createElement('li');
    chipChegada.className = 'chip';

    const chegadaEst = ((rota.hora_chegada_estimada ?? '') + '').trim();
    chipChegada.textContent =
      chegadaEst && chegadaEst !== 'null' && chegadaEst !== 'undefined'
        ? `chegada ~${chegadaEst}`
        : 'chegada a combinar';

    lista.appendChild(chipIda);
    lista.appendChild(chipChegada);

    if (rota.duracao_estimada_min) {
      const chipDur = document.createElement('li');
      chipDur.className = 'chip chip-duracao';
      chipDur.textContent = formatarDuracao(rota.duracao_estimada_min);
      lista.appendChild(chipDur);
    }

    const rodape = document.createElement('div');
    rodape.className = 'rodape-rota';

    const preco = document.createElement('span');
    preco.className = 'preco';

    const valor = typeof rota.preco === 'number' ? rota.preco : 0;
    preco.textContent = `R$ ${valor.toFixed(2).replace('.', ',')}`;

    const link = document.createElement('a');
    link.className = 'botao botao-primario';
    link.href = 'rotas.html';
    link.textContent = 'Ver rota';

    rodape.appendChild(preco);
    rodape.appendChild(link);

    article.appendChild(titulo);
    article.appendChild(lista);
    article.appendChild(rodape);

    return article;
  }

  async function initHomeRotas() {
    const container = document.getElementById('destaque-rotas');
    if (!container) return;

    container.innerHTML = '<p>Carregando rotas...</p>';

    try {
      const body = await apiRequest('/api/rotas?limit=3');
      const rotas = body.items || [];
      container.innerHTML = '';

      if (!rotas.length) {
        container.innerHTML = '<p>Não há rotas cadastradas ainda.</p>';
        return;
      }

      rotas.forEach((rota) => {
        const card = criarCardRotaDestaque(rota);
        container.appendChild(card);
      });
    } catch (err) {
      console.error(err);
      container.innerHTML = '<p>Erro ao carregar rotas em destaque.</p>';
    }
  }

  // ===================== CADASTRO DE USUÁRIO =====================

  function initCadastroUsuario() {
    const form = document.querySelector('.cadastro-form');
    if (!form) return;

    const senha = document.getElementById('senha');
    const confirmar = document.getElementById('confirmar');
    const perfil = document.getElementById('perfil');
    const blocoMotorista = document.getElementById('dados-motorista');
    const cnh = document.getElementById('cnh');
    const cnhImg = document.getElementById('cnh_imagem');
    const docVeicImg = document.getElementById('doc_veiculo_imagem');
    const msgConfirm =
      confirmar && confirmar.parentElement
        ? confirmar.parentElement.querySelector('.msg-erro')
        : null;

    const MAX_MB = 5;
    const MAX_BYTES = MAX_MB * 1024 * 1024;

    if (blocoMotorista) {
      const styleEl = document.createElement('style');
      styleEl.textContent =
        '#dados-motorista.is-open{display:block!important}';
      document.head.appendChild(styleEl);
    }

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
      blocoMotorista.style.setProperty(
        'display',
        isMotorista ? 'block' : 'none',
        'important'
      );

      [cnh, cnhImg, docVeicImg].forEach((el) => {
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
      cnh.addEventListener('input', () => {
        cnh.value = cnh.value.replace(/\D/g, '').slice(0, 11);
        clearMsg(cnh);
      });
    }

    [cnhImg, docVeicImg].forEach((el) => {
      if (!el) return;
      el.addEventListener('change', () => {
        clearMsg(el);
        const file = el.files && el.files[0];
        if (file && file.size > MAX_BYTES) {
          const wrap = el.parentElement;
          const m = wrap ? wrap.querySelector('.msg-erro') : null;
          if (m)
            m.textContent =
              'Arquivo muito grande. Máx: ' + MAX_MB + ' MB.';
          el.value = '';
        }
      });
    });

    if (confirmar) {
      confirmar.addEventListener('input', () => {
        if (msgConfirm) msgConfirm.textContent = '';
      });
    }

    const btnSubmitCad = form.querySelector('button[type="submit"]');

    const nome = document.getElementById('nome');
    const email = document.getElementById('email');
    const aceite = document.getElementById('aceite');
    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function setErro(input, msg) {
      if (!input) return;
      const wrap = input.parentElement;
      const m = wrap ? wrap.querySelector('.msg-erro') : null;
      if (m) m.textContent = msg || '';
      if (msg) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
    }

    // Limpa erro ao corrigir
    [nome, email, senha, confirmar, perfil].forEach((el) => {
      if (!el) return;
      const ev = el.tagName === 'SELECT' ? 'change' : 'input';
      el.addEventListener(ev, () => setErro(el, ''));
    });

    function validarCadastro() {
      let ok = true;
      let primeiroInvalido = null;
      const fail = (input, msg) => {
        setErro(input, msg);
        if (!primeiroInvalido) primeiroInvalido = input;
        ok = false;
      };

      if (nome && (nome.value.trim().length < 2 || nome.value.length > 120)) {
        fail(nome, 'Informe seu nome completo (2–120 caracteres).');
      }
      if (email && !EMAIL_RE.test(email.value.trim())) {
        fail(email, 'Informe um e-mail válido.');
      }
      if (senha && senha.value.length < 6) {
        fail(senha, 'A senha deve ter no mínimo 6 caracteres.');
      }
      if (confirmar && senha && senha.value !== confirmar.value) {
        fail(confirmar, 'As senhas não coincidem.');
      }
      if (perfil && !perfil.value) {
        fail(perfil, 'Selecione um perfil.');
      }
      if (perfil && perfil.value === 'motorista' && cnh && !/^\d{11}$/.test(cnh.value)) {
        fail(cnh, 'Informe os 11 dígitos da CNH (somente números).');
      }
      if (aceite && !aceite.checked) {
        alert('Você precisa aceitar os Termos de Uso e a Política de Privacidade.');
        ok = false;
      }

      if (!ok && primeiroInvalido) primeiroInvalido.focus();
      return ok;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!validarCadastro()) return;

      const formData = new FormData(form);

      if (!formData.get('perfil')) {
        formData.set('perfil', 'estudante');
      }

      if (btnSubmitCad) btnSubmitCad.disabled = true;
      try {
        const data = await apiRequest('/api/auth/register', {
          method: 'POST',
          body: formData,
          isForm: true,
        });

        saveAuth(data.usuario);
        location.assign('painel.html');
      } catch (err) {
        console.error(err);
        alert('Erro ao cadastrar: ' + err.message);
      } finally {
        if (btnSubmitCad) btnSubmitCad.disabled = false;
      }
    });
  }

  // ===================== LOGIN =====================

  function initLogin() {
    const form = document.querySelector(
      'form.login-form, form.form-login, form#form-login'
    );
    if (!form) return;

    const btn = form.querySelector('button[type="submit"]');
    const emailInput = form.querySelector('#email');
    const senhaInput = form.querySelector('#senha');
    const senhaWrap = senhaInput ? senhaInput.closest('.login-campo') : null;
    const msgGeral = senhaWrap ? senhaWrap.querySelector('.msg-erro') : null;
    const emailWrap = emailInput ? emailInput.closest('.login-campo') : null;
    const msgEmail = emailWrap ? emailWrap.querySelector('.msg-erro') : null;
    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function setLoginErro(input, msgEl, msg) {
      if (msgEl) msgEl.textContent = msg || '';
      if (input) {
        if (msg) input.setAttribute('aria-invalid', 'true');
        else input.removeAttribute('aria-invalid');
      }
    }

    if (emailInput) {
      emailInput.addEventListener('input', () =>
        setLoginErro(emailInput, msgEmail, '')
      );
    }
    if (senhaInput) {
      senhaInput.addEventListener('input', () =>
        setLoginErro(senhaInput, msgGeral, '')
      );
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      setLoginErro(emailInput, msgEmail, '');
      setLoginErro(senhaInput, msgGeral, '');

      const d = new FormData(form);
      const email = (d.get('email') || '').toString().trim();
      const senha = (d.get('senha') || '').toString();

      if (!EMAIL_RE.test(email)) {
        setLoginErro(emailInput, msgEmail, 'Informe um e-mail válido.');
        if (emailInput) emailInput.focus();
        return;
      }
      if (!senha) {
        setLoginErro(senhaInput, msgGeral, 'Informe sua senha.');
        if (senhaInput) senhaInput.focus();
        return;
      }

      if (btn) btn.disabled = true;
      try {
        const data = await apiRequest('/api/auth/login', {
          method: 'POST',
          body: { email, senha },
        });

        saveAuth(data.usuario);
        location.assign('painel.html');
      } catch (err) {
        console.error(err);
        if (msgGeral) setLoginErro(senhaInput, msgGeral, err.message);
        else alert('Erro ao fazer login: ' + err.message);
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  // ===================== ROTAS (LISTAGEM) =====================

  function mapDiaLabelToKey(label) {
    const l = label.toLowerCase();
    if (l.startsWith('seg')) return 'seg';
    if (l.startsWith('ter')) return 'ter';
    if (l.startsWith('qua')) return 'qua';
    if (l.startsWith('qui')) return 'qui';
    if (l.startsWith('sex')) return 'sex';
    if (l.startsWith('sáb') || l.startsWith('sab')) return 'sab';
    if (l.startsWith('dom')) return 'dom';
    return '';
  }

  function initRotas() {
    const container = document.querySelector('.lista-resultados');
    if (!container) return;

    const inputOrigem = document.getElementById('origem');
    const inputDestino = document.getElementById('destino');
    const chips = document.querySelectorAll('.chip-dia');
    const btnNovaBusca = document.getElementById('btnNovaBusca');
    const tituloLista = document.getElementById('tituloLista');
    const msgSem = container.querySelector('.sem-resultados');

    function limparCards() {
      const cards = container.querySelectorAll('.linha-card');
      cards.forEach((c) => c.remove());
    }

    function appendCardRota(r) {
        const artigo = document.createElement('article');
        artigo.className = 'linha-card';

        const header = document.createElement('header');
        header.className = 'linha-topo';

        const h2 = document.createElement('h2');
        h2.className = 'nome-motorista';
        h2.textContent = r.nome || 'Rota';

        const user = getUsuario();
        const podeReservar = user && user.perfil === 'estudante';

        const acao = document.createElement('button');
        acao.type = 'button';
        acao.className = podeReservar ? 'botao botao-primario' : 'botao botao-suave';
        acao.textContent = podeReservar ? 'Reservar' : 'Saiba mais';
        if (podeReservar) {
          acao.addEventListener('click', () => abrirModalReservar(r));
        } else {
          acao.disabled = !user;
          if (!user) acao.title = 'Faça login como estudante para reservar';
        }

        header.appendChild(h2);
        header.appendChild(acao);

        const info = document.createElement('div');
        info.className = 'linha-info';

        const origDest = document.createElement('div');
        origDest.className = 'origem-destino';

        const spanOrigem = document.createElement('span');
        spanOrigem.className = 'cidade origem';
        spanOrigem.textContent = r.origem;

        const sep = document.createElement('span');
        sep.className = 'separador';
        sep.textContent = '→';

        const spanDestino = document.createElement('span');
        spanDestino.className = 'cidade destino';
        spanDestino.textContent = r.destino;

        origDest.appendChild(spanOrigem);
        origDest.appendChild(sep);
        origDest.appendChild(spanDestino);

        const horarios = document.createElement('div');
        horarios.className = 'horarios';

        const horaIda = ((r.hora_ida ?? '') + '').trim();
        const chegadaEst = ((r.hora_chegada_estimada ?? '') + '').trim();

        const hSaida = document.createElement('div');
        hSaida.className = 'horario';
        hSaida.innerHTML =
          '<span class="rotulo">Saída</span><strong class="hora">' +
          (horaIda || '-') +
          '</strong>';

        const hChegada = document.createElement('div');
        hChegada.className = 'horario';
        hChegada.innerHTML =
          '<span class="rotulo">Chegada est.</span><strong class="hora">' +
          (chegadaEst || '—') +
          '</strong>';

        horarios.appendChild(hSaida);
        if (r.duracao_estimada_min) {
          const dur = document.createElement('div');
          dur.className = 'horario-duracao';
          dur.innerHTML =
            '<span class="seta-trajeto">→</span>' +
            `<span class="duracao-badge">${formatarDuracao(r.duracao_estimada_min)}</span>`;
          horarios.appendChild(dur);
        }
        horarios.appendChild(hChegada);

        info.appendChild(origDest);
        info.appendChild(horarios);

        artigo.appendChild(header);
        artigo.appendChild(info);

        if (r.motorista) {
          const rodape = document.createElement('div');
          rodape.className = 'rota-motorista';
          rodape.innerHTML =
            `<span class="motorista-nome">${r.motorista.nome}</span>` +
            (r.motorista.media_avaliacoes !== null
              ? ` · <span class="motorista-rating">★ ${r.motorista.media_avaliacoes.toFixed(1)}` +
                ` <small>(${r.motorista.total_avaliacoes})</small></span>`
              : ' · <span class="motorista-rating-vazio">sem avaliações ainda</span>');
          artigo.appendChild(rodape);
        }

        container.insertBefore(artigo, msgSem || null);
    }

    function renderRotasLista(rotas, diaLabel) {
      limparCards();
      if (!rotas || !rotas.length) {
        if (msgSem) msgSem.hidden = false;
      } else {
        if (msgSem) msgSem.hidden = true;
        rotas.forEach(appendCardRota);
      }
      if (tituloLista) {
        tituloLista.textContent = `Rotas disponíveis${
          diaLabel ? ` — ${diaLabel}` : ''
        }`;
      }
      document.dispatchEvent(
        new CustomEvent('rotas:atualizadas', { detail: { rotas: rotas || [] } })
      );
    }

    // Restaura filtros salvos na sessão
    const filtrosSalvos = getFiltrosRotas();
    if (filtrosSalvos) {
      if (inputOrigem && filtrosSalvos.origem)
        inputOrigem.value = filtrosSalvos.origem;
      if (inputDestino && filtrosSalvos.destino)
        inputDestino.value = filtrosSalvos.destino;
      if (filtrosSalvos.dia) {
        chips.forEach((c) => {
          if (mapDiaLabelToKey(c.textContent.trim()) === filtrosSalvos.dia) {
            chips.forEach((x) => x.classList.remove('ativo'));
            c.classList.add('ativo');
          }
        });
      }
    }

    const PAGE_SIZE = 10;
    let offsetAtual = 0;
    let totalAtual = 0;

    const inputPrecoMin = document.getElementById('filtro-preco-min');
    const inputPrecoMax = document.getElementById('filtro-preco-max');
    const inputHoraMin = document.getElementById('filtro-hora-min');
    const inputHoraMax = document.getElementById('filtro-hora-max');
    const selectOrdenar = document.getElementById('filtro-ordenar');
    const btnCarregarMais = document.getElementById('btn-carregar-mais');
    const resumoPaginacao = document.getElementById('resumo-paginacao');

    function montarParams(offset) {
      const params = new URLSearchParams();
      const origemVal = inputOrigem ? inputOrigem.value : '';
      const destinoVal = inputDestino ? inputDestino.value : '';
      if (origemVal) params.append('origem', origemVal);
      if (destinoVal) params.append('destino', destinoVal);

      let diaLabel = '';
      let diaKey = '';
      const chipAtivo = document.querySelector('.chip-dia.ativo');
      if (chipAtivo) {
        diaLabel = chipAtivo.textContent.trim();
        diaKey = mapDiaLabelToKey(diaLabel);
        if (diaKey) params.append('dia', diaKey);
      }

      if (inputPrecoMin && inputPrecoMin.value) params.append('preco_min', inputPrecoMin.value);
      if (inputPrecoMax && inputPrecoMax.value) params.append('preco_max', inputPrecoMax.value);
      if (inputHoraMin && inputHoraMin.value) params.append('hora_min', inputHoraMin.value);
      if (inputHoraMax && inputHoraMax.value) params.append('hora_max', inputHoraMax.value);
      if (selectOrdenar && selectOrdenar.value) params.append('ordenar_por', selectOrdenar.value);

      params.append('limit', String(PAGE_SIZE));
      params.append('offset', String(offset));

      saveFiltrosRotas({
        origem: origemVal,
        destino: destinoVal,
        dia: diaKey,
      });

      return { params, diaLabel };
    }

    function renderSkeletonsRotas(qtd = 3) {
      limparCards();
      if (msgSem) msgSem.hidden = true;
      for (let i = 0; i < qtd; i++) {
        const card = document.createElement('article');
        card.className = 'linha-card skeleton-card';
        card.innerHTML =
          '<div class="skeleton-linha media"></div>' +
          '<div class="skeleton-linha cheia"></div>' +
          '<div class="skeleton-linha curta"></div>';
        container.insertBefore(card, msgSem || null);
      }
    }

    async function carregarRotas() {
      offsetAtual = 0;
      totalAtual = 0;
      renderSkeletonsRotas(3);
      try {
        const { params, diaLabel } = montarParams(0);
        const body = await apiRequest(`/api/rotas?${params.toString()}`, { skipOverlay: true });
        totalAtual = body.total;
        renderRotasLista(body.items, diaLabel);
        offsetAtual = body.items.length;
        atualizarPaginacao();
      } catch (err) {
        console.error(err);
        limparCards();
        if (msgSem) {
          msgSem.hidden = false;
          msgSem.textContent = 'Erro ao carregar rotas. Tente novamente.';
        }
        atualizarPaginacao();
      }
    }

    async function carregarMais() {
      try {
        const { params } = montarParams(offsetAtual);
        const body = await apiRequest(`/api/rotas?${params.toString()}`);
        body.items.forEach(appendCardRota);
        offsetAtual += body.items.length;
        atualizarPaginacao();
      } catch (err) {
        console.error(err);
      }
    }

    function atualizarPaginacao() {
      if (btnCarregarMais) {
        btnCarregarMais.hidden = offsetAtual >= totalAtual;
      }
      if (resumoPaginacao) {
        if (totalAtual === 0) {
          resumoPaginacao.textContent = '';
        } else {
          resumoPaginacao.textContent =
            `Mostrando ${offsetAtual} de ${totalAtual} rota${totalAtual === 1 ? '' : 's'}`;
        }
      }
    }

    const carregarRotasDebounced = debounce(carregarRotas, 400);

    if (inputOrigem) {
      inputOrigem.addEventListener('input', carregarRotasDebounced);
    }

    if (inputDestino) {
      inputDestino.addEventListener('input', carregarRotasDebounced);
    }

    chips.forEach((chip) => {
      chip.addEventListener('click', () => {
        chips.forEach((c) => c.classList.remove('ativo'));
        chip.classList.add('ativo');
        carregarRotas();
      });
    });

    if (btnNovaBusca) {
      btnNovaBusca.addEventListener('click', () => {
        carregarRotas();
        const resultados = document.querySelector('.resultados');
        if (resultados) {
          resultados.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }

    [inputPrecoMin, inputPrecoMax, inputHoraMin, inputHoraMax].forEach((el) => {
      if (el) el.addEventListener('change', carregarRotas);
    });
    if (selectOrdenar) selectOrdenar.addEventListener('change', carregarRotas);
    if (btnCarregarMais) btnCarregarMais.addEventListener('click', carregarMais);

    carregarRotas();
  }

  // ===================== MODAL DE RESERVA =====================

  const DIA_LABEL = {
    seg: 'segunda',
    ter: 'terça',
    qua: 'quarta',
    qui: 'quinta',
    sex: 'sexta',
    sab: 'sábado',
    dom: 'domingo',
  };

  function abrirModalReservar(rota) {
    const dialog = document.getElementById('modal-reservar');
    if (!dialog || typeof dialog.showModal !== 'function') {
      // Fallback se o navegador não suporta <dialog>
      const data = prompt('Data da viagem (AAAA-MM-DD):');
      if (data) confirmarReserva(rota.id, data);
      return;
    }

    const nomeEl = document.getElementById('modal-rota-nome');
    const diasEl = document.getElementById('modal-rota-dias');
    const dataInput = document.getElementById('modal-data');
    const erroEl = document.getElementById('modal-erro');
    const btnCancelar = document.getElementById('modal-cancelar');
    const form = document.getElementById('form-reservar');

    if (nomeEl) nomeEl.textContent = `${rota.nome} — ${rota.origem} → ${rota.destino}`;
    if (diasEl) {
      const dias = (rota.dias_semana || []).map((d) => DIA_LABEL[d] || d).join(', ');
      diasEl.textContent = `Opera em: ${dias}`;
    }

    if (dataInput) {
      const hoje = new Date();
      dataInput.min = hoje.toISOString().slice(0, 10);
      dataInput.value = '';
    }
    if (erroEl) {
      erroEl.hidden = true;
      erroEl.textContent = '';
    }

    if (btnCancelar) {
      btnCancelar.onclick = () => dialog.close();
    }

    form.onsubmit = async (ev) => {
      ev.preventDefault();
      if (!dataInput || !dataInput.value) return;
      const ok = await confirmarReserva(rota.id, dataInput.value, erroEl);
      if (ok) dialog.close();
    };

    dialog.showModal();
  }

  async function confirmarReserva(rotaId, data, erroEl) {
    try {
      await apiRequest('/api/estudante/viagens', {
        method: 'POST',
        body: { rota_id: rotaId, data: data },
      });
      alert('Reserva confirmada!');
      return true;
    } catch (err) {
      if (erroEl) {
        erroEl.textContent = err.message || 'Erro ao reservar.';
        erroEl.hidden = false;
      } else {
        alert(err.message || 'Erro ao reservar.');
      }
      return false;
    }
  }

  // ===================== PAINEL (APENAS MOTORISTA) =====================

  function renderRotasMotorista(rotas, container, msgVaziaEl) {
    if (!container) return;
    container.innerHTML = '';

    if (!rotas || !rotas.length) {
      if (msgVaziaEl) msgVaziaEl.style.display = 'block';
      return;
    }

    if (msgVaziaEl) msgVaziaEl.style.display = 'none';

    rotas.forEach((r) => {
      const item = document.createElement('div');
      item.className = 'item-card';

      let rotaId = null;
      if (r.id != null) rotaId = r.id;
      else if (r.rota_id != null) rotaId = r.rota_id;
      else if (r._id != null) rotaId = r._id;
      if (rotaId != null) {
        item.dataset.rotaId = String(rotaId);
      }

      const info = document.createElement('div');
      info.className = 'info';

      const strong = document.createElement('strong');
      strong.textContent = `${r.origem} → ${r.destino}`;

      const smallDiasHora = document.createElement('small');
      const dias = Array.isArray(r.dias_semana)
        ? r.dias_semana.join(', ')
        : r.dias_semana;
      const horaIda = ((r.hora_ida ?? '') + '').trim();
      smallDiasHora.textContent = `${dias || ''} • ${horaIda || ''}`;

      const smallVagas = document.createElement('small');
      smallVagas.textContent = `Vagas: ${r.vagas}`;

      info.appendChild(strong);
      info.appendChild(smallDiasHora);
      info.appendChild(smallVagas);

      const info2 = document.createElement('div');
      info2.className = 'info-secundaria';

      const spanStatus = document.createElement('span');
      spanStatus.className = 'status ativo';
      spanStatus.textContent = 'Reservas: (em breve)';

      const btnEditar = document.createElement('button');
      btnEditar.type = 'button';
      btnEditar.className = 'botao botao-suave btn-editar-rota';
      btnEditar.textContent = 'Editar rota';

      const btnExcluir = document.createElement('button');
      btnExcluir.type = 'button';
      btnExcluir.className = 'botao botao-suave btn-excluir-rota';
      btnExcluir.textContent = 'Excluir rota';

      info2.appendChild(spanStatus);
      info2.appendChild(btnEditar);
      info2.appendChild(btnExcluir);

      item.appendChild(info);
      item.appendChild(info2);

      container.appendChild(item);
    });
  }

  async function carregarPainelMotorista() {
    const spanRotasAtivas = document.getElementById('qtd-rotas-ativas');
    const spanViagensHoje = document.getElementById('qtd-viagens-hoje');
    const spanAlunosHoje = document.getElementById('qtd-alunos-hoje');

    const listaRotas = document.getElementById('lista-rotas-motorista');
    const msgSemRotas = document.getElementById('msg-sem-rotas');

    const filtroData = document.getElementById('filtro-data');
    const listaViagensDia = document.getElementById('lista-viagens-dia');
    const msgSemViagensDia = document.getElementById('msg-sem-viagens-dia');

    const [resumoResult, rotasResult] = await Promise.allSettled([
      apiRequest('/api/motorista/resumo'),
      apiRequest('/api/motorista/minhas-rotas'),
    ]);

    if (resumoResult.status === 'fulfilled') {
      const resumo = resumoResult.value;
      if (spanRotasAtivas) spanRotasAtivas.textContent = resumo.rotas_ativas;
      if (spanViagensHoje) spanViagensHoje.textContent = resumo.viagens_hoje;
      if (spanAlunosHoje) spanAlunosHoje.textContent = resumo.alunos_hoje;
    } else {
      console.error(resumoResult.reason);
    }

    if (rotasResult.status === 'fulfilled') {
      renderRotasMotorista(rotasResult.value, listaRotas, msgSemRotas);
    } else {
      console.error(rotasResult.reason);
    }

    if (listaRotas) {
      listaRotas.addEventListener('click', async function (e) {
        const target = e.target;

        const btnEditar = target.closest
          ? target.closest('.btn-editar-rota')
          : null;

        if (btnEditar) {
          const item = btnEditar.closest('.item-card');
          if (!item) return;

          const rotaId = item.dataset.rotaId;
          if (!rotaId) {
            alert('Não foi possível identificar essa rota para edição.');
            return;
          }

          window.location.href = `cadastroRotas.html?rotaId=${rotaId}`;
          return;
        }

        const btnExcluir = target.closest
          ? target.closest('.btn-excluir-rota')
          : null;
        if (!btnExcluir) return;

        const item = btnExcluir.closest('.item-card');
        if (!item) return;

        const rotaId = item.dataset.rotaId;
        if (!rotaId) {
          alert('Não foi possível identificar essa rota para exclusão.');
          return;
        }

        if (!confirm('Tem certeza que deseja excluir esta rota?')) {
          return;
        }

        try {
          await apiRequest('/api/motorista/rotas/' + rotaId, {
            method: 'DELETE',
          });
          item.remove();
          if (spanRotasAtivas) {
            const atual = parseInt(spanRotasAtivas.textContent || '0', 10);
            if (!Number.isNaN(atual) && atual > 0) {
              spanRotasAtivas.textContent = String(atual - 1);
            }
          }
          if (!listaRotas.children.length && msgSemRotas) {
            msgSemRotas.style.display = 'block';
          }
        } catch (err) {
          console.error(err);
          alert('Erro ao excluir rota: ' + (err.message || ''));
        }
      });
    }

    if (filtroData && listaViagensDia) {
      filtroData.addEventListener('change', async () => {
        const dataSel = filtroData.value;
        if (!dataSel) return;

        try {
          const viagens = await apiRequest(
            `/api/motorista/viagens?data=${dataSel}`
          );

          listaViagensDia.innerHTML = '';

          if (!viagens || !viagens.length) {
            if (msgSemViagensDia) msgSemViagensDia.style.display = 'block';
            return;
          }
          if (msgSemViagensDia)
            msgSemViagensDia.style.display = 'none';

          viagens.forEach((v) => {
            const item = document.createElement('div');
            item.className = 'item-card';

            const info = document.createElement('div');
            info.className = 'info';
            const strong = document.createElement('strong');
            strong.textContent = `Rota #${v.rota_id}`;
            const smallData = document.createElement('small');
            smallData.textContent = formatDateBr(v.data);

            info.appendChild(strong);
            info.appendChild(smallData);

            const info2 = document.createElement('div');
            info2.className = 'info-secundaria';
            const smallStatus = document.createElement('small');
            smallStatus.textContent = `Status: ${v.status}`;
            info2.appendChild(smallStatus);

            item.appendChild(info);
            item.appendChild(info2);
            listaViagensDia.appendChild(item);
          });
        } catch (err) {
          console.error(err);
        }
      });
    }
  }

  function initPainel() {
    const painelTopo = document.querySelector('.painel-topo');
    if (!painelTopo) return;

    const user = getUsuario();
    if (!user) {
      location.href = 'login.html';
      return;
    }

    const nomeSpan = document.getElementById('nome-usuario');
    const textoTipo = document.getElementById('texto-tipo-usuario');
    const blocoMotorista = document.getElementById('bloco-motorista');
    const blocoPassageiro = document.getElementById('bloco-passageiro');
    const btnSair = document.getElementById('btn-sair');

    if (nomeSpan) {
      const primeiroNome = (user.nome || '').split(' ')[0] || 'Usuário';
      nomeSpan.textContent = primeiroNome;
    }

    if (btnSair) {
      btnSair.addEventListener('click', logout);
    }

    if (user.perfil === 'motorista') {
      if (textoTipo) {
        textoTipo.textContent =
          'Aqui você vê as rotas que cadastrou e quantas reservas cada uma possui.';
      }
      if (blocoMotorista) blocoMotorista.style.display = 'block';
      carregarPainelMotorista();
    } else {
      if (textoTipo) {
        textoTipo.textContent = 'Aqui você acompanha suas viagens.';
      }
      if (blocoPassageiro) blocoPassageiro.style.display = 'block';
      carregarPainelPassageiro();
    }
  }

  // ===================== PAINEL PASSAGEIRO =====================

  function renderSkeletonsViagens(container, qtd) {
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < qtd; i++) {
      const card = document.createElement('article');
      card.className = 'linha-card skeleton-card';
      card.innerHTML =
        '<div class="skeleton-linha media"></div>' +
        '<div class="skeleton-linha cheia"></div>';
      container.appendChild(card);
    }
  }

  async function carregarPainelPassageiro() {
    const proximas = document.getElementById('lista-proximas-viagens');
    const historico = document.getElementById('lista-historico-viagens');
    const msgSemProximas = document.getElementById('msg-sem-proximas');
    const msgSemHistorico = document.getElementById('msg-sem-historico');

    if (msgSemProximas) msgSemProximas.style.display = 'none';
    if (msgSemHistorico) msgSemHistorico.style.display = 'none';
    renderSkeletonsViagens(proximas, 2);
    renderSkeletonsViagens(historico, 2);

    try {
      const viagens = await apiRequest('/api/estudante/viagens', { skipOverlay: true });
      const hoje = new Date().toISOString().slice(0, 10);

      const futuras = viagens.filter(
        (v) => v.status === 'reservada' && v.data >= hoje
      );
      const passadas = viagens.filter(
        (v) => v.status !== 'reservada' || v.data < hoje
      );

      renderViagensPassageiro(proximas, futuras, msgSemProximas, true);
      renderViagensPassageiro(historico, passadas, msgSemHistorico, false);
    } catch (err) {
      console.error(err);
    }
  }

  function renderViagensPassageiro(container, viagens, msgVazia, podeCancelar) {
    if (!container) return;
    container.innerHTML = '';

    if (!viagens.length) {
      if (msgVazia) msgVazia.style.display = 'block';
      return;
    }
    if (msgVazia) msgVazia.style.display = 'none';

    viagens.forEach((v) => {
      const card = document.createElement('article');
      card.className = 'linha-card';

      const header = document.createElement('header');
      header.className = 'linha-topo';

      const h2 = document.createElement('h2');
      h2.className = 'nome-motorista';
      h2.textContent = v.rota.nome || 'Viagem';

      const status = document.createElement('span');
      status.className = `tag-status tag-${v.status}`;
      status.textContent = v.status;

      header.appendChild(h2);
      header.appendChild(status);

      const info = document.createElement('div');
      info.className = 'linha-info';
      info.innerHTML =
        `<div><strong>${v.rota.origem}</strong> → <strong>${v.rota.destino}</strong></div>` +
        `<div>Data: ${formatDateBr(v.data)} · Saída ${v.rota.hora_ida}</div>`;

      card.appendChild(header);
      card.appendChild(info);

      if (podeCancelar && v.status === 'reservada') {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'botao botao-invertido';
        btn.textContent = 'Cancelar reserva';
        btn.addEventListener('click', () => cancelarViagem(v.id));
        card.appendChild(btn);
      } else if (v.status === 'realizada' && !v.avaliada) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'botao botao-primario';
        btn.textContent = 'Avaliar';
        btn.addEventListener('click', () => abrirModalAvaliar(v));
        card.appendChild(btn);
      } else if (v.status === 'realizada' && v.avaliada) {
        const span = document.createElement('span');
        span.className = 'avaliada-marca';
        span.textContent = '✓ Já avaliada';
        card.appendChild(span);
      }

      container.appendChild(card);
    });
  }

  function abrirModalAvaliar(viagem) {
    const dialog = document.getElementById('modal-avaliar');
    if (!dialog || typeof dialog.showModal !== 'function') {
      const nota = parseInt(prompt('Nota de 1 a 5:'), 10);
      if (nota) enviarAvaliacao(viagem.id, nota, '');
      return;
    }

    const rotaEl = document.getElementById('modal-avaliar-rota');
    const comentarioEl = document.getElementById('modal-comentario');
    const erroEl = document.getElementById('modal-avaliar-erro');
    const btnCancelar = document.getElementById('modal-avaliar-cancelar');
    const btnConfirmar = document.getElementById('modal-avaliar-confirmar');
    const estrelas = dialog.querySelectorAll('.estrela');
    const form = document.getElementById('form-avaliar');

    if (rotaEl) {
      rotaEl.textContent = `${viagem.rota.nome} — ${viagem.rota.origem} → ${viagem.rota.destino}`;
    }
    if (comentarioEl) comentarioEl.value = '';
    if (erroEl) { erroEl.hidden = true; erroEl.textContent = ''; }

    let notaSelecionada = 0;
    function pintarEstrelas(n) {
      estrelas.forEach((e) => {
        const d = parseInt(e.dataset.nota, 10);
        e.classList.toggle('preenchida', d <= n);
        e.setAttribute('aria-checked', String(d === n));
      });
    }
    pintarEstrelas(0);
    btnConfirmar.disabled = true;

    estrelas.forEach((e) => {
      e.onclick = () => {
        notaSelecionada = parseInt(e.dataset.nota, 10);
        pintarEstrelas(notaSelecionada);
        btnConfirmar.disabled = false;
      };
    });

    if (btnCancelar) btnCancelar.onclick = () => dialog.close();

    form.onsubmit = async (ev) => {
      ev.preventDefault();
      if (!notaSelecionada) return;
      const ok = await enviarAvaliacao(
        viagem.id,
        notaSelecionada,
        comentarioEl ? comentarioEl.value : '',
        erroEl,
      );
      if (ok) dialog.close();
    };

    dialog.showModal();
  }

  async function enviarAvaliacao(viagemId, nota, comentario, erroEl) {
    try {
      await apiRequest(`/api/estudante/viagens/${viagemId}/avaliar`, {
        method: 'POST',
        body: { nota: nota, comentario: comentario || null },
      });
      alert('Avaliação enviada. Obrigado!');
      carregarPainelPassageiro();
      return true;
    } catch (err) {
      if (erroEl) {
        erroEl.textContent = err.message || 'Erro ao avaliar.';
        erroEl.hidden = false;
      } else {
        alert(err.message || 'Erro ao avaliar.');
      }
      return false;
    }
  }

  async function cancelarViagem(viagemId) {
    if (!confirm('Cancelar esta reserva?')) return;
    try {
      await apiRequest(`/api/estudante/viagens/${viagemId}`, { method: 'DELETE' });
      carregarPainelPassageiro();
    } catch (err) {
      alert(err.message || 'Erro ao cancelar.');
    }
  }

  ready(function () {
    const btnSairGlobal = document.getElementById('btn-sair');
    if (btnSairGlobal) btnSairGlobal.addEventListener('click', logout);

    initCadastroUsuario();
    initLogin();
    initRotas();
    initPainel();
    initHomeRotas();
    initHeroPreviewLive();
    initHeaderPainelUsuario();
  });
})();
