
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

  // Mapa de campos -> elemento input (usado para aria-invalid)
  const inputsPorCampo = {
    nome: inputNome,
    origem: inputOrigem,
    destino: inputDestino,
    partida: inputPartida,
    vagas: inputVagas,
    preco: inputPrecoVis,
    veiculo: selectVeiculo,
    imagem: inputImagem,
  };

  function err(field, msg) {
    const el = form.querySelector('[data-err-for="' + field + '"]');
    if (el) el.textContent = msg || '';
    const input = inputsPorCampo[field];
    if (input) {
      if (msg) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
    }
  }

  function limparErros() {
    ['nome', 'origem', 'destino', 'partida', 'vagas', 'preco', 'veiculo', 'dias', 'imagem']
      .forEach((f) => err(f, ''));
  }

  function validaImagem() {
    if (!inputImagem || !inputImagem.files || !inputImagem.files[0]) return true;
    const f = inputImagem.files[0];
    if (f.size > 5 * 1024 * 1024) {
      err('imagem', 'Imagem muito grande. Máximo 5 MB.');
      return false;
    }
    return true;
  }

  // Validação completa antes de enviar
  function validarFormulario() {
    limparErros();
    let ok = true;
    let primeiroInvalido = null;

    function invalida(campo, msg) {
      err(campo, msg);
      if (!primeiroInvalido && inputsPorCampo[campo]) {
        primeiroInvalido = inputsPorCampo[campo];
      }
      ok = false;
    }

    const nome = inputNome ? inputNome.value.trim() : '';
    if (nome.length < 2) invalida('nome', 'Informe um nome com pelo menos 2 caracteres.');
    else if (nome.length > 120) invalida('nome', 'Nome muito longo (máx 120 caracteres).');

    const origem = inputOrigem ? inputOrigem.value.trim() : '';
    if (origem.length < 2) invalida('origem', 'Informe a origem.');
    else if (origem.length > 120) invalida('origem', 'Origem muito longa (máx 120 caracteres).');

    const destino = inputDestino ? inputDestino.value.trim() : '';
    if (destino.length < 2) invalida('destino', 'Informe o destino.');
    else if (destino.length > 120) invalida('destino', 'Destino muito longo (máx 120 caracteres).');

    const horaIda = inputPartida ? inputPartida.value : '';
    if (!/^\d{2}:\d{2}$/.test(horaIda)) invalida('partida', 'Informe a hora de partida.');

    const vagasVal = inputVagas ? Number(inputVagas.value) : 0;
    if (!Number.isInteger(vagasVal) || vagasVal < 1 || vagasVal > 99) {
      invalida('vagas', 'Vagas deve ser um número entre 1 e 99.');
    }

    const veiculoVal = selectVeiculo ? selectVeiculo.value : '';
    if (!veiculoVal) invalida('veiculo', 'Selecione um tipo de veículo.');

    const precoTexto = (inputPrecoVis && inputPrecoVis.value) || '';
    const precoVal = parseBRLToNumber(precoTexto);
    if (precoVal <= 0) invalida('preco', 'Informe o preço por assento.');
    else if (precoVal > 10000) invalida('preco', 'Preço fora da faixa permitida.');

    const diasSelecionados = form.querySelectorAll('input[name="dias"]:checked');
    if (diasSelecionados.length === 0) {
      invalida('dias', 'Selecione pelo menos um dia da semana.');
    }

    if (!validaImagem()) {
      if (!primeiroInvalido) primeiroInvalido = inputImagem;
      ok = false;
    }

    if (!ok && primeiroInvalido) primeiroInvalido.focus();
    return ok;
  }

  // Real-time: limpa o erro do campo assim que o usuário corrige
  function ligarLimpezaErro(input, campo) {
    if (!input) return;
    const ev = input.type === 'checkbox' || input.tagName === 'SELECT' ? 'change' : 'input';
    input.addEventListener(ev, () => err(campo, ''));
  }

  ligarLimpezaErro(inputNome, 'nome');
  ligarLimpezaErro(inputOrigem, 'origem');
  ligarLimpezaErro(inputDestino, 'destino');
  ligarLimpezaErro(inputPartida, 'partida');
  ligarLimpezaErro(inputVagas, 'vagas');
  ligarLimpezaErro(inputPrecoVis, 'preco');
  ligarLimpezaErro(selectVeiculo, 'veiculo');
  ligarLimpezaErro(inputImagem, 'imagem');

  // Limpa erro de "dias" quando qualquer checkbox muda
  form.querySelectorAll('input[name="dias"]').forEach((chk) => {
    chk.addEventListener('change', () => err('dias', ''));
  });

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

  const btnSubmitRota = form.querySelector('button[type="submit"]');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    if (!validarFormulario()) return;

    const nome = inputNome.value.trim();
    const origem = inputOrigem.value.trim();
    const destino = inputDestino.value.trim();
    const horaIda = inputPartida.value;
    const horaVolta = inputRetorno ? inputRetorno.value : '';
    const vagas = Number(inputVagas.value);
    const veiculo = selectVeiculo.value;

    const valor = parseBRLToNumber(inputPrecoVis.value);
    if (inputPreco) inputPreco.value = String(valor);

    const dias = Array.from(
      form.querySelectorAll('input[name="dias"]:checked')
    ).map(i => i.value);

    const parseNumOrNull = (id) => {
      const el = document.getElementById(id);
      const v = el && el.value ? parseFloat(el.value) : NaN;
      return Number.isFinite(v) ? v : null;
    };

    const rota = {
      nome,
      origem,
      destino,
      origem_lat: parseNumOrNull('origem_lat'),
      origem_lng: parseNumOrNull('origem_lng'),
      destino_lat: parseNumOrNull('destino_lat'),
      destino_lng: parseNumOrNull('destino_lng'),
      hora_ida: horaIda,
      hora_volta: horaVolta || null,
      vagas,
      veiculo,
      dias_semana: dias,
      preco: valor > 0 ? valor : 0
    };

    if (btnSubmitRota) btnSubmitRota.disabled = true;
    try {
      const url = rotaEmEdicaoId
        ? '/api/motorista/rotas/' + rotaEmEdicaoId
        : '/api/motorista/rotas';

      const method = rotaEmEdicaoId ? 'PUT' : 'POST';

      await apiRequest(url, { method, body: rota });
      window.location.href = 'painel.html';
    } catch (err) {
      alert('Erro ao salvar rota: ' + (err.message || ''));
    } finally {
      if (btnSubmitRota) btnSubmitRota.disabled = false;
    }
  });
});
