# Session Documentation Security Guide

**Version**: 1.0.0
**Last Updated**: 09/11/2026 15:35
**Part of**: IMP-50 — Sistema de documentação incremental — Docs + Migração

---

## 🎯 Objetivo

Este guia fornece exemplos práticos de **DO** e **DON'T** para documentação segura de sessões de desenvolvimento, prevenindo exposição acidental de dados sensíveis.

**Princípio fundamental:**
> Session docs são commitados em git público → **NUNCA** incluir dados que comprometam segurança, privacidade ou compliance.

---

## 🚨 Categorias de Dados Sensíveis

### P0 — Credenciais (CRÍTICO)

| Tipo | Risco | Impacto |
|------|-------|---------|
| API Keys | Acesso não autorizado a serviços | Crítico |
| Passwords | Comprometimento de contas | Crítico |
| Tokens (JWT, OAuth) | Sessões hijacking | Crítico |
| SSH Private Keys | Acesso a servidores | Crítico |
| Database URLs com credenciais | Acesso a dados | Crítico |

### P1 — Infraestrutura Interna

| Tipo | Risco | Impacto |
|------|-------|---------|
| IPs privados (10.x, 172.16-31.x, 192.168.x) | Mapeamento de rede interna | Alto |
| Hostnames internos | Descoberta de arquitetura | Alto |
| Portas não-padrão | Fingerprinting de serviços | Médio |
| URLs de produção internas | Exposição de endpoints | Alto |

### P2 — Dados Pessoais (PII)

| Tipo | Risco | Impacto |
|------|-------|---------|
| Emails reais de clientes/usuários | LGPD/GDPR violation | Alto |
| CPF, CNPJ, SSN | Compliance violation | Crítico |
| Nomes completos reais | Privacy breach | Médio |
| Endereços físicos | Privacy breach | Médio |

### P3 — Informacional

| Tipo | Risco | Impacto |
|------|-------|---------|
| Paths absolutos do sistema | Information disclosure | Baixo |
| Versões específicas de libs vulneráveis | Exploitation guidance | Médio |
| Estrutura detalhada de banco de dados | Schema disclosure | Médio |

---

## ✅ DO — Exemplos Corretos

### 1. API Keys e Tokens

#### ❌ DON'T
```markdown
**Passos executados**:
1. Configurar API key: `sk_live_EXEMPLO_FICTICIO`
2. Testar autenticação
```

#### ✅ DO
```markdown
**Passos executados**:
1. Configurar API key: `<REDACTED>` ou `sk_live_***`
2. Testar autenticação
```

**Melhor ainda:**
```markdown
**Passos executados**:
1. Configurar API key via `.env`: `API_KEY=<your_key_here>`
2. Testar autenticação com variável de ambiente
```

---

### 2. Database Connection Strings

#### ❌ DON'T
```markdown
**Contexto**: Conectar ao banco de produção

**Passos executados**:
1. `mysql://admin:MyS3cr3tP@ss@10.20.30.40:3306/production_db`
2. Executar migration
```

#### ✅ DO
```markdown
**Contexto**: Conectar ao banco de produção

**Passos executados**:
1. `mysql://<USER>:<PASSWORD>@<DB_HOST>:3306/<DB_NAME>`
2. Executar migration (credenciais via `.env`)
```

**Melhor ainda:**
```markdown
**Contexto**: Conectar ao banco de produção

**Passos executados**:
1. Configurar `DB_URL` via secrets manager
2. Executar migration: `make db-migrate ENV=production`
```

---

### 3. IP Addresses e Hostnames

#### ❌ DON'T
```markdown
**Resultado**: Servidor provisionado em 10.20.30.40 (internal-api.company.local)
```

#### ✅ DO
```markdown
**Resultado**: Servidor provisionado em `<PRIVATE_IP>` (`<INTERNAL_HOSTNAME>`)
```

**Melhor ainda:**
```markdown
**Resultado**: Servidor provisionado conforme playbook ansible (ver inventory/production.yml)
```

**Para testes locais** (IPs locais OK):
```markdown
**Resultado**: Container rodando em 127.0.0.1:8080 (localhost)
```

**Para exemplos** (usar RFC 5737 IPs):
```markdown
**Exemplo**: Configurar firewall para bloquear 192.0.2.0/24 (TEST-NET-1)
```

---

### 4. Email Addresses

#### ❌ DON'T
```markdown
**Contexto**: Testar notificação para cliente@empresareal.com.br
```

#### ✅ DO
```markdown
**Contexto**: Testar notificação para `user@example.com`
```

**Emails de sistema** (OK para usar):
```markdown
**Contexto**: Configurar sender: `noreply@projeto.com`
```

---

### 5. JWT Tokens e Bearer Tokens

#### ❌ DON'T
```markdown
**Passos executados**:
1. Autenticar: `Authorization: Bearer eyJhbGciOiJI...real_token_here`
2. Fazer request ao endpoint
```

#### ✅ DO
```markdown
**Passos executados**:
1. Autenticar: `Authorization: Bearer <JWT_TOKEN>`
2. Fazer request ao endpoint
```

**Ou mascarar:**
```markdown
**Passos executados**:
1. Autenticar: `Authorization: Bearer eyJ...***`
2. Fazer request ao endpoint
```

---

### 6. SSH Commands e Keys

#### ❌ DON'T
```markdown
**Passos executados**:
1. `ssh admin@10.50.60.70 -i ~/.ssh/prod_key.pem`
2. Copiar arquivo: `scp file.txt admin@10.50.60.70:/var/www/`
```

#### ✅ DO
```markdown
**Passos executados**:
1. `ssh <USER>@<SERVER_IP> -i ~/.ssh/<KEY_NAME>`
2. Copiar arquivo: `scp file.txt <USER>@<SERVER_IP>:<DEST_PATH>`
```

**Melhor ainda:**
```markdown
**Passos executados**:
1. Acessar servidor via SSH config: `ssh prod-web-01`
2. Deploy via ansible: `ansible-playbook deploy.yml -i production`
```

---

### 7. Certificados e Keys

#### ❌ DON'T
```markdown
**Arquivo criado**: cert.pem
```
```
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL0UG+mRKSzMA0

