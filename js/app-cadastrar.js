import { saveUsuario, setSessao } from './storage.js';
import { hydrateHeader } from './auth.js';
(function(){
hydrateHeader();
const form=document.querySelector('.cadastro-form'); if(!form) return;
const senha=document.getElementById('senha');
const confirmar=document.getElementById('confirmar');
const perfil=document.getElementById('perfil');
const blocoMotorista=document.getElementById('dados-motorista');
const cnh=document.getElementById('cnh');
const cnhImg=document.getElementById('cnh_imagem');
const docVeicImg=document.getElementById('doc_veiculo_imagem');
const msgConfirm=confirmar?.parentElement?.querySelector('.msg-erro');
const MAX_MB=5, MAX_BYTES=MAX_MB*1024*1024;
function toggleCamposMotorista(){ const isMotorista=perfil?.value==='motorista'; if(!blocoMotorista) return; blocoMotorista.style.display=isMotorista?'block':'none'; [cnh,cnhImg,docVeicImg].forEach(el=>{ if(!el) return; if(isMotorista){ el.setAttribute('required','required'); } else { el.removeAttribute('required'); const msg=el.parentElement?.querySelector('.msg-erro'); if(msg) msg.textContent=''; if(el.type==='file') el.value=''; else el.value=''; } }); }
perfil?.addEventListener('change', toggleCamposMotorista); toggleCamposMotorista();
function validaArquivo(input){ const msg=input.parentElement?.querySelector('.msg-erro'); if(msg) msg.textContent=''; const file=input.files && input.files[0]; if(file && file.size>MAX_BYTES){ if(msg) msg.textContent=`Arquivo muito grande. Máx: ${MAX_MB} MB.`; return false; } return true; }
cnh?.addEventListener('input', ()=>{ cnh.value=cnh.value.replace(/\D/g,'').slice(0,11); const msg=cnh.parentElement?.querySelector('.msg-erro'); if(msg) msg.textContent=''; });
;[cnhImg,docVeicImg].forEach(el=>{ el?.addEventListener('change', ()=>{ const msg=el.parentElement?.querySelector('.msg-erro'); if(msg) msg.textContent=''; }); });
confirmar?.addEventListener('input', ()=>{ if(msgConfirm) msgConfirm.textContent=''; });
form.addEventListener('submit', (e)=>{
if (senha && confirmar && senha.value!==confirmar.value){ e.preventDefault(); if(msgConfirm) msgConfirm.textContent='As senhas não coincidem.'; confirmar.focus(); return; }
if (perfil?.value==='motorista' && cnh){ const msg=cnh.parentElement?.querySelector('.msg-erro'); if(!/^\d{11}$/.test(cnh.value)){ e.preventDefault(); if(msg) msg.textContent='Informe os 11 dígitos da CNH (somente números).'; cnh.focus(); return; } else if(msg){ msg.textContent=''; } }
if (perfil?.value==='motorista'){ if(cnhImg && !validaArquivo(cnhImg)){ e.preventDefault(); cnhImg.focus(); return; } if(docVeicImg && !validaArquivo(docVeicImg)){ e.preventDefault(); docVeicImg.focus(); return; } }
e.preventDefault(); const d=new FormData(form); const user={ nome:d.get('nome')||'', email:d.get('email')||'', senha:d.get('senha')||'', perfil:d.get('perfil')||'estudante' };
saveUsuario(user); setSessao(user.email); alert('Cadastro concluído!'); location.assign('index.html');
});
})();