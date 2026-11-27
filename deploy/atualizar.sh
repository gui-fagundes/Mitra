#!/bin/sh
# Atualiza o Mitra no servidor: baixa a main, reconstrói e confere se a API voltou.
# Rodado pelo deploy automático (GitHub Actions) ou à mão: /root/Mitra/deploy/atualizar.sh
set -eu

PASTA_DEPLOY="$(cd "$(dirname "$0")" && pwd)"
cd "$PASTA_DEPLOY/.."

echo "==> Baixando a versão mais recente"
git pull --ff-only

echo "==> Reconstruindo e reiniciando"
cd "$PASTA_DEPLOY"
docker compose up -d --build --remove-orphans

echo "==> Conferindo a API"
for tentativa in 1 2 3 4 5 6 7 8 9 10 11 12; do
	if docker compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude', timeout=3)" 2>/dev/null; then
		echo "API respondendo ($(git -C "$PASTA_DEPLOY/.." log -1 --format='%h %s'))"
		docker image prune -f >/dev/null
		exit 0
	fi
	sleep 5
done

echo "A API não respondeu em 60 s. Últimos logs:"
docker compose logs --tail 40 api
exit 1
