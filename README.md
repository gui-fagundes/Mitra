# Mitra

Monorepo fullstack com API em FastAPI + Postgres e SPA em Vue 3.

## Stack

**Backend** (`backend/`)
- FastAPI · SQLAlchemy 2 (sync) · psycopg 3 · Alembic
- Auth: JWT em cookie **httpOnly** + **sliding session** (renovação automática)
- `bcrypt` para senhas, `python-jose` para tokens, `cryptography.Fernet` para dados sensíveis
- Testes: `pytest` com fixtures transacionais (rollback por teste)
- Lint/format: `ruff`

**Frontend** (`frontend/`)
- Vue 3 (`<script setup>`) · TypeScript · Vite
- `vue-router` (com guards de auth) · `pinia` (store) · `axios` (com `withCredentials`)
- Tailwind CSS v4 (via `@tailwindcss/vite`, sem `tailwind.config.js`)

**Repo**
- Git hooks via `pre-commit`: ruff + higiene de arquivos

## Estrutura

```
Mitra/
├── backend/
│   ├── app/
│   │   ├── config/         # database, dependencies, constants, migrations helper
│   │   ├── middlewares/    # exception handler, sliding session
│   │   ├── models/         # SQLAlchemy models + ToDictMixin
│   │   ├── routes/         # APIRouters
│   │   ├── schemas/        # Pydantic
│   │   ├── services/       # regras de negócio (chamadas pelas routes)
│   │   ├── utils/          # auth, cookies, datas, conversões
│   │   └── cli.py          # entry points de `uv run dev/start/migrate/...`
│   ├── migrations/         # Alembic
│   ├── tests/              # pytest (conftest + test_*.py)
│   └── main.py
├── frontend/
│   └── src/
│       ├── api/            # axios client + wrappers tipados
│       ├── stores/         # Pinia
│       ├── views/          # páginas (Login, Register, Home)
│       ├── App.vue
│       ├── main.ts
│       └── router.ts
├── .pre-commit-config.yaml
└── .gitignore
```

## Pré-requisitos

- Python 3.13+ e [`uv`](https://docs.astral.sh/uv/)
- Node.js 20+ e `npm`
- Postgres acessível (local ou remoto) — **dois bancos**: um pro app, outro pros testes

## Setup — backend

```bash
cd backend
cp .env.example .env      # preencher variáveis (ver seção abaixo)
uv sync                   # instala deps + dev deps (ruff, pytest, pre-commit, httpx2)
uv run dev                # aplica migrations e sobe uvicorn com --reload em :8000
```

Scripts (`[project.scripts]`):

| Comando                             | O que faz                                            |
| ----------------------------------- | ---------------------------------------------------- |
| `uv run dev`                        | Migra e sobe em dev (reload, `127.0.0.1:8000`)       |
| `uv run start`                      | Migra e sobe em prod (4 workers, `0.0.0.0:8000`)     |
| `uv run test`                       | Roda `pytest` (aceita args extras)                   |
| `uv run lint`                       | `ruff check .`                                       |
| `uv run format`                     | `ruff format .`                                      |
| `uv run migrate`                    | `alembic upgrade head`                               |
| `uv run rollback`                   | `alembic downgrade -1`                               |
| `uv run makemigration "mensagem"`   | Gera revisão autogenerate                            |

Swagger: `http://localhost:8000/docs`.

## Setup — frontend

```bash
cd frontend
npm install
npm run dev               # Vite em :5173, proxy /api/* → backend :8000
```

Scripts do `package.json`: `dev`, `build`, `preview`.

Rotas:

| Path         | Acesso        |
| ------------ | ------------- |
| `/login`     | guest only    |
| `/register`  | guest only    |
| `/`          | autenticado   |

O proxy do Vite (`/api` → `127.0.0.1:8000`) evita CORS em dev. Em produção, o backend precisa servir o build estático **ou** ter a origem do frontend em `CORS_ORIGINS`.

## Variáveis de ambiente (backend)

Todas em [`backend/.env`](backend/.env.example) (não versionado):

| Variável              | Obrigatório | O que é                                                       |
| --------------------- | ----------- | ------------------------------------------------------------- |
| `DATABASE_URL`        | sim         | Postgres do app (aceita `postgresql://` — driver normalizado) |
| `TEST_DATABASE_URL`   | pra testes  | Banco separado, schema é dropped/recriado por sessão de teste |
| `TOKEN_SECRET_KEY`    | sim         | Chave HMAC do JWT                                             |
| `TOKEN_ALGORITHM`     | sim         | Ex.: `HS256`                                                  |
| `ENCRYPTION_KEY`      | sim         | Fernet key (base64 32 bytes)                                  |
| `ENV`                 | não         | `development` (default) ou `production` — controla `Secure`   |
| `CORS_ORIGINS`        | não         | Lista separada por vírgula. Default `http://localhost:5173`   |

Gerar `ENCRYPTION_KEY`:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Autenticação — como funciona

1. `POST /auth/signup` ou `POST /auth/login` retornam o usuário e setam cookie **`access_token` httpOnly** (`SameSite=lax`, `Secure` em produção).
2. Requests subsequentes carregam o cookie automaticamente. `get_current_user` valida e injeta o `Usuario` nas rotas protegidas.
3. **Sliding session**: cada request autenticada reemite o cookie com `exp` resetado. O usuário só é deslogado após `TOKEN_EXPIRATION_TIME` (60 min) de **inatividade**.
4. `POST /auth/logout` apaga o cookie (204).

Endpoints:

| Método   | Path             | Auth     |
| -------- | ---------------- | -------- |
| `POST`   | `/auth/signup`   | público  |
| `POST`   | `/auth/login`    | público  |
| `POST`   | `/auth/logout`   | público  |
| `GET`    | `/auth/me`       | cookie   |
| `GET`    | `/health-check`  | público  |

## Testes

```bash
cd backend
uv run test                       # roda tudo
uv run test tests/test_auth.py    # arquivo específico
uv run test -k login              # filtro por nome
```

Cada teste roda em uma transação isolada — nada persiste no `TEST_DATABASE_URL` entre testes.

## Git hooks (pre-commit)

Após clonar o repo, uma vez:

```bash
cd backend && uv run pre-commit install
```

A partir daí todo `git commit` roda ruff + higiene de arquivos. Rodar manual em tudo:

```bash
uv run --project backend pre-commit run --all-files
```

## O que não está aqui ainda

Coisas comuns que serão adicionadas conforme aparecer necessidade:

- CI (GitHub Actions rodando `uv run test` + `npm run build`)
- Refresh token real (hoje temos sliding session)
- Rate limit em `/auth/login`
- Logs estruturados (hoje é `print()` + tabela `logerro`)
- ESLint/Prettier no frontend
- Path aliases (`@/...`) no frontend
