// frontend/js/cadastroRotas.js
const API_BASE = 'http://127.0.0.1:8000';

// ============ helpers básicos ============

async function apiRequest(path, { method = 'GET', body = null, auth = false } = {}) {
  const url = `${API_BASE}${path}`;
  const options = { method, headers: {} };

  if (auth) {
    const token = localStorage.getItem('token');
    console.log('[apiRequest] token atual:', token);
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }
  }

  if (body) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  console.log('[apiRequest] >>>', method, url, 'body:', body);

  let resp;
  try {
    resp = await fetch(url, options);
  } catch (networkErr) {
    console.error('[apiRequest] ERRO DE REDE / CORS:', networkErr);
    throw new Error('Falha de rede (backend fora do ar ou CORS).');
  }

  let data = null;

  try {
    data = await resp.json();
  } catch (parseErr) {
    console.warn('[apiRequest] resposta sem JSON ou JSON inválido');
  }

  console.log('[apiRequest] <<< status:', resp.status, 'data:', data);

  if (!resp.ok) {
    const msg =
      (data && (data.detail || data.message)) ||
      `Erro HTTP ${resp.status}`;
    throw new Error(msg);
  }

  return data;
}

function getUsuario() {
  try {
    const raw = localStorage.getItem('usuario');
    console.log('[getUsuario] raw localStorage.usuario =', raw);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// ============ cadastro de rotas ============

document.addEventListener('DOMContentLoaded', function () {
  console.log('[cadastroRotas] JS carregado');

  const form = document.getElementById('form-rota');
  if (!form) {
    console.log('[cadastroRotas] form-rota NÃO encontrado');
    return;
  }

  console.log('[cadastroRotas] form-rota encontrado, registrando submit');

  // --- NOVO: container da lista de rotas e mensagem
  const listaRotas = document.getElementById('lista-rotas-cadastro');
  const msgSemRotas = document.getElementById('msg-sem-rotas-cadastro');

  const precoVis = document.getElementById('preco_vis');
  const preco = document.getElementById('preco');
  const listaParadas = document.getElementById('listaParadas');
  const addParadaBtn = document.getElementById('addParada');
  const imagem = document.getElementById('imagem');

  const MAX_MB = 5;
  const MAX_BYTES = MAX_MB * 1024 * 1024;

  const fmt = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

  // exige que seja motorista para usar essa página
  const user = getUsuario();
  console.log('[cadastroRotas] usuario atual (carregando página):', user);
  if (!user || user.perfil !== 'motorista') {
    alert('Você precisa estar logado como motorista para acessar esta página.');
    location.href = 'login.html';
    return;
  }

  function parseBRLToNumber(text) {
    if (!text) return 0;

    const only = text
      .replace(/[^\d,.-]/g, '')
      .replace(/\./g, '')
      .replace(',', '.');

    const n = parseFloat(only);
    return Number.isNaN(n) ? 0 : n;
  }

  function formatPrecoOnInput() {
    if (!precoVis) return;
    let val = precoVis.value;
    val = val.replace(/[^\d]/g, '');

    if (!val) {
      precoVis.value = '';
      if (preco) preco.value = '';
      return;
    }

    const int = parseInt(val, 10);
    const num = int / 100;

    precoVis.value = fmt.format(num);
    if (preco) preco.value = String(num);
  }

  function err(field, msg) {
    const el = form.querySelector('[data-err-for="' + field + '"]');
    if (el) el.textContent = msg || '';
  }

  function validaImagem() {
    if (!imagem || !imagem.files || !imagem.files[0]) return true;
    const f = imagem.files[0];

    if (f.size > MAX_BYTES) {
      alert('Imagem muito grande. Máx: ' + MAX_MB + ' MB.');
      return false;
    }

    return true;
  }

  function criaLinhaParada(nome, hora) {
    if (nome === void 0) nome = '';
    if (hora === void 0) hora = '';
    const wrap = document.createElement('div');
    wrap.className = 'parada-item';

    wrap.innerHTML =
      '<input type="text" name="paradas[][nome]" placeholder="Ex.: Terminal Centro" value="' +
      nome +
      '">' +
      '<input type="time" name="paradas[][hora]" value="' +
      hora +
      '">' +
      '<button type="button" class="btn btn-danger">Remover</button>';

    const btnRemover = wrap.querySelector('button');
    btnRemover.addEventListener('click', function () {
      wrap.remove();
    });

    return wrap;
  }

  // -------- NOVO: renderizar e carregar "minhas rotas" --------

  function renderMinhasRotas(rotas) {
    if (!listaRotas) return;

    listaRotas.innerHTML = '';

    if (!rotas || !rotas.length) {
      if (msgSemRotas) {
        msgSemRotas.textContent = 'Você ainda não cadastrou nenhuma rota.';
        msgSemRotas.style.display = 'block';
      }
      return;
    }

    if (msgSemRotas) {
      msgSemRotas.style.display = 'none';
    }

    rotas.forEach((r) => {
      const item = document.createElement('div');
      item.className = 'item-card rota-cadastrada';

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
      spanStatus.textContent = 'Ativa';

      const btnExcluir = document.createElement('button');
      btnExcluir.type = 'button';
      btnExcluir.className = 'botao botao-suave btn-excluir-rota';
      btnExcluir.textContent = 'Excluir rota';

      info2.appendChild(spanStatus);
      info2.appendChild(btnExcluir);

      item.appendChild(info);
      item.appendChild(info2);

      listaRotas.appendChild(item);
    });
  }

  async function carregarMinhasRotas() {
    if (!listaRotas) return;
    try {
      const rotas = await apiRequest('/api/motorista/minhas-rotas', {
        auth: true,
      });
      console.log('[cadastroRotas] minhas rotas:', rotas);
      renderMinhasRotas(rotas);
    } catch (err) {
      console.error('[cadastroRotas] erro ao carregar minhas rotas:', err);
      if (msgSemRotas) {
        msgSemRotas.textContent = 'Erro ao carregar suas rotas.';
        msgSemRotas.style.display = 'block';
      }
    }
  }

  // clique em "Excluir rota" dentro da lista
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

        if (!listaRotas.children.length && msgSemRotas) {
          msgSemRotas.textContent = 'Você ainda não cadastrou nenhuma rota.';
          msgSemRotas.style.display = 'block';
        }
      } catch (err) {
        console.error('[cadastroRotas] ERRO AO EXCLUIR ROTA:', err);
        alert('Erro ao excluir rota: ' + (err.message || ''));
      }
    });
  }

  // -------- fim da parte nova --------

  if (precoVis) {
    precoVis.addEventListener('input', formatPrecoOnInput);
    precoVis.addEventListener('blur', function () {
      if (precoVis.value) formatPrecoOnInput();
    });
  }

  if (addParadaBtn && listaParadas) {
    addParadaBtn.addEventListener('click', function () {
      listaParadas.appendChild(criaLinhaParada());
    });

    // parada padrão
    listaParadas.appendChild(
      criaLinhaParada('Ponto de encontro', '06:50')
    );
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    console.log('[cadastroRotas] SUBMIT disparado');

    const user = getUsuario();
    console.log('[cadastroRotas] usuario atual (submit):', user);

    if (!user || user.perfil !== 'motorista') {
      alert('Você precisa estar logado como motorista para cadastrar rotas.');
      location.href = 'login.html';
      return;
    }

    // limpa mensagens anteriores
    ['nome', 'origem', 'destino', 'partida', 'vagas', 'preco', 'dias'].forEach(
      function (f) {
        err(f, '');
      }
    );

    // loga os valores crus do formulário
    console.log('[cadastroRotas] valores do form:', {
      nome: form.nome.value,
      origem: form.origem.value,
      destino: form.destino.value,
      partida: form.partida.value,
      retorno: form.retorno.value,
      vagas: form.vagas.value,
      veiculo: form.veiculo.value,
      precoVis: precoVis ? precoVis.value : null,
      precoHidden: preco ? preco.value : null,
      diasMarcados: Array.from(
        form.querySelectorAll('input[name="dias"]:checked')
      ).map((i) => i.value),
    });

    // ---- mensagens de erro (AVISA, mas não bloqueia envio) ----
    if (!form.nome.value.trim()) {
      console.log('[cadastroRotas] aviso: nome vazio');
      err('nome', 'Informe o nome da rota.');
    }
    if (!form.origem.value.trim()) {
      console.log('[cadastroRotas] aviso: origem vazia');
      err('origem', 'Informe a origem.');
    }
    if (!form.destino.value.trim()) {
      console.log('[cadastroRotas] aviso: destino vazio');
      err('destino', 'Informe o destino.');
    }
    if (!form.partida.value) {
      console.log('[cadastroRotas] aviso: partida vazia');
      err('partida', 'Informe a hora de partida.');
    }
    if (!form.vagas.value || Number(form.vagas.value) <= 0) {
      console.log('[cadastroRotas] aviso: vagas inválidas:', form.vagas.value);
      err('vagas', 'Informe as vagas.');
    }

    let precoTexto =
      (precoVis && precoVis.value) ||
      (preco && preco.value) ||
      '';

    console.log('[cadastroRotas] precoTexto:', precoTexto);

    const valor = parseBRLToNumber(precoTexto);
    console.log('[cadastroRotas] valor numérico do preço:', valor);

    if (valor <= 0) {
      console.log('[cadastroRotas] aviso: preço inválido (<= 0)');
      err('preco', 'Informe um preço válido.');
    } else if (preco) {
      preco.value = String(valor);
    }

    const dias = Array.from(
      form.querySelectorAll('input[name="dias"]:checked')
    ).map(function (i) {
      return i.value;
    });

    if (dias.length === 0) {
      console.log('[cadastroRotas] aviso: nenhum dia marcado');
      err('dias', 'Selecione ao menos um dia.');
    }

    // valida imagem (essa sim bloqueia se for muito grande)
    if (!validaImagem()) {
      console.log('[cadastroRotas] imagem inválida, não vou chamar API');
      return;
    }

    // monta o payload independente dos avisos acima
    const d = new FormData(form);

    const rota = {
      nome: d.get('nome') || '',
      origem: d.get('origem') || '',
      destino: d.get('destino') || '',
      hora_ida: d.get('partida') || '',
      hora_volta: d.get('retorno') || null,
      vagas: Number(d.get('vagas') || 0),
      veiculo: d.get('veiculo') || '',
      dias_semana: dias,
      preco: valor > 0 ? valor : 0,
    };

    console.log('[cadastroRotas] payload rota pronto pra enviar:', rota);

    try {
      const resposta = await apiRequest('/api/motorista/rotas', {
        method: 'POST',
        body: rota,
        auth: true,
      });

      console.log('[cadastroRotas] resposta da API ao criar rota:', resposta);

      const rotaId =
        (resposta && (resposta.id || resposta.rota_id || resposta._id)) || null;

      alert(
        'Rota salva com sucesso!' +
          (rotaId ? ' (id: ' + rotaId + ')' : '')
      );

      try {
        form.reset();
        if (precoVis) precoVis.value = '';
        if (preco) preco.value = '';
      } catch (e) {}

      // depois de cadastrar, recarrega a lista
      await carregarMinhasRotas();
    } catch (err) {
      console.error('[cadastroRotas] ERRO AO SALVAR ROTA:', err);
      alert('Erro ao salvar rota: ' + (err.message || ''));
    }
  });

  // carrega as rotas do motorista ao abrir a página
  carregarMinhasRotas();
});
