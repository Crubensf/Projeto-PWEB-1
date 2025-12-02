function hydrateHeader(){
  const user = (typeof getUsuarioLogado === 'function') ? getUsuarioLogado() : null;
  const headerSlot = document.querySelector('[data-auth-slot]') || document.querySelector('.acoes-header') || document.querySelector('nav .acoes');
  if (!headerSlot) return;
  if (user){
    const primeiroNome = (user.nome || '').split(' ')[0] || 'Usuário';
    headerSlot.innerHTML = '<span class="saudacao">Olá, ' + primeiroNome + '</span> <button type="button" id="btnSair" class="botao botao-invertido">Sair</button>';
    const btn = document.getElementById('btnSair');
    if (btn) btn.addEventListener('click', function(){ if (typeof clearSessao === 'function') clearSessao(); location.reload(); });
  }
}
window.hydrateHeader = hydrateHeader;
