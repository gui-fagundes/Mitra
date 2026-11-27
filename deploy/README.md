# Deploy do Mitra num Droplet da DigitalOcean

Um único servidor roda tudo com Docker Compose:

| Container | O que faz |
|---|---|
| `web` | Caddy: serve o frontend compilado, repassa `/api` e `/arquivos` para a API e obtém o certificado HTTPS (Let's Encrypt) sozinho |
| `api` | FastAPI (2 workers); aplica as migrações ao subir |
| `db` | PostgreSQL 17 |

Frontend e API ficam no **mesmo endereço**, então o cookie de sessão continua com
`SameSite=Lax` e funciona em qualquer navegador (inclusive Safari e aba anônima).
Banco e imagens enviadas ficam em volumes do Docker e sobrevivem a reinícios.

Custo esperado: Droplet básico de 1 GB (~US$ 6/mês, cobrado por hora). O banco
roda no próprio Droplet; não é preciso contratar o banco gerenciado.

---

## 0. Antes de começar

- **Conta na DigitalOcean.** Estudante: o GitHub Student Developer Pack costuma
  dar crédito na DigitalOcean.
- **Chave SSH** no seu computador. No PowerShell: `ssh-keygen -t ed25519`
  (aceite o caminho padrão). A chave pública fica em `C:\Users\<você>\.ssh\id_ed25519.pub`.
- **Serviço de envio de e-mail na porta 2525.** A DigitalOcean bloqueia as portas
  25, 465 e 587 nos Droplets, então o Gmail não funciona daqui. Crie uma conta
  gratuita no Brevo (ou Mailgun/SendGrid), **verifique o endereço remetente** e
  anote as credenciais SMTP (servidor, usuário e chave).

## 1. Criar o Droplet

No painel da DigitalOcean: **Create → Droplets**

- Imagem: **Ubuntu 24.04 LTS**
- Plano: **Basic → Regular → 1 GB / 1 CPU** (ou 2 GB, se quiser folga)
- Região: **New York** ou **Toronto** (as mais próximas do Brasil)
- Autenticação: **SSH Key** → adicione o conteúdo do seu `id_ed25519.pub`

Anote o **IP** do Droplet.

## 2. Escolher o endereço

- **Sem domínio:** use o sslip.io, que aponta para o IP sem configurar nada.
  Para o IP `203.0.113.10`, o endereço é `203-0-113-10.sslip.io`.
- **Com domínio:** crie um registro **A** apontando `mitra.seudominio.com` para o IP.

## 3. Preparar o servidor

```bash
ssh root@IP_DO_DROPLET
```

Memória extra (o build do frontend passa de 1 GB):

```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

Docker (script oficial) e firewall:

```bash
curl -fsSL https://get.docker.com | sh
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable
```

## 4. Baixar o código

```bash
git clone https://github.com/gui-fagundes/Mitra.git /root/Mitra
```

Se o repositório for privado, o Git vai pedir usuário e senha: use seu usuário do
GitHub e, como senha, um **token de acesso pessoal** (GitHub → Settings → Developer
settings → Personal access tokens, só com leitura do repositório).

## 5. Configurar o `.env`

```bash
cd /root/Mitra/deploy
cp .env.exemplo .env
```

Gere os segredos (cada comando imprime um valor diferente):

```bash
openssl rand -base64 36                    # TOKEN_SECRET_KEY
openssl rand -hex 24                       # POSTGRES_PASSWORD
openssl rand -base64 32 | tr '+/' '-_'     # ENCRYPTION_KEY (chave Fernet)
```

Edite com `nano .env` e preencha `DOMINIO`, `POSTGRES_PASSWORD`,
`TOKEN_SECRET_KEY`, `ENCRYPTION_KEY` e o bloco de SMTP do serviço de envio
(`SMTP_FROM` com o remetente verificado nele). Salve com Ctrl+O, Enter, Ctrl+X.

## 6. Subir

```bash
docker compose up -d --build
docker compose logs -f
```

O primeiro build leva alguns minutos. Quando aparecer `Application startup complete`
na API e o Caddy registrar o certificado, saia dos logs com Ctrl+C.

## 7. Conferir

1. Abra `https://DOMINIO` e veja o cadeado de HTTPS.
2. Crie uma conta com um e-mail seu e confira se o **e-mail de confirmação chega**.
3. Envie uma foto de perfil, abra a busca e o perfil público.

O banco começa só com cidades, categorias e serviços. Antes do teste de usabilidade,
cadastre pela própria interface os prestadores de exemplo que os participantes
vão encontrar.

## 8. Backups

```bash
chmod +x /root/Mitra/deploy/backup.sh
/root/Mitra/deploy/backup.sh               # testa uma vez
crontab -e                                 # e acrescente a linha:
0 3 * * * /root/Mitra/deploy/backup.sh
```

Os arquivos ficam em `deploy/backups/` (banco e imagens, últimos 7 dias). Para
trazer para o seu computador, no PowerShell:

```bash
scp -r root@IP_DO_DROPLET:/root/Mitra/deploy/backups .
```

## 9. Atualizar depois de uma mudança no código

```bash
cd /root/Mitra && git pull
cd deploy && docker compose up -d --build
```

Ou, com o mesmo efeito e conferindo se a API voltou:

```bash
/root/Mitra/deploy/atualizar.sh
```

As migrações novas são aplicadas sozinhas quando a API sobe.

### Deploy automático (GitHub Actions)

O workflow `.github/workflows/ci-deploy.yml` roda lint, testes e build a cada push.
Na `main`, se tudo passar, ele entra no servidor e roda `deploy/atualizar.sh`
(o mesmo `git pull` + `docker compose up -d --build`, conferindo se a API voltou).

Configuração, uma vez só:

**a) Chave só para o deploy, sem passphrase** (no seu computador, PowerShell):

