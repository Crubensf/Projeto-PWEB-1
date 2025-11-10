import { hydrateHeader } from './auth.js';
import { filtrarRotas } from './rotasService.js';
import { renderRotas, getDiaAtivo, setSemResultadosVisible, setTituloLista } from './ui.js';
(function(){
hydrateHeader();
const inputOrigem=document.getElementById('origem');
const inputDestino=document.getElementById('destino');
const lista=document.querySelector('.lista-resultados') || document.querySelector('.linhas');
const chips=document.querySelectorAll('.chip-dia');
const btnNovaBusca=document.getElementById('btnNovaBusca');

function atualizar(){
const dia=getDiaAtivo();
const rotas=filtrarRotas({ origem: inputOrigem?.value||'', destino: inputDestino?.value||'', dia });
if (lista) renderRotas(rotas, lista);
setSemResultadosVisible(rotas.length===0);
setTituloLista(`Rotas disponíveis${dia?` — ${dia}`:''}`);
}

inputOrigem?.addEventListener('input', atualizar);
inputDestino?.addEventListener('input', atualizar);
chips.forEach(ch=> ch.addEventListener('click', ()=> setTimeout(atualizar,0)));
btnNovaBusca?.addEventListener('click', ()=>{ atualizar(); document.querySelector('.resultados')?.scrollIntoView({behavior:'smooth'}); });
atualizar();
})();