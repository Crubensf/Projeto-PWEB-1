export function el(tag, attrs={}, children=[]) {
const e=document.createElement(tag);
Object.entries(attrs).forEach(([k,v])=>{
if(k==='class') e.className=v; else if(k.startsWith('aria-')) e.setAttribute(k,v); else if(k==='html') e.innerHTML=v; else e.setAttribute(k,v);
});
[].concat(children).filter(Boolean).forEach(c=>{ if(typeof c==='string') e.appendChild(document.createTextNode(c)); else e.appendChild(c); });
return e;
}
export function renderRotas(lista, container){
container.innerHTML=''; if(!lista.length) return;
for (const r of lista){
const dias=(r.dias||[]).join(' · ');
const card = el('article',{class:'linha-card'},[
el('header',{class:'linha-topo'},[
el('h2',{class:'nome-motorista'}, r.nome || `${r.origem} → ${r.destino}`),
el('a',{class:'botao botao-suave',href:'#'},'Saiba mais')
]),
el('div',{class:'linha-info'},[
el('div',{class:'origem-destino'},[
el('span',{class:'cidade origem'},r.origem),
el('span',{class:'separador'},'→'),
el('span',{class:'cidade destino'},r.destino)
]),
el('div',{class:'horarios'},[
el('div',{class:'horario'},[el('span',{class:'rotulo'},'Saída'), el('strong',{class:'hora'},r.horaIda||'-')]),
el('div',{class:'horario'},[el('span',{class:'rotulo'},'Chegada'), el('strong',{class:'hora'},r.horaVolta||'-')])
])
]),
el('p',{class:'dias'}, dias?`Dias: ${dias}`:''),
el('p',{class:'vagas'}, r.vagas?`Vagas: ${r.vagas}`:''),
]);
container.appendChild(card);
}
}
export function getDiaAtivo(){ const ativo=document.querySelector('.chip-dia.ativo'); return ativo? ativo.textContent.trim():''; }
export function setSemResultadosVisible(flag){ const p=document.querySelector('.sem-resultados'); if(!p) return; p.hidden = !flag; }
export function setTituloLista(texto){ const t=document.getElementById('tituloLista'); if(t) t.textContent = texto; }