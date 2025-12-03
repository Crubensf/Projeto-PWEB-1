// frontend/js/app.js
(function () {
  const API_BASE = 'http://127.0.0.1:8000';

  // ===================== HELPERS GERAIS =====================

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  async function apiRequest(
    path,
    { method = 'GET', body = null, auth = false, isForm = false } = {}
  ) {
    const url = `${API_BASE}${path}`;
    const options = { method, headers: {} };

    if (auth) {
      const token = localStorage.getItem('token');
      if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
      }
    }

    if (body) {
      if (isForm) {
        options.body = body; // FormData
      } else {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
      }
    }

    const resp = await fetch(url, options);
    let data = null;

    try {
      data = await resp.json();
    } catch {
      // resposta sem JSON
    }

    if (!resp.ok) {
      const msg =
        (data && (data.detail || data.message)) ||
        `Erro HTTP ${resp.status}`;
      throw new Error(msg);
    }

    return data;
  }

  function saveAuth(token, usuario) {
    if (token) localStorage.setItem('token', token);
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

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
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

  // ===================== HEADER: BOTÃO PAINEL USUÁRIO =====================

  function initHeaderPainelUsuario() {
    const btnPainel = document.getElementById('btn-painel-usuario');
    if (!btnPainel) return; // não está nessa página

    const user = getUsuario();

    if (user) {
      // usuário logado → mostra botão
      btnPainel.style.display = 'inline-flex';

      if (user.perfil === 'motorista') {
        btnPainel.textContent = 'Painel do motorista';
      } else {
        btnPainel.textContent = 'Meu painel';
      }
    } else {
      // ninguém logado → esconde
      btnPainel.style.display = 'none';
    }
  }

  // ===================== HOME: ROTAS EM DESTAQUE =====================

  function criarCardRotaDestaque(rota) {
    const article = document.createElement('article');
    article.className = 'cartao rota';

    const titulo = document.createElement('h3');
    titulo.textContent = `${rota.origem} → ${rota.destino}`;

    const lista = document.createElement('ul');
    lista.className = 'lista-chip';

    const chipIda = document.createElement('li');
    chipIda.className = 'chip';
    chipIda.textContent = rota.hora_ida ? `saída ${rota.hora_ida}` : 'horário a combinar';

    const chipVolta = document.createElement('li');
    chipVolta.className = 'chip';
    chipVolta.textContent = rota.hora_volta ? `chegada ${rota.hora_volta}` : 'sem volta';

    lista.appendChild(chipIda);
    lista.appendChild(chipVolta);

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
    if (!container) return; // não está na index

    container.innerHTML = '<p>Carregando rotas...</p>';

    try {
      const rotas = await apiRequest('/api/rotas');

      container.innerHTML = '';

      if (!rotas || !rotas.length) {
        container.innerHTML = '<p>Não há rotas cadastradas ainda.</p>';
        return;
      }

      const destaque = rotas.slice(0, 3);
      destaque.forEach((rota) => {
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

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (senha && confirmar && senha.value !== confirmar.value) {
        if (msgConfirm) msgConfirm.textContent = 'As senhas não coincidem.';
        confirmar.focus();
        return;
      }

      if (perfil && perfil.value === 'motorista' && cnh) {
        const wrap = cnh.parentElement;
        const m = wrap ? wrap.querySelector('.msg-erro') : null;

        if (!/^\d{11}$/.test(cnh.value)) {
          if (m)
            m.textContent =
              'Informe os 11 dígitos da CNH (somente números).';
          cnh.focus();
          return;
        } else if (m) {
          m.textContent = '';
        }
      }

      const formData = new FormData(form);

      // padrão: estudante se não escolher
      if (!formData.get('perfil')) {
        formData.set('perfil', 'estudante');
      }

      try {
        const data = await apiRequest('/api/auth/register', {
          method: 'POST',
          body: formData,
          isForm: true,
        });

        saveAuth(data.access_token, data.usuario);
        alert('Cadastro concluído!');
        location.assign('painel.html');
      } catch (err) {
        console.error(err);
        alert('Erro ao cadastrar: ' + err.message);
      }
    });
  }

  // ===================== LOGIN =====================

  function initLogin() {
    const form = document.querySelector(
      'form.login-form, form.form-login, form#form-login'
    );
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const d = new FormData(form);
      const email = d.get('email') || '';
      const senha = d.get('senha') || '';

      try {
        const data = await apiRequest('/api/auth/login', {
          method: 'POST',
          body: { email, senha },
        });

        saveAuth(data.access_token, data.usuario);
        alert('Login realizado com sucesso!');
        location.assign('painel.html');
      } catch (err) {
        console.error(err);
        alert('Erro ao fazer login: ' + err.message);
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

    function renderRotasLista(rotas, diaLabel) {
      limparCards();

      if (!rotas || !rotas.length) {
        if (msgSem) msgSem.hidden = false;
        return;
      }

      if (msgSem) msgSem.hidden = true;

      rotas.forEach((r) => {
        const artigo = document.createElement('article');
        artigo.className = 'linha-card';

        const header = document.createElement('header');
        header.className = 'linha-topo';

        const h2 = document.createElement('h2');
        h2.className = 'nome-motorista';
        h2.textContent = r.nome || 'Rota';

        const link = document.createElement('a');
        link.className = 'botao botao-suave';
        link.href = '#';
        link.textContent = 'Saiba mais';

        header.appendChild(h2);
        header.appendChild(link);

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

        const hSaida = document.createElement('div');
        hSaida.className = 'horario';
        hSaida.innerHTML =
          '<span class="rotulo">Saída</span><strong class="hora">' +
          (r.hora_ida || '-') +
          '</strong>';

        const hChegada = document.createElement('div');
        hChegada.className = 'horario';
        hChegada.innerHTML =
          '<span class="rotulo">Chegada</span><strong class="hora">' +
          (r.hora_volta || '-') +
          '</strong>';

        horarios.appendChild(hSaida);
        horarios.appendChild(hChegada);

        info.appendChild(origDest);
        info.appendChild(horarios);

        artigo.appendChild(header);
        artigo.appendChild(info);

        container.insertBefore(
          artigo,
          msgSem || null
        );
      });

      if (tituloLista) {
        tituloLista.textContent = `Rotas disponíveis${
          diaLabel ? ` — ${diaLabel}` : ''
        }`;
      }
    }

    async function carregarRotas() {
      try {
        const params = new URLSearchParams();

        if (inputOrigem && inputOrigem.value) params.append('origem', inputOrigem.value);
        if (inputDestino && inputDestino.value) params.append('destino', inputDestino.value);

        let diaLabel = '';
        const chipAtivo = document.querySelector('.chip-dia.ativo');
        if (chipAtivo) {
          diaLabel = chipAtivo.textContent.trim();
          const diaKey = mapDiaLabelToKey(diaLabel);
          if (diaKey) params.append('dia', diaKey);
        }

        const qs = params.toString();
        const rotas = await apiRequest(`/api/rotas${qs ? `?${qs}` : ''}`);
        renderRotasLista(rotas, diaLabel);
      } catch (err) {
        console.error(err);
        alert('Erro ao carregar rotas: ' + err.message);
      }
    }

    if (inputOrigem) {
      inputOrigem.addEventListener('input', () => {
        carregarRotas();
      });
    }

    if (inputDestino) {
      inputDestino.addEventListener('input', () => {
        carregarRotas();
      });
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

    carregarRotas();
  }

  // ===================== PAINEL =====================

  function renderViagensLista(viagens, container, msgVaziaEl) {
    if (!container) return;
    container.innerHTML = '';

    if (!viagens || !viagens.length) {
      if (msgVaziaEl) msgVaziaEl.style.display = 'block';
      return;
    }

    if (msgVaziaEl) msgVaziaEl.style.display = 'none';

    viagens.forEach((v) => {
      const rota = v.rota || {};
      const item = document.createElement('div');
      item.className = 'item-card';

      const info = document.createElement('div');
      info.className = 'info';

      const strong = document.createElement('strong');
      strong.textContent = `${rota.origem || ''} → ${rota.destino || ''}`;

      const smallData = document.createElement('small');
      smallData.textContent = `${formatDateBr(v.data)} às ${
        rota.hora_ida || '--:--'
      }`;

      info.appendChild(strong);
      info.appendChild(smallData);

      const statusDiv = document.createElement('div');
      const statusSpan = document.createElement('div');
      const status = (v.status || '').toLowerCase();

      let classeStatus = 'status';
      if (status === 'reservada') classeStatus += ' ativo';
      if (status === 'concluida') classeStatus += ' concluida';

      statusSpan.className = classeStatus;
      statusSpan.textContent =
        status === 'reservada'
          ? 'Ativa'
          : status === 'concluida'
          ? 'Concluída'
          : v.status || '';

      statusDiv.appendChild(statusSpan);

      item.appendChild(info);
      item.appendChild(statusDiv);

      container.appendChild(item);
    });
  }

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
      smallDiasHora.textContent = `${dias || ''} • ${r.hora_ida || ''}`;

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

      const btnExcluir = document.createElement('button');
      btnExcluir.type = 'button';
      btnExcluir.className = 'botao botao-suave btn-excluir-rota';
      btnExcluir.textContent = 'Excluir rota';

      info2.appendChild(spanStatus);
      info2.appendChild(btnExcluir);

      item.appendChild(info);
      item.appendChild(info2);

      container.appendChild(item);
    });
  }

  async function carregarPainelEstudante() {
    const listaProximas = document.getElementById('lista-proximas-viagens');
    const msgSemProximas = document.getElementById('msg-sem-proximas');

    const listaHist = document.getElementById('lista-historico-viagens');
    const msgSemHist = document.getElementById('msg-sem-historico');

    try {
      const proximas = await apiRequest(
        '/api/passageiro/viagens/proximas',
        { auth: true }
      );
      renderViagensLista(proximas, listaProximas, msgSemProximas);
    } catch (err) {
      console.error(err);
    }

    try {
      const historico = await apiRequest(
        '/api/passageiro/viagens/historico',
        { auth: true }
      );
      renderViagensLista(historico, listaHist, msgSemHist);
    } catch (err) {
      console.error(err);
    }
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

    try {
      const resumo = await apiRequest('/api/motorista/resumo', {
        auth: true,
      });
      if (spanRotasAtivas) spanRotasAtivas.textContent = resumo.rotas_ativas;
      if (spanViagensHoje)
        spanViagensHoje.textContent = resumo.viagens_hoje;
      if (spanAlunosHoje)
        spanAlunosHoje.textContent = resumo.alunos_hoje;
    } catch (err) {
      console.error(err);
    }

    try {
      const rotas = await apiRequest('/api/motorista/minhas-rotas', {
        auth: true,
      });
      renderRotasMotorista(rotas, listaRotas, msgSemRotas);
    } catch (err) {
      console.error(err);
    }

    if (listaRotas) {
      listaRotas.addEventListener('click', async function (e) {
        const target = e.target;
        const btn = target.closest
          ? target.closest('.btn-excluir-rota')
          : null;
        if (!btn) return;

        const item = btn.closest('.item-card');
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
            auth: true,
          });
          item.remove();
          if (spanRotasAtivas) {
            const atual = parseInt(spanRotasAtivas.textContent || '0', 10);
            if (!Number.isNaN(atual) && atual > 0) {
              spanRotasAtivas.textContent = String(atual - 1);
            }
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
            `/api/motorista/viagens?data=${dataSel}`,
            { auth: true }
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
    const blocoPassageiro = document.getElementById('bloco-passageiro');
    const blocoMotorista = document.getElementById('bloco-motorista');
    const btnSair = document.getElementById('btn-sair');

    if (nomeSpan) {
      const primeiroNome = (user.nome || '').split(' ')[0] || 'Usuário';
      nomeSpan.textContent = primeiroNome;
    }

    if (btnSair) {
      btnSair.addEventListener('click', logout);
    }

    if (user.perfil === 'estudante') {
      if (textoTipo)
        textoTipo.textContent =
          'Aqui você vê suas passagens ativas e o histórico de viagens.';
      if (blocoPassageiro) blocoPassageiro.style.display = 'block';
      if (blocoMotorista) blocoMotorista.style.display = 'none';

      carregarPainelEstudante();
    } else if (user.perfil === 'motorista') {
      if (textoTipo)
        textoTipo.textContent =
          'Aqui você vê as rotas que cadastrou e quantas reservas cada uma possui.';
      if (blocoPassageiro) blocoPassageiro.style.display = 'none';
      if (blocoMotorista) blocoMotorista.style.display = 'block';

      carregarPainelMotorista();
    }
  }

  // ===================== INIT GLOBAL =====================

  ready(function () {
    const btnSairGlobal = document.getElementById('btn-sair');
    if (btnSairGlobal) btnSairGlobal.addEventListener('click', logout);

    initCadastroUsuario();
    initLogin();
    initRotas();
    initPainel();
    initHomeRotas();
    initHeaderPainelUsuario(); // ativa o botão do painel na home
  });
})();
