# Homologação — Enterprise Scaffold Project Template
**Data**: 2026-03-08
**Contexto**: IMPs 01–32 concluídas. 410 testes passando. Debate de homologação por perspectiva profissional.
**Referência do framework de skills**: [`docs/GitHub Copilot - Default Porject Template Skills.md`](../GitHub%20Copilot%20-%20Default%20Porject%20Template%20Skills.md)

---

## 1. Template Architect / Platform Tooling Engineer

**Veredicto: APROVADO com observações estruturais**

O que foi feito está correto na essência: core separado de plugins, layering declarativo (core → layer2 → layer3 → layer4 → transversal), motor de composição com rollback. O `profile-descriptor-schema.md` é o artefato mais valioso do projeto — cria o contrato que impede o template de virar monólito.

### Pontos fortes
- Separação `scripts/lib/` por responsabilidade (composer, config, templates, validate...) — cada módulo tem uma função. Sem God Object.
- `ProfileComposer` com rollback em caso de erro parcial: isso é nível production.
- `.scaffold-state.yaml` persistindo estado do projeto gerado — permite `--upgrade` real, não só "re-executar cegamente".
- `--validate` em IMP-32 fecha o loop: agora o template valida a si mesmo antes de CI falhar.

### Alertas
- `scaffold.py` já tem ~900 linhas. Está no limite do "aceitável para um entry point". O próximo perfil Layer 2 provavelmente vai forçar `flow_compose_profiles` a crescer além do que deve. **Recomendação**: extrair `flow_*.py` para `scripts/lib/flows/` antes de adicionar mais 3 perfis.
- `TEMPLATE-VERSIONS.md` está desatualizado — ainda lista k8s-helm e terraform-aws como "planejados" quando já foram implementados em IMP-22/23. Sinal de que governança documental está ficando para trás do código.
- Não existe um `scaffold.py --new-profile` para scaffoldar um novo descriptor. O crescimento de perfis ainda é manual — risco de inconsistência de schema.

---

## 2. DevEx / CLI Engineer

**Veredicto: APROVADO — melhor CLI do projeto**

A ergonomia do CLI está genuinamente boa. `--dry-run --json`, `--list-profiles --json`, `--validate --json` — o pattern de "toda ação tem saída estruturada para CI" foi respeitado em todas as IMPs.

### Pontos fortes
- Modo `--ci` vs. interativo bem separado. Não há "prompt que bloqueia automação".
- `--config FILE` (YAML) para projetos infra/GitOps onde ninguém quer digitar flags. Decisão madura.
- `--dry-run` retorna manifesto de operações com step + op + path + desc — exatamente o que um dev precisa para revisar antes de commitar.
- Rich console com tabelas estruturadas, sem poluir `--json`. Tratamento de `stderr` vs `stdout` em modo JSON (IMP-28).

### Alertas
- `--help` hoje tem 2 grupos (`ações`, `modo`, `campos do projeto`) mas mistura "ações de template" com "flags de comportamento". Um `--publish` e um `--validate` são fundamentalmente diferentes de `--dry-run`. Considerar subcomandos (`scaffold compose`, `scaffold validate`, `scaffold publish`) na próxima versão MAJOR.
- Não há `--version` com componentes granular (template version + scaffold version separados). O `SCAFFOLD_VERSION` não reflete a versão do perfil ativo.
- Ausência de `--help` por subfluxo: `scaffold.py --compose --help` seria útil.

---

## 3. SRE / Infra Generalist

**Veredicto: APROVADO PARCIALMENTE — baseline sólido, staleness é risco real**

O template gera CI/CD, Dockerfile, docker-compose, runbook — tudo que um projeto precisa para "funcionar em produção" no dia 1. A cobertura de linguagens (Python/Node/Go) no `infra.py` é suficiente para 90% dos casos.

### Pontos fortes
- Dockerfile multistage em todos os Layer 2 (python-fastapi, python-flask, typescript-next): non-root user, `uv sync --frozen --no-dev`, node:20-slim. Não é template de tutorial — é produção.
- `--upgrade` com `.scaffold-state.yaml` resolve o problema real de "o projeto foi gerado há 6 meses, o template evoluiu, como atualizo sem sobrescrever customizações?". Poucas ferramentas fazem isso.
- `ci-template.yml` (IMP-31) com matrix 3.10/3.11/3.12 e job de lint YAML: o template testa a si mesmo.

