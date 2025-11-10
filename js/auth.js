import { getUsuarioLogado, clearSessao } from './storage.js';
export function hydrateHeader(){
const user = getUsuarioLogado();
const headerSlot = document.querySelector('[data-auth-slot]') || document.querySelector('.acoes-header') || document.querySelector('nav .acoes');
if (!headerSlot) return;
if (user){
headerSlot.innerHTML = `<span class="saudacao">Olá, ${user.nome?.split(' ')[0]||'Usuário'}</span> <button type="button" id="btnSair" class="botao botao-invertido">Sair</button>`;
document.getElementById('btnSair')?.addEventListener('click', () => { clearSessao(); location.reload(); });
}
}