```bash
ssh-keygen -t ed25519 -N '""' -C "deploy-github" -f "$env:USERPROFILE\.ssh\mitra_deploy"
```

**b) Autorizar a chave no servidor, presa a um único comando.** Copie a pública
(`Get-Content "$env:USERPROFILE\.ssh\mitra_deploy.pub" | Set-Clipboard`) e, no servidor:

```bash
echo 'command="/root/Mitra/deploy/atualizar.sh",restrict COLE_A_CHAVE_PUBLICA_AQUI' >> /root/.ssh/authorized_keys
```

Com `command=` e `restrict`, essa chave não abre terminal nem roda outra coisa:
qualquer conexão com ela só executa o script de atualização.

**c) Secrets do repositório** (GitHub → Settings → Secrets and variables → Actions →
New repository secret):

| Nome | Valor |
|---|---|
| `DEPLOY_HOST` | IP do Droplet |
| `DEPLOY_SSH_KEY` | conteúdo inteiro de `mitra_deploy` (a **privada**, sem `.pub`) |
| `DEPLOY_KNOWN_HOSTS` | saída de `ssh-keyscan -t ed25519 IP_DO_DROPLET` (garante que o GitHub fala com o seu servidor) |

**d) Testar:** aba **Actions → CI e deploy → Run workflow** na `main`.

Para **pausar o deploy automático** , crie em **Variables** a variável `DEPLOY_AUTOMATICO` com valor `false`.
Os testes continuam rodando a cada push, e o botão **Run workflow** ainda publica
quando você quiser. Apague a variável para voltar ao automático.

## 10. Encerrar (depois da defesa)

1. Rode um último `backup.sh` e baixe a pasta `backups` (passo 8).
2. No painel da DigitalOcean, **Destroy** no Droplet. A cobrança para na hora;
   desligar o Droplet sem destruir **continua sendo cobrado**.

---

## Problemas comuns

| Sintoma | O que ver |
|---|---|
| Site não abre / sem HTTPS | `docker compose logs web`. O `DOMINIO` precisa apontar para o IP, e as portas 80 e 443 precisam estar liberadas no `ufw` |
| Erro 502 em `/api` | `docker compose logs api` (variável faltando no `.env` costuma aparecer aqui) |
| E-mail não chega | `docker compose logs api \| grep -i e-mail`. Confira porta 2525 e remetente verificado no serviço de envio |
| Build trava ou é encerrado | Falta de memória: confira o swap do passo 3 (`free -h`) |
| Ver os dados direto no banco | `docker compose exec db psql -U mitra -d mitra` |
