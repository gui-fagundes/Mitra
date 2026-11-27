#!/bin/sh
# Backup diário do banco e das imagens enviadas. Guarda os últimos 7 dias.
# Agendar no servidor (crontab -e):  0 3 * * * /root/Mitra/deploy/backup.sh
set -eu

PASTA_DEPLOY="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$PASTA_DEPLOY/backups"
DATA="$(date +%Y-%m-%d_%H%M)"
mkdir -p "$DESTINO"

cd "$PASTA_DEPLOY"
docker compose exec -T db pg_dump -U mitra -d mitra | gzip > "$DESTINO/banco_$DATA.sql.gz"
docker compose exec -T api tar -czf - -C /dados arquivos > "$DESTINO/arquivos_$DATA.tar.gz"

find "$DESTINO" -name "*.gz" -mtime +7 -delete
echo "Backup em $DESTINO ($DATA)"
