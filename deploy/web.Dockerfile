# Frontend compilado servido pelo Caddy, que também faz o HTTPS e repassa a API.
# Contexto do build: a raiz do repositório (ver docker-compose.yml).
FROM node:22-alpine AS build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /frontend/dist /srv