### Alertas
- `LAST_TESTED_DATE: "2026-03-07"` nos descritores não é atualizado automaticamente. Em 90 dias isso começa a mentir. Falta um job no CI que execute `--validate` e alerte sobre descriptors com data > 90 dias (staleness check estava previsto no schema mas não foi implementado).
- Não há `healthcheck` padronizado no `generates.files` dos perfis Layer 2 — cada um define à sua maneira. Para SRE consumir, isso deveria ser um campo `observability.healthcheck_path` no schema.
- O `RUNBOOK.md` gerado por `infra.py` é um template genérico. Não tem substituição de variáveis por perfil. Um projeto k8s-helm deveria ter runbook com comandos `helm rollback`, não só "verifique os logs".

---

## 4. AppSec / Security Engineer

**Veredicto: APROVADO — melhor compliance da categoria "template OSS"**

Layer 4 com `lgpd-baseline` e `soc2-baseline` é inesperadamente completo para um template de projeto. A maioria dos templates open source nem menciona LGPD. Ter isso como perfil composável (não hardcoded) é a decisão certa.

### Pontos fortes
- `.secrets/` no `.gitignore` verificado em toda sessão via copilot-instructions. P0 de segurança cumprido.
- `security.enforces` nos descriptors é auditável: dá para gerar um security checklist por projeto a partir dos perfis aplicados.
- `bandit` + `pip-audit` no Makefile de todos os perfis Python. `pnpm audit` no TypeScript. Não é cosmético.
- Layer 4 compliance como overlay: LGPD não polui o Layer 2. Composição limpa.

### Alertas
- O campo `security.enforces` é uma lista de strings livres. Para auditoria real, precisa ser estruturado: `{control: "CC6.1", description: "...", tool: "trivy", severity: "high"}`. Hoje não dá pra automação consumir — só humano.
- Não há `SBOM` (Software Bill of Materials) gerado por nenhum perfil. SOC 2 CC8 (Change Management) exige rastreabilidade de dependências. `cyclonedx-bom` ou `syft` deveriam estar no CI dos perfis Layer 2.
- `devops-security` é referenciado em vários `combines_with` mas não existe como descriptor no repositório. É um "perfil fantasma" — 9 warnings em `--validate`. Isso precisa ser resolvido: ou criar o descriptor, ou remover as referências.

---

## 5. Technical Writer / Docs Engineer

**Veredicto: APROVADO COM RESSALVAS — documentação rica mas fragmentada**

A cobertura documental é invulgar para um projeto pessoal: SESSION_REPORT, DAILY_ACTIVITIES, INDEX, TODO, COMPATIBILITY-MATRIX, DEPRECATION-POLICY, PROFILE-DESCRIPTOR-SCHEMA. Mostra maturidade de processo.

### Pontos fortes
- `generate_profile_guide()` (IMP-29) é o feature mais valioso para o usuário final do template: ao aplicar perfis, recebe um documento específico para aquela combinação. Não encontrado em nenhum scaffolder equivalente.
- `docs/copilot/` com análise de domínio, decisões de design e estratégia de perfis: serve como "Architecture Decision Record" orgânico.
- Padrão de sessão (SESSION_RECOVERY, DAILY_ACTIVITIES, SESSION_REPORT) funciona como changelog de decisões — útil quando o mantenedor é uma pessoa só.

### Alertas
- `TEMPLATE-VERSIONS.md` desatualizado (confirmado pelo Template Architect acima). Documento importante que perdeu sincronia com a realidade.
- Não há `GETTING-STARTED.md` ou `QUICKSTART` de 5 minutos para um novo usuário. Todo o README assume que o leitor conhece o projeto. Barreira de entrada alta.
- `docs/PROFILE-GUIDE-{slug}.md` é gerado no projeto destino, mas não há nenhum exemplo no repositório do template em si. Um usuário novo não consegue ver como esse output parece antes de executar.
- A documentação das 9 sessões (SESSIONS/2026-01-27 a 2026-03-08) é valiosa internamente mas dificulta entender "o que o template faz hoje". Falta um sumário executivo do estado atual.

