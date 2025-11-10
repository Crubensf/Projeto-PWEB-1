const DB_KEYS = { usuarios: 'pweb:usuarios', rotas: 'pweb:rotas', sessao: 'pweb:sessao' };
function getJSON(key, fallback){ try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } }
function setJSON(key, value){ localStorage.setItem(key, JSON.stringify(value)); }
export function listUsuarios(){ return getJSON(DB_KEYS.usuarios, []); }
export function saveUsuario(user){ const arr = listUsuarios(); const i = arr.findIndex(u => u.email === user.email); if (i>=0) arr[i]=user; else arr.push(user); setJSON(DB_KEYS.usuarios, arr); }
export function findUsuarioByEmail(email){ return listUsuarios().find(u => u.email===email) || null; }
export function setSessao(email){ localStorage.setItem(DB_KEYS.sessao, email); }
export function getSessao(){ return localStorage.getItem(DB_KEYS.sessao); }
export function clearSessao(){ localStorage.removeItem(DB_KEYS.sessao); }
export function getUsuarioLogado(){ const email=getSessao(); return email? findUsuarioByEmail(email): null; }
export function listRotas(){ return getJSON(DB_KEYS.rotas, []); }
export function saveRota(rota){ const arr=listRotas(); rota.id = rota.id || ('r_'+Math.random().toString(36).slice(2)); const i=arr.findIndex(r=>r.id===rota.id); if(i>=0) arr[i]=rota; else arr.push(rota); setJSON(DB_KEYS.rotas, arr); return rota.id; }
export function clearAll(){ localStorage.removeItem(DB_KEYS.usuarios); localStorage.removeItem(DB_KEYS.rotas); localStorage.removeItem(DB_KEYS.sessao); }