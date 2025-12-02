import { listRotas } from './storage.js';

export function normalizarStr(s) {
  return (s || '').toString().trim().toLowerCase();
}

export function filtrarRotas({ origem, destino, dia }) {
  const o = normalizarStr(origem);
  const d = normalizarStr(destino);
  const diaKey = normalizarStr(dia);

  return listRotas().filter((r) => {
    const matchO =
      !o || normalizarStr(r.origem).includes(o);

    const matchD =
      !d || normalizarStr(r.destino).includes(d);

    const matchDia =
      !diaKey ||
      (r.dias || []).some((x) => normalizarStr(x) === diaKey);

    return matchO && matchD && matchDia;
  });
}