GCSqGSIb3DQEBCwUA...
-----END CERTIFICATE-----
```

#### ✅ DO
```markdown
**Arquivo criado**: cert.pem (certificado TLS armazenado em `.secrets/certs/`)
```

**Ou:**
```markdown
**Arquivo criado**: Certificado gerado via Let's Encrypt:
```bash
certbot certonly --webroot -w /var/www/html -d example.com
```
```

---

### 8. Paths Absolutos do Sistema

#### ❌ DON'T
```markdown
**Arquivo modificado**: `/home/yves/Documentos/TopSecret/passwords.txt`
```

#### ✅ DO
```markdown
**Arquivo modificado**: `docs/configs/database.yml` (caminho relativo ao projeto)
```

**Quando paths absolutos são necessários:**
```markdown
**Arquivo modificado**: `/home/user/project/...` (sanitizar nome real)
```

---

### 9. Variáveis de Ambiente

#### ❌ DON'T
```markdown
**Passos executados**:
1. `export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE`
2. `export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7M...real_secret`
```

#### ✅ DO
```markdown
**Passos executados**:
1. Configurar `.env` com variáveis AWS (ver `.env.example`)
2. Carregar: `source .env`
```

**Ou placeholders:**
```markdown
**Passos executados**:
1. `export AWS_ACCESS_KEY_ID=<YOUR_ACCESS_KEY>`
2. `export AWS_SECRET_ACCESS_KEY=<YOUR_SECRET_KEY>`
```

---

### 10. URLs de Produção

#### ❌ DON'T
```markdown
**Contexto**: Testar webhook em https://api.cliente-secreto.com/webhooks/payment-callback
```

#### ✅ DO (opção 1 - genérico)
```markdown
**Contexto**: Testar webhook em `<PRODUCTION_API_URL>/webhooks/<ENDPOINT>`
```

#### ✅ DO (opção 2 - exemplo válido)
```markdown
**Contexto**: Testar webhook em https://api.exemplo.local/webhooks/payment-callback
```

---

## 🔍 Padrões de Sanitização

### Template de Sanitização Padrão

| Dado Real | Sanitizado | Notação |
|-----------|------------|---------|
| `sk_live_abc123...` | `<API_KEY>` ou `sk_live_***` | Redação completa ou mascaramento |
| `MyP@ssw0rd!` | `<PASSWORD>` ou `***` | Redação ou asteriscos |
| `10.20.30.40` | `<PRIVATE_IP>` ou `192.0.2.1` | Placeholder ou TEST-NET |
| `admin@cliente.com` | `user@example.com` | Domínio exemplo |
| `internal-db.corp.local` | `<INTERNAL_HOST>` | Placeholder genérico |
| `/home/john/proj/` | `/home/user/proj/` | Nome genérico |
| `https://prod-api.secret.io` | `<PROD_API>` ou `https://api.exemplo.com` | Placeholder ou exemplo |

---

## 🧪 Testes de Segurança

### 1. Auto-Verificação Manual

Antes de commitar, procurar por padrões:

```bash
# Buscar credenciais óbvias
grep -r "password.*=.*[^<]" docs/SESSIONS/2026-04-03/
grep -r "secret.*=.*[^<]" docs/SESSIONS/2026-04-03/
grep -r "api_key.*=.*[^<]" docs/SESSIONS/2026-04-03/

# Buscar IPs privados
grep -rE "10\.\d+\.\d+\.\d+" docs/SESSIONS/2026-04-03/
grep -rE "192\.168\.\d+\.\d+" docs/SESSIONS/2026-04-03/

# Buscar emails não-example
grep -rE "[a-z0-9.]+@(?!example\.(com|org|net))" docs/SESSIONS/2026-04-03/
```