---

## 6. Release Maintainer / Librarian

**Veredicto: APROVADO — governança acima da média, com gaps identificados**

`CHANGELOG.md`, `COMPATIBILITY-MATRIX.md`, `DEPRECATION-POLICY.md`, `TEMPLATE-VERSIONS.md` e `--validate` são os quatro pilares de um template governado. Todos existem. Isso coloca o projeto significativamente acima do padrão.

### Pontos fortes
- `--publish` (IMP-30) com tarball + manifesto JSON é o que permite distribuição repetível do template. SHA-256 do tarball pode ser adicionado ao manifesto para verificação de integridade.
- `SCAFFOLD_VERSION = "1.0.0"` em `config.py` centraliza o versionamento.
- 410 testes com cobertura por IMP. Testabilidade do gerador em nível que permite regressão controlada.
- `ci-template.yml` com matrix de Python garante que o template não quebra silenciosamente com upgrade de runtime.

### Alertas
- **Gap crítico**: não existe `MIGRATION-GUIDE.md` nem processo de como um projeto gerado com v1.0.0 migra para v1.1.0. O `--upgrade` existe, mas não está documentado com "o que muda, o que precisa de ação manual".
- O CHANGELOG tem seção `[Unreleased]` com IMP-29, 30, 31, 32 — nunca foi "fechada" em uma versão. Na prática, o template está em perpetual pre-release. Falta um processo de `make release VERSION=1.1.0` que fecha o Unreleased, atualiza SCAFFOLD_VERSION e cria a git tag.
- `snapshot tests` (test_templates_snapshot.py) testam apenas 3 arquivos. Com 10 perfis e centenas de templates gerados, a cobertura de snapshot é baixa — regressões visuais de template podem passar despercebidas.

---

## Matriz de Homologação

| Dimensão | Status | Gap Crítico |
|---|---|---|
| Arquitetura do core | ✅ APROVADO | `scaffold.py` na borda do tamanho aceitável |
| CLI / DevEx | ✅ APROVADO | Sem subcomandos — crescimento vai cobrar |
| Baseline infra/SRE | ✅ PARCIAL | Staleness check e runbook parametrizado |
| Segurança / Compliance | ✅ APROVADO | `devops-security` fantasma; `security.enforces` não-estruturado |
| Documentação | ⚠️ RESSALVAS | `TEMPLATE-VERSIONS.md` desatualizado; sem QUICKSTART |
| Governança / Release | ⚠️ RESSALVAS | Sem processo de release; sem migration guide |

---

## Próximas IMPs recomendadas pelo debate

> **Plano de ação completo com escopo, esforço e prioridade**: [`docs/TODO.md` — seção "Plano de Ação Pós-Homologação"](../../TODO.md)

| IMP | Título | Prioridade | Origem |
|---|---|---|---|
| **IMP-33** | `devops-security.yaml` + `TEMPLATE-VERSIONS.md` atualizado | P0 | Template Arch • AppSec • Release |
| **IMP-34** | `QUICKSTART.md` + exemplo de output de `generate_profile_guide()` | P0 | Docs |
| **IMP-35** | Processo de release: `make release VERSION=x.y.z` | P1 | Release |
| **IMP-36** | Staleness check no CI (descriptors > 90 dias) | P1 | SRE |
| **IMP-37** | `MIGRATION-GUIDE.md` | P1 | Release |
| **IMP-38** | Refactor `scaffold.py` → `scripts/lib/flows/` | P2 | Template Arch |
| **IMP-39** | Ampliar snapshot tests (todos os 10 perfis) | P2 | Release |
| **IMP-40** | `RUNBOOK.md` parametrizado por perfil | P2 | SRE |
| **IMP-41** | `security.enforces` estruturado por controle | P3 | AppSec |
| **IMP-42** | SBOM nos perfis Layer 2 | P3 | AppSec |
| **IMP-43** | `scaffold.py --new-profile` scaffolder de descriptors | P3 | Template Arch |
| **IMP-44** | Subcomandos CLI (versão MAJOR — breaking change) | P3 | DevEx |
