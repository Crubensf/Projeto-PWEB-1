#!/bin/sh
# Dump diário do Postgres. Mantém últimos 7. Variáveis vêm do env do container.
set -eu

STAMP=$(date +%Y%m%d_%H%M%S)
DEST="/backups/vanja_${STAMP}.sql.gz"
RETENCAO_DIAS=7

echo "[$(date -Iseconds)] iniciando dump → ${DEST}"

export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump \
  -h "${POSTGRES_HOST:-postgres}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  --no-owner --no-privileges \
  | gzip -9 > "${DEST}"

SIZE=$(stat -c %s "${DEST}" 2>/dev/null || stat -f %z "${DEST}")
echo "[$(date -Iseconds)] dump ok: ${SIZE} bytes"

# Limpa backups antigos
find /backups -type f -name "vanja_*.sql.gz" -mtime "+${RETENCAO_DIAS}" -delete
echo "[$(date -Iseconds)] retenção aplicada (>${RETENCAO_DIAS} dias removidos)"
