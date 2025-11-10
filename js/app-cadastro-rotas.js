import { hydrateHeader } from './auth.js';
import { saveRota } from './storage.js';
(function(){
hydrateHeader();
const form=document.getElementById('cadastroRotas'); if(!form) return;
const precoVis=document.getElementById('preco_vis');
const preco=document.getElementById('preco');
const listaParadas=document.getElementById('listaParadas');
const addParadaBtn=document.getElementById('addParada');
const imagem=document.getElementById('imagem');
const MAX_MB=5, MAX_BYTES=MAX_MB*1024*1024; const fmt=new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
function parseBRLToNumber(text){ if(!text) return 0; const only=text.replace(/[^\d,.-]/g,'').replace(/\./g,'').replace(',', '.'); const n=parseFloat(only); return isNaN(n)?0:n; }
function formatPrecoOnInput(){ let val=precoVis.value; val=val.replace(/[^\d]/g,''); if(!val){ precoVis.value=''; preco.value=''; return;} const int=parseInt(val,10); const num=int/100; precoVis.value=fmt.format(num); preco.value=String(num); }
function err(field,msg){ const el=form.querySelector(`[data-err-for="${field}"]`); if(el) el.textContent=msg||''; }
function validaDias(){ const marcados=form.querySelectorAll('input[name="dias[]"]:checked'); if(marcados.length===0){ err('dias','Selecione ao menos um dia.'); return false;} err('dias',''); return true; }
function validaImagem(){ const f=imagem?.files && imagem.files[0]; if(!f) return true; if(f.size>MAX_BYTES){ alert(`Imagem muito grande. Máx: ${MAX_MB} MB.`); return false;} return true; }
function criaLinhaParada(nome='',hora=''){ const wrap=document.createElement('div'); wrap.className='parada-item'; wrap.innerHTML=`<input type="text" name="paradas[][nome]" placeholder="Ex.: Terminal Centro" value="${nome}"><input type="time" name="paradas[][hora]" value="${hora}"><button type="button" class="btn btn-danger">Remover</button>`; wrap.querySelector('button').addEventListener('click',()=>wrap.remove()); return wrap; }
precoVis?.addEventListener('input', formatPrecoOnInput);
precoVis?.addEventListener('blur', ()=>{ if(precoVis.value) formatPrecoOnInput(); });
addParadaBtn?.addEventListener('click', ()=>{ listaParadas?.appendChild(criaLinhaParada()); });
listaParadas?.appendChild(criaLinhaParada('Ponto de encontro','06:50'));
form.addEventListener('submit',(e)=>{
let ok=true; err('nome',''); err('origem',''); err('destino',''); err('partida',''); err('vagas',''); err('preco','');
if(!form.nome.value.trim()){ err('nome','Informe o nome da rota.'); ok=false; }
if(!form.origem.value.trim()){ err('origem','Informe a origem.'); ok=false; }
if(!form.destino.value.trim()){ err('destino','Informe o destino.'); ok=false; }
if(!form.partida.value){ err('partida','Informe a hora de partida.'); ok=false; }
if(!form.vagas.value || Number(form.vagas.value)<=0){ err('vagas','Informe as vagas.'); ok=false; }
const valor=parseBRLToNumber(precoVis.value); if(valor<=0){ err('preco','Informe um preço válido.'); ok=false; } else { preco.value=String(valor); }
if(!validaDias()) ok=false; if(!validaImagem()) ok=false; if(!ok){ e.preventDefault(); return; }
const d=new FormData(form);
const dias=Array.from(form.querySelectorAll('input[name="dias[]"]:checked')).map(i=>i.value);
const paradas=Array.from(document.querySelectorAll('#listaParadas .parada-item input[type="text"]')).map(i=>i.value).filter(Boolean);
const rota={ nome:d.get('nome')||'', origem:d.get('origem')||'', destino:d.get('destino')||'', horaIda:d.get('partida')||'', horaVolta:d.get('volta')||'', vagas:Number(d.get('vagas')||0), veiculo:d.get('veiculo')||'', dias, precoVis:d.get('preco_vis')||'', preco:parseBRLToNumber(d.get('preco_vis')||''), paradas };
saveRota(rota); alert('Rota salva com sucesso! Você já pode vê-la em Rotas.'); try{ form.reset(); }catch{}
});
})();