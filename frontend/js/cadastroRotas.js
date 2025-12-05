const API_BASE = 'http://127.0.0.1:8000';

async function apiRequest(path, { method = 'GET', body = null } = {}) {
  const url = `${API_BASE}${path}`;
  const options = { method, headers: {}, credentials: 'include' };

  if (body) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  const resp = await fetch(url, options);
  let data = null;

  try { data = await resp.json(); } catch {}

  if (!resp.ok) {
    const msg = (data && (data.detail || data.message)) || `Erro HTTP ${resp.status}`;
    throw new Error(msg);
  }

  return data;
}

function getUsuario() {
  try {
    const raw = localStorage.getItem('usuario');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('form-rota');
  if (!form) return;

  const user = getUsuario();
  if (!user || user.perfil !== 'motorista') {
    alert('Você precisa estar logado como motorista para acessar esta página.');
    location.href = 'login.html';
    return;
  }

  let rotaEmEdicaoId = null;

  const tituloPagina = document.getElementById('titulo-rotas');
  const subtituloPagina = document.querySelector('.rotas-sub');

  const inputNome = document.getElementById('nome');
  const inputOrigem = document.getElementById('origem');
  const inputDestino = document.getElementById('destino');
  const inputPartida = document.getElementById('partida');
  const inputRetorno = document.getElementById('retorno');
  const inputVagas = document.getElementById('vagas');
  const selectVeiculo = document.getElementById('veiculo');
  const inputPrecoVis = document.getElementById('preco_vis');
  const inputPreco = document.getElementById('preco');
  const inputImagem = document.getElementById('imagem');

  const fmt = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });

  function parseBRLToNumber(text) {
    if (!text) return 0;
    const only = text.replace(/[^\d,.-]/g, '').replace(/\./g, '').replace(',', '.');
    const n = parseFloat(only);
    return Number.isNaN(n) ? 0 : n;
  }

  function formatPrecoOnInput() {
    if (!inputPrecoVis) return;
    let val = inputPrecoVis.value.replace(/[^\d]/g, '');
    if (!val) {
      inputPrecoVis.value = '';
      if (inputPreco) inputPreco.value = '';
      return;
    }
    const num = parseInt(val, 10) / 100;
    inputPrecoVis.value = fmt.format(num);
    if (inputPreco) inputPreco.value = String(num);
  }

  if (inputPrecoVis) {
    inputPrecoVis.addEventListener('input', formatPrecoOnInput);
    inputPrecoVis.addEventListener('blur', () => {
      if (inputPrecoVis.value) formatPrecoOnInput();
    });
  }

  function err(field, msg) {
    const el = form.querySelector('[data-err-for="' + field + '"]');
    if (el) el.textContent = msg || '';
  }

  function validaImagem() {
    if (!inputImagem || !inputImagem.files || !inputImagem.files[0]) return true;
    const f = inputImagem.files[0];
    if (f.size > 5 * 1024 * 1024) {
      alert('Imagem muito grande.');
      return false;
    }
    return true;
  }

  const listaParadas = document.getElementById('listaParadas');
  const addParadaBtn = document.getElementById('addParada');

  function criaLinhaParada(nome, hora) {
    const wrap = document.createElement('div');
    wrap.className = 'parada-item';
    wrap.innerHTML =
      '<input type="text" name="paradas[][nome]" value="' + (nome || '') + '">' +
      '<input type="time" name="paradas[][hora]" value="' + (hora || '') + '">' +
      '<button type="button" class="btn btn-danger">Remover</button>';
    wrap.querySelector('button').addEventListener('click', () => wrap.remove());
    return wrap;
  }

  if (listaParadas && addParadaBtn) {
    addParadaBtn.addEventListener('click', () => {
      listaParadas.appendChild(criaLinhaParada());
    });
    listaParadas.appendChild(criaLinhaParada('Ponto de encontro', '06:50'));
  }

  async function carregarRotaParaEdicao(rotaId) {
    try {
      const rota = await apiRequest(`/api/motorista/rotas/${rotaId}`);

      rotaEmEdicaoId = rotaId;

      if (tituloPagina) tituloPagina.textContent = 'Editar rota';
      if (subtituloPagina) subtituloPagina.textContent = 'Atualize as informações da rota.';

      if (inputNome) inputNome.value = rota.nome || '';
      if (inputOrigem) inputOrigem.value = rota.origem || '';
      if (inputDestino) inputDestino.value = rota.destino || '';
      if (inputPartida) inputPartida.value = rota.hora_ida || '';
      if (inputRetorno) inputRetorno.value = rota.hora_volta || '';
      if (inputVagas) inputVagas.value = rota.vagas != null ? rota.vagas : '';
      if (selectVeiculo) selectVeiculo.value = rota.veiculo || '';

      const diasArray = Array.isArray(rota.dias_semana)
        ? rota.dias_semana
        : String(rota.dias_semana || '').split(',');

      form.querySelectorAll('input[name="dias"]').forEach(chk => {
        chk.checked = diasArray.includes(chk.value);
      });

      if (typeof rota.preco === 'number') {
        if (inputPreco) inputPreco.value = String(rota.preco);
        if (inputPrecoVis) inputPrecoVis.value = fmt.format(rota.preco);
      }

      const btnSubmit = form.querySelector('button[type="submit"]');
      if (btnSubmit) btnSubmit.textContent = 'Salvar alterações';
    } catch {
      alert('Erro ao carregar dados da rota.');
    }
  }

  const params = new URLSearchParams(window.location.search);
  const rotaIdParam = params.get('rotaId');
  if (rotaIdParam) {
    carregarRotaParaEdicao(rotaIdParam);
  } else {
    if (tituloPagina) tituloPagina.textContent = 'Cadastrar rota';
    if (subtituloPagina) subtituloPagina.textContent = 'Preencha os dados da sua rota.';
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    ['nome', 'origem', 'destino', 'partida', 'vagas', 'preco', 'dias'].forEach(f => err(f, ''));

    if (!validaImagem()) return;

    const nome = inputNome ? inputNome.value.trim() : '';
    const origem = inputOrigem ? inputOrigem.value.trim() : '';
    const destino = inputDestino ? inputDestino.value.trim() : '';
    const horaIda = inputPartida ? inputPartida.value : '';
    const horaVolta = inputRetorno ? inputRetorno.value : '';
    const vagas = inputVagas ? Number(inputVagas.value || 0) : 0;
    const veiculo = selectVeiculo ? selectVeiculo.value : '';

    let precoTexto = (inputPrecoVis && inputPrecoVis.value) || '';
    const valor = parseBRLToNumber(precoTexto);
    if (inputPreco) inputPreco.value = valor > 0 ? String(valor) : '0';

    const dias = Array.from(
      form.querySelectorAll('input[name="dias"]:checked')
    ).map(i => i.value);

    const rota = {
      nome,
      origem,
      destino,
      hora_ida: horaIda,
      hora_volta: horaVolta || null,
      vagas,
      veiculo,
      dias_semana: dias,
      preco: valor > 0 ? valor : 0
    };

    try {
      const url = rotaEmEdicaoId
        ? '/api/motorista/rotas/' + rotaEmEdicaoId
        : '/api/motorista/rotas';

      const method = rotaEmEdicaoId ? 'PUT' : 'POST';

      await apiRequest(url, { method, body: rota });

      if (rotaEmEdicaoId) alert('Rota atualizada com sucesso!');
      else alert('Rota criada com sucesso!');

      window.location.href = 'painel.html';
    } catch (err) {
      alert('Erro ao salvar rota: ' + (err.message || ''));
    }
  });
});