### 2. Validação Automática (Gitleaks)

```bash
# Scan local antes de commit
make session-sanitize

# Ou diretamente:
gitleaks detect \
  --config .gitleaks-session-docs.toml \
  --source docs/SESSIONS/2026-04-03/ \
  --verbose
```

### 3. CI/CD Integration

Ver template completo em: `.github/templates/ci-jobs/SESSION_DOCS_SCAN_JOB.md`

---

## 🛡️ Procedimento de Remediação

### Se Dados Sensíveis Foram Commitados

#### 1. **Avaliar Impacto**

```bash
# Verificar se commit foi pushed
git log --oneline -5
git status

# Se AINDA NÃO foi pushed → simples
# Se JÁ foi pushed → crítico
```

#### 2. **Se NÃO foi pushed** (local only)

```bash
# Opção A: Corrigir último commit
# 1. Sanitizar arquivos
sed -i 's/password=MyP@ss/password=<REDACTED>/g' docs/SESSIONS/.../file.md

# 2. Amend commit
git add docs/SESSIONS/.../file.md
git commit --amend --no-edit

# Opção B: Reset e recommit
git reset HEAD~1
# Sanitizar arquivos
git add .
git commit -m "..." -F /tmp/commit.txt
```

#### 3. **Se JÁ foi pushed** (público)

**⚠️ AÇÃO IMEDIATA NECESSÁRIA**

```bash
# 1. Revogar credenciais comprometidas
# - Rotacionar API keys
# - Trocar senhas
# - Invalidar tokens

# 2. Reescrever histórico (DESTRUCTIVE)
git filter-repo --path docs/SESSIONS/.../file.md --invert-paths
# OU usar BFG Repo-Cleaner

# 3. Force push (se repositório privado)
git push origin master --force

# 4. Notificar time
# 5. Documentar incidente
```

**Para repositórios públicos:**
- Assumir que dados já foram indexados (GitHub, Archive.org, etc)
- Revogar TODAS as credenciais expostas imediatamente
- Considerar criar novo repositório se exposição for crítica

---

## 📋 Checklist de Revisão Pré-Commit

Antes de cada commit com mudanças em session docs:

### Automático
- [ ] `make session-sanitize` passou (exit code 0)
- [ ] `make session-validate` passou (sem erros)

### Manual (quick scan)
- [ ] Nenhum `password=` seguido de valor real
- [ ] Nenhum `api_key=` seguido de valor real
- [ ] Nenhum IP da forma `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x` sem ser exemplo
- [ ] Nenhum email com domínio real (exceto noreply@, bot@)
- [ ] Nenhum Bearer token com valor real
- [ ] Nenhum path `/home/<nome-real>/`
- [ ] Nenhuma URL de produção não-pública

### Se algum item falhar:
1. ❌ **NÃO COMMITAR**
2. Sanitizar dados conforme exemplos deste guia
3. Re-executar checklist

---

## 🎓 Treinamento e Cultura

### Para Novos Membros

**Sessão obrigatória** (30 min):
1. Apresentar este guia
2. Mostrar 5 exemplos de DO/DON'T
3. Praticar: sanitizar 3 blocos com dados sensíveis
4. Ensinar: `make session-sanitize` antes de todo commit

### Para Time Estabelecido

**Code review focus:**
- Revisor deve verificar session docs em PRs
- Template de PR checklist deve incluir "Session docs sanitized"

**Retrospectivas:**
- Incluir questão: "Houve alguma exposição acidental esta sprint?"
- Documentar lições aprendidas

---

## 📚 Referências

- [SESSION_DOCS_STYLE_GUIDE.md](SESSION_DOCS_STYLE_GUIDE.md) - Formato canônico
- [SESSION_DOCS_ADOPTION.md](SESSION_DOCS_ADOPTION.md) - Guia de adoção
- [.gitleaks-session-docs.toml](../.gitleaks-session-docs.toml) - Configuração de scan
- [OWASP Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [LGPD](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd) - Lei Geral de Proteção de Dados
- [GDPR](https://gdpr.eu/) - General Data Protection Regulation

---

## 🚨 Reporte de Incidentes

Se você descobrir dados sensíveis expostos em session docs:

**Contato imediato:**
- 🔒 Security Lead: [definir contato]
- 📧 DevSecOps: [definir email]
- 🆘 Incident Response: [definir processo]

**Não:**
- ❌ Comentar no código ou PR mencionando o dado sensível
- ❌ Enviar screenshot com dado exposto
- ❌ Esperar até "momento conveniente"

**Fazer:**
- ✅ Relatar via canal seguro imediatamente
- ✅ Documentar timestamp de descoberta
- ✅ Seguir procedimento de remediação acima

---

*Security Guide v1.0 | IMP-50 | 2026-04-03*
