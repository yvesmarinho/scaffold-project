# Migration Guide — Enterprise Scaffold Project Template

> **Versão do documento**: 1.0.0
> **Última actualização**: 2026-03-14
> **Versões cobertas**: v1.2.0 → v1.3.0 → próximas versões

---

## Índice

1. [Conceitos fundamentais](#1-conceitos-fundamentais)
2. [O que o `--upgrade` faz automaticamente](#2-o-que-o---upgrade-faz-automaticamente)
3. [O que requer acção manual](#3-o-que-requer-acção-manual)
4. [Procedimento geral de migração](#4-procedimento-geral-de-migração)
5. [Migrando de v1.2.0 para v1.3.0](#5-migrando-de-v120-para-v130)
6. [Migrando de v1.3.0 para a próxima versão](#6-migrando-de-v130-para-a-próxima-versão)
7. [Referência rápida de comandos](#7-referência-rápida-de-comandos)
8. [Solução de problemas](#8-solução-de-problemas)

---

## 1. Conceitos fundamentais

### O ficheiro `.scaffold-state.yaml`

Cada projecto gerado pelo scaffold contém um ficheiro `.scaffold-state.yaml` na sua raiz. Ele regista:

- Versão do scaffold que gerou o projecto (`scaffold_version`)
- Data de criação e de última actualização
- Configuração do projecto (domínio, linguagem, nome, repo)
- Lista de perfis SpecKit aplicados (`profiles_applied`)

Exemplo:

```yaml
scaffold_version: "1.0.0"
created_at: "2026-01-15T10:00:00Z"
updated_at: "2026-03-14T09:30:00Z"
project:
  name: meu-servico
  domain: programming
  language: python
  github_repo: https://github.com/org/meu-servico
profiles_applied:
  - devops-programming
  - python-fastapi
  - devops-security
```

> ⚠️ **Não remova este ficheiro.** Ele é necessário para o `--upgrade` funcionar.
> ✅ **Commite-o** no repositório do projecto — é seguro e não contém segredos.

### Política de retrocompatibilidade

| Tipo de mudança no template | Impacto nos projectos existentes |
|-----------------------------|----------------------------------|
| Novo perfil Layer 2         | Nenhum (opt-in via `--compose`)  |
| Novo campo YAML gerado      | `--upgrade` adiciona automaticamente |
| Novo ficheiro de configuração gerado | `--upgrade` cria se ausente |
| Alteração de ficheiro de configuração existente | `--upgrade` **não sobrescreve** (usa `--force`) |
| Remoção de campo deprecated | Requer acção manual              |
| Breaking change de CLI (`--` flags) | Documentado por versão major |

---

## 2. O que o `--upgrade` faz automaticamente

Ao executar `scaffold.py --upgrade [--target-dir /caminho/projecto]`, o scaffold:

### ✅ Cria ficheiros ausentes

- **Estrutura de directórios** — pastas padrão do projecto que não existam
- **Symlinks** para `.copilot-shared/` — recria se quebrados ou ausentes
- **`.copilot-rules.md`** — gera a partir do template (se ausente)
- **`.github/copilot-instructions.md`** — gera a partir do template (se ausente)
- **`.vscode/settings.json`**, **`mcp.json`**, **`extensions.json`**, **`tasks.json`**, **`launch.json`** — gera cada um que não exista
- **`.specify/constitution.md`** — gera se ausente
- **`scripts/load-mcp.sh`** — gera se ausente
- **Assets SpecKit** (`.github/agents/`, `.github/prompts/`, `.github/copilot-skills.json`) — copia novos assets
- **`docs/PROFILE-GUIDE-*.md`** — regenera guia de composição de perfis

### ✅ Pula ficheiros sem alteração

Quando o ficheiro já existe **e o conteúdo é idêntico** → operação marcada como `skipped`.

### ⚠️ Pula ficheiros com divergência (sem `--force`)

Quando o ficheiro já existe **com conteúdo diferente** → operação marcada como `skipped` para preservar as suas customizações.

Para sobrescrever explicitamente:

```bash
scaffold.py --upgrade --force --target-dir /caminho/projecto
```

> `--force` sobrescreve **todos** os ficheiros com divergência, incluindo customizações. Use com cuidado e verifique o git diff depois.

### ✅ Re-aplica perfis SpecKit registados

Todos os perfis listados em `profiles_applied` do `.scaffold-state.yaml` são re-aplicados. Novos templates adicionados a um perfil existente são copiados; ficheiros já existentes e iguais são pulados.

---

## 3. O que requer acção manual

### 🔴 Campos depreciados em descritores YAML

Quando um campo de `profile-descriptors/*.yaml` muda de nome entre versões (ex: `VERSION` → `version`), os seus ficheiros gerados podem ficar desactualizados. Verifique o CHANGELOG da versão e actualize manualmente os campos marcados como deprecated.

### 🔴 Breaking changes de CLI

Em versões **major** (ex: v1.x.x → v2.0.0), os argumentos `--` da CLI podem mudar. Reveja as notas de quebra no CHANGELOG e actualize scripts de CI que chamem `scaffold.py`.

### 🔴 Personalização de ficheiros sobrescritos por `--force`

Se usou `--force` e sobrescreveu um ficheiro customizado, reconstrua as customizações sobre o novo template usando `git diff`.

### 🟡 Reorganização de directórios

Quando o template muda a estrutura de directórios gerada, o `--upgrade` cria a nova estrutura mas **não remove** a estrutura antiga. Remova manualmente pastas obsoletas.

### 🟡 Adição de novos perfis Layer 2

Novos perfis Layer 2 (ex: `devops-security`, `data-warehouse-dbt`) são **opt-in**. Para aplicar ao projecto existente:

```bash
scaffold.py --compose devops-programming,python-fastapi,devops-security \
            --target-dir /caminho/projecto
```

### 🟡 Novos campos em `.scaffold-state.yaml`

Versions futuras do scaffold podem adicionar novos campos ao estado. O scaffold lê o ficheiro existente e adiciona campos em falta; porém, se preferir regenerar:

```bash
# Re-cria o .scaffold-state.yaml com todos os campos actuais
scaffold.py --upgrade --target-dir /caminho/projecto
```

### 🟡 `SCAFFOLD_VERSION` em `scripts/lib/config.py`

Quando um release é gerado com `make release VERSION=x.y.z`, o campo é actualizado automaticamente. Se actualizar o template manualmente sem usar `make release`, actualize este campo à mão para garantir que os state files gerados reflitam a versão correcta.

---

## 4. Procedimento geral de migração

```
┌─────────────────────────────────────────────┐
│  1. Actualizar o template (git pull/checkout) │
│  2. Verificar CHANGELOG.md desta versão       │
│  3. Dry-run para ver o que mudaria            │
│  4. Executar --upgrade                        │
│  5. Rever git diff                            │
│  6. Aplicar acções manuais (se houver)        │
│  7. Rodar testes do projecto                  │
│  8. Commitar                                  │
└─────────────────────────────────────────────┘
```

**Passo a passo:**

```bash
# 1. Actualizar o template local
cd ~/caminho/do/template
git pull origin master

# 2. Verificar o que mudou
cat CHANGELOG.md | head -60

# 3. Dry-run no projecto alvo
python scripts/scaffold.py --dry-run --json \
  --target-dir ~/projecto/meu-servico | python -m json.tool

# 4. Executar --upgrade
python scripts/scaffold.py --upgrade \
  --target-dir ~/projecto/meu-servico

# 5. Rever o diff
cd ~/projecto/meu-servico
git diff

# 6. Acções manuais (ver seção específica da versão abaixo)

# 7. Rodar testes
make test   # ou pytest, ou o runner do projecto

# 8. Commitar
git add -A
git commit -m "chore: upgrade scaffold template vX.Y.Z"
```

---

## 5. Migrando de v1.2.0 para v1.3.0

### Novidades relevantes para projectos existentes

| Componente | O que mudou |
|-----------|-------------|
| `profile-descriptors/` | 6 novos perfis Layer 2/3 adicionados (k8s-helm, terraform-aws, data-pipeline-airflow, data-warehouse-dbt, soc2-baseline, lgpd-baseline) |
| `.github/workflows/ci.yml` | Agora gerado por linguagem via `--infra`; não sobrescreve CI customizado |
| `.github/templates/` | Novos templates para python-fastapi, python-flask, typescript-next |
| `docs/PROFILE-GUIDE-*.md` | Novo ficheiro gerado automaticamente após `--compose` |
| `.vscode/tasks.json` | Novo ficheiro gerado pelo scaffold (ausente em v1.2.0) |
| `.vscode/launch.json` | Novo ficheiro gerado pelo scaffold (ausente em v1.2.0) |
| `scripts/lib/composer.py` | Novo módulo — não afecta projectos existentes directamente |

### Acções automáticas (`--upgrade`)

```bash
python scripts/scaffold.py --upgrade --target-dir ~/projecto/meu-servico
```

O `--upgrade` irá:
- ✅ Criar `.vscode/tasks.json` e `.vscode/launch.json` se ausentes
- ✅ Copiar novos assets SpecKit (novas skills, novos prompts de domínio)
- ✅ Regenerar `docs/PROFILE-GUIDE-*.md` com a nova estrutura

### Acções manuais

1. **Perfis novos (opt-in)** — Para usar k8s-helm, terraform-aws, etc.:

   ```bash
   python scripts/scaffold.py \
     --compose devops-programming,python-fastapi,k8s-helm,devops-security \
     --target-dir ~/projecto/meu-servico
   ```

2. **Artefactos de infra** — Para gerar CI/CD, Dockerfile e docker-compose actualizados:

   ```bash
   python scripts/scaffold.py --infra \
     --target-dir ~/projecto/meu-servico
   ```

   > ⚠️ Se já tiver `.github/workflows/ci.yml` ou `Dockerfile` customizados, o scaffold não os sobrescreverá. Use `--force` para substituir.

3. **`docs/COMPATIBILITY-MATRIX.md`** — Foi adicionado ao template. Não é gerado automaticamente no projecto destino; copie manualmente se quiser o documento de referência:

   ```bash
   cp ~/template/docs/COMPATIBILITY-MATRIX.md ~/projecto/meu-servico/docs/
   ```

---

## 6. Migrando de v1.3.0 para a próxima versão

> Esta secção será preenchida com as notas específicas quando a próxima versão for lançada via `make release`.

### Template de notas por versão futura

```markdown
## Migrando de vX.Y.Z para vA.B.C

### Novidades relevantes para projectos existentes
| Componente | O que mudou |
|-----------|-------------|
| ...       | ...         |

### Acções automáticas (`--upgrade`)
- ✅ ...

### Acções manuais
1. ...
```

---

## 7. Referência rápida de comandos

```bash
# Ver versão do scaffold
python scripts/scaffold.py --version   # (quando implementado)
grep SCAFFOLD_VERSION scripts/lib/config.py

# Ver perfis disponíveis
python scripts/scaffold.py --list-profiles

# Simular upgrade sem gravar
python scripts/scaffold.py --upgrade --dry-run \
  --target-dir ~/projecto/meu-servico

# Upgrade normal (preserva customizações)
python scripts/scaffold.py --upgrade \
  --target-dir ~/projecto/meu-servico

# Upgrade forçado (sobrescreve divergências)
python scripts/scaffold.py --upgrade --force \
  --target-dir ~/projecto/meu-servico

# Adicionar perfil novo a projecto existente
python scripts/scaffold.py \
  --compose PERFIL1,PERFIL2,PERFIL3 \
  --target-dir ~/projecto/meu-servico

# Verificar descritores (staleness + erros)
python scripts/scaffold.py --validate

# Gerar release do template
make release VERSION=x.y.z          # release completo
make release VERSION=x.y.z DRY_RUN=1  # simulação
```

---

## 8. Solução de problemas

### `.scaffold-state.yaml` não encontrado

```
❌ .scaffold-state.yaml não encontrado em /caminho/projecto
```

**Causa**: O projecto não foi criado com `scaffold.py --new`, ou o ficheiro foi removido.

**Solução**: Crie um `.scaffold-state.yaml` mínimo manualmente:

```yaml
scaffold_version: "1.0.0"
created_at: "2026-01-01T00:00:00Z"
project:
  name: meu-projecto
  domain: programming   # programming | infrastructure | analysis
  language: python      # python | typescript | go | other
  github_repo: ""
profiles_applied: []
paths:
  target_dir: /caminho/projecto
  shared_dir: ~/Documentos/DevOps/.copilot-shared
```

### Ficheiro customizado sobrescrito por engano

```bash
# Recuperar versão antes do --force
git checkout HEAD -- caminho/do/ficheiro.yml
# Ou ver o diff e reaplicar customizações sobre o novo template
git show HEAD:caminho/do/ficheiro.yml > /tmp/antigo.yml
diff /tmp/antigo.yml caminho/do/ficheiro.yml
```

### Descriptor marcado como stale no CI

```
::warning file=profile-descriptors/python-fastapi.yaml::
  Descriptor "python-fastapi" está desatualizado (last_tested > 90 dias)
```

**Causa**: O campo `last_tested`/`LAST_TESTED_DATE` no descriptor tem mais de 90 dias.

**Solução**: Testar o perfil e actualizar a data no ficheiro YAML:

```yaml
# profile-descriptors/python-fastapi.yaml
LAST_TESTED_DATE: "2026-03-14"   # actualizado após validação
```

### Conflito de perfis na composição

```
❌ Conflito de perfis: devops-programming e devops-infrastructure não podem ser usados juntos
```

**Causa**: Os perfis têm `excludes_with` mútuo — são alternativos, não complementares.

**Solução**: Escolha apenas um dos perfis core. Consulte a [Matriz de Compatibilidade](COMPATIBILITY-MATRIX.md) para combinações válidas.
