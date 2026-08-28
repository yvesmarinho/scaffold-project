---
title: "Copilot Arquitetura de Software framework minimo"
source: "https://github.com/copilot/c/6cf7fc3c-b8c4-4abf-9a42-0639e5a10a7f"
author:
published:
created: 2026-05-19
modificado: 2026-07-01 15:40
description: "GitHub is where people build software. More than 150 million people use GitHub to discover, fork, and contribute to over 420 million projects."
tags:
  - "clippings"
  - "grill-me"
---
Sim: **existe um padrão mínimo, prático e especificável** que você pode adotar para aumentar bastante a qualidade do software e reduzir a probabilidade de erros, **sem precisar dominar arquitetura avançada logo no início**.

Para o seu contexto, eu recomendo definir um **padrão arquitetural mínimo “profissional e sustentável”**, composto por:

1. **Arquitetura em camadas simples**
2. **Separação por responsabilidades**
3. **Contratos claros entre módulos**
4. **Validação forte de entradas**
5. **Testes automatizados por camada**
6. **Observabilidade básica com logs estruturados**
7. **Configuração externa e segura**
8. **Especificação orientada a fluxo e critérios de aceite**

No seu caso, para o projeto `portfolio-generator`, isso é muito mais importante do que tentar aplicar “todos os patterns” de uma vez.

---

## Resposta curta

Se você quer um **mínimo padrão de arquitetura** para software com boa qualidade, baixa chance de erro e boa manutenção, especifique isto:

- **Arquitetura Hexagonal simplificada** ou **Camadas + Casos de Uso**
- **DDD leve** apenas para modelar domínio e linguagem
- **SOLID como critério de revisão**, não como obsessão
- **TDD para partes críticas**
- **GoF apenas quando houver problema real que justifique**
- **Contratos de entrada/saída com schemas e validação**
- **Testes unitários + integração + CLI**
- **Logs estruturados**
- **Configuração por arquivos e variáveis**
- **Lint, typing e coverage obrigatórios no CI**

Se quiser algo objetivo para pôr na especificação:  
**“Adotar arquitetura em camadas com Application, Domain e Infrastructure, seguindo DDD leve, SOLID, validação de contratos, testes automatizados e observabilidade por logs estruturados.”**

---

## O que é o “mínimo viável de arquitetura” para reduzir erros?

Quando alguém fala em “arquitetura”, muita gente imagina microservices, event-driven, mensageria, CQRS e coisas complexas.  
**Você não precisa começar por isso.**

O mínimo que realmente reduz erro é:

## 1\. Separar o sistema em partes com responsabilidades claras

Exemplo:

- **CLI**: recebe comandos e opções do usuário
- **Application / Use Cases**: orquestra o fluxo
- **Domain**: regras centrais do negócio
- **Infrastructure**: filesystem, Git, parsers, JSON, APIs externas
- **Tests**: validam cada camada

Isso sozinho já reduz:

- acoplamento
- duplicação
- efeitos colaterais
- dificuldade de testes
- risco de regressão

---

## 2\. Impedir que regra de negócio fique espalhada

No seu projeto, a regra principal não é “ler arquivos”.  
A regra principal é algo como:

- o que é um “projeto”
- quando um diretório pode ser catalogado
- como classificar tecnologia
- como inferir resumo
- como medir qualidade
- quando usar IA opcionalmente
- como serializar isso num JSON válido

Essas decisões precisam ficar em um **núcleo de domínio**, não espalhadas entre CLI, parser, Git e output.

---

## 3\. Definir contratos de entrada e saída

Erros aparecem muito quando módulos “adivinham” formatos.

Você deve especificar:

- formato do input da CLI
- formato dos objetos internos
- schema do JSON final
- estrutura dos metadados extraídos
- estrutura dos erros
- comportamento em caso de falha parcial

Isso é arquitetura também.

---

## O melhor padrão mínimo para você

Para seu cenário, eu recomendo:

## Arquitetura em Camadas + DDD Leve + Ports and Adapters simplificado

Isso parece sofisticado, mas na prática significa algo simples.

## Estrutura conceitual

### 1\. Presentation Layer

Interface de entrada e saída.

No seu caso:

- `click`
- `rich`
- mensagens de terminal
- progress bar
- tratamento amigável de erro

### 2\. Application Layer

Casos de uso.

Exemplos:

- `scan_projects`
- `extract_project_metadata`
- `generate_portfolio`
- `export_portfolio_json`
- `summarize_project`

Essa camada coordena o fluxo, mas **não deveria saber detalhes de GitPython, tree-sitter ou OpenAI**.

### 3\. Domain Layer

Regras e modelos centrais.

Exemplos:

- entidade `Project`
- entidade `Portfolio`
- value objects como `ProjectPath`, `GitMetadata`, `TechnologyStack`
- regras como:
	- “nunca processar fora de `/home/yves_marinho/Documentos/DevOps/` ”
		- “README prioritário sobre IA”
		- “se README for ausente, gerar resumo por fallback”
		- “projeto inválido deve ser marcado e não quebrar a execução global”

### 4\. Infrastructure Layer

Implementações concretas.

Exemplos:

- leitor de arquivos
- parser de README
- Git metadata collector
- detector de linguagens
- exportador JSON
- cliente opcional de IA
- providers de config

---

## Por que isso é melhor do que tentar “DDD completo”?

Porque **DDD completo exige maturidade de modelagem**, linguagem ubíqua, bounded contexts, context maps etc.

Para seu projeto, o melhor é **DDD leve**, ou seja:

- modelar bem o problema
- nomear bem as coisas
- separar entidades, serviços e regras
- evitar lógica de domínio em adapters

Isso já entrega muito valor.

---

## Como SOLID entra nisso de forma útil

SOLID não deve virar religião.  
Ele deve ser usado como **filtro de qualidade**.

## S — Single Responsibility Principle

Cada módulo faz uma coisa principal.

Exemplo ruim:

- um arquivo que escaneia diretório, lê README, faz inferência, chama Git, exporta JSON e imprime no terminal

Exemplo bom:

- scanner
- readme analyzer
- git collector
- summary service
- json exporter

## O — Open/Closed Principle

Você quer poder adicionar novas estratégias sem reescrever tudo.

Exemplo:

- hoje exporta JSON
- amanhã exporta HTML ou Markdown

Use estratégia/interface.

## L — Liskov

Se você trocar uma implementação por outra, o comportamento contratual deve se manter.

Exemplo:

- `SummaryProvider`
	- `ReadmeSummaryProvider`
		- `AISummaryProvider`

Ambos devem retornar algo no mesmo contrato.

## I — Interface Segregation

Não criar interfaces gigantes.

## D — Dependency Inversion

Casos de uso dependem de abstrações, não de `GitPython` direto.

---

## Onde GoF realmente ajuda no seu caso

Você mencionou Factory. Sim, faz sentido, mas **não aplique pattern por vaidade**.

Patterns úteis para você:

## 1\. Factory

Para instanciar analisadores por tipo de projeto ou fonte.

Exemplos:

- `ProjectAnalyzerFactory`
- `SummaryProviderFactory`
- `ExporterFactory`

## 2\. Strategy

Muito útil no seu projeto.

Exemplos:

- estratégia de resumo:
	- por README
		- por heurística
		- por IA
- estratégia de detecção de stack
- estratégia de exportação

## 3\. Builder

Bom para montar objetos complexos como `ProjectMetadata`.

## 4\. Template Method

Pode ajudar em pipelines de análise com etapas padronizadas.

## 5\. Adapter

Ótimo para integrar libs externas sem contaminar o domínio.

Exemplo:

- adapter para `GitPython`
- adapter para `tree-sitter`
- adapter para `anthropic/openai`

## 6\. Facade

Muito útil para expor um serviço simples para a CLI.

Exemplo:

- `PortfolioGenerationFacade.generate(...)`

---

## O que eu NÃO recomendaria como padrão mínimo agora

Para seu caso, eu **não começaria** com:

- microservices
- event sourcing
- CQRS
- arquitetura orientada a eventos completa
- plugins excessivos desde o primeiro dia
- abstrações profundas demais
- genericismo exagerado
- “framework próprio” antes do produto existir

Isso adiciona complexidade antes de validar a ferramenta.

---

## Padrão mínimo de arquitetura que você pode escrever na especificação

Você pode colocar algo assim no `objetivo.yaml` ou em `spec.md`:

## Diretriz arquitetural recomendada

- Adotar **arquitetura em camadas**, separando:
	- **Presentation**: CLI e interface terminal
		- **Application**: casos de uso e orquestração
		- **Domain**: entidades, regras de negócio e contratos
		- **Infrastructure**: acesso a filesystem, Git, parsers, serialização e integrações externas
- Aplicar **DDD leve**, com foco em:
	- linguagem ubíqua
		- modelagem do domínio
		- isolamento das regras centrais
- Aplicar princípios **SOLID**
- Utilizar **Strategy**, **Factory**, **Adapter** e **Facade** quando agregarem clareza e extensibilidade
- Adotar **injeção de dependências simples**
- Toda integração externa deve ficar isolada em adapters/providers
- Todo fluxo principal deve ser representado por **casos de uso**
- Todo dado de entrada e saída deve possuir **validação explícita**
- Todo erro deve ser tratado com **falha controlada**, logging e retorno consistente
- Toda saída final deve obedecer a **schema versionado**

---

## Padrão de estrutura de projeto recomendado

Para o seu projeto, eu estruturaria assim:

```
portfolio-generator/
├── .github/
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
├── .git-hooks/
├── .specify/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── usage/
│   └── validation/
├── logs/
├── schemas/
│   └── portfolio-schema-v1.json
├── scripts/
├── src/
│   └── portfolio_generator/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── commands.py
│       │   └── presenters.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── dto/
│       │   ├── services/
│       │   └── use_cases/
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   ├── value_objects/
│       │   ├── services/
│       │   ├── repositories/
│       │   └── rules/
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── filesystem/
│       │   ├── git/
│       │   ├── parsers/
│       │   ├── exporters/
│       │   ├── ai/
│       │   └── config/
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── enums.py
│       │   ├── exceptions.py
│       │   ├── logging.py
│       │   ├── validators.py
│       │   └── utils.py
│       └── main.py
├── test/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── e2e/
├── tmp/
├── pyproject.toml
├── README.md
└── objetivo.yaml
```

Isso já é um padrão muito bom e profissional.

---

## Como isso se traduz no seu domínio específico

Seu sistema tem um fluxo principal parecido com isto:

1. usuário executa CLI
2. CLI valida argumentos
3. caso de uso recebe diretório-base
4. regra de domínio valida se caminho está dentro de `/home/yves_marinho/Documentos/DevOps/`
5. scanner localiza projetos candidatos
6. extractor coleta:
	- nome
		- tipo
		- linguagens
		- dependências
		- Git metadata
		- estatísticas
7. analyzer lê README e produz resumo
8. fallback opcional de IA entra apenas se necessário
9. aggregator monta portfólio final
10. exporter valida no schema e salva JSON
11. presenter mostra relatório ao usuário
12. logger registra tudo

Perceba que isso naturalmente se encaixa em camadas.

---

## Qual padrão usar para “menor probabilidade de erro”?

Se o objetivo é **reduzir erro**, os pilares mais fortes são estes:

## 1\. Design by Contract leve

Defina pré-condições, pós-condições e invariantes.

Exemplos:

- entrada não pode ser vazia
- path deve existir
- path deve estar dentro do diretório permitido
- JSON final deve bater com schema
- se projeto falhar, erro deve ser agregado, não derrubar toda a execução

## 2\. Fail-safe / graceful degradation

Se um projeto específico falhar:

- registrar erro
- marcar projeto como parcialmente analisado
- continuar os demais

## 3\. Idempotência

Rodar duas vezes não deve corromper dados.

## 4\. Determinismo quando possível

A mesma entrada deve produzir mesma saída, exceto dados temporais/Git dinâmicos.

## 5\. Testabilidade

Toda regra importante deve ser fácil de testar sem filesystem real ou API real.

---

## O mínimo de documentação arquitetural que vale a pena ter

Você não precisa escrever um tratado.  
Mas vale muito ter estes documentos:

## 1\. docs/architecture/overview.md

- objetivo
- escopo
- camadas
- fluxo principal
- decisões

## 2\. docs/architecture/domain-model.md

- entidades
- value objects
- serviços de domínio
- regras

## 3\. docs/decisions/adr-001-architecture.md

Uma ADR simples explicando:

- por que camadas
- por que DDD leve
- por que CLI + services + adapters
- por que evitar acoplamento direto

## 4\. docs/validation/quality-gates.md

- ruff
- pylint
- mypy/pyright
- pytest
- coverage
- schema validation

---

## Como especificar isso no Spec Drive Development

Como você usa especificação orientada a objetivo, recomendo que o padrão mínimo seja descrito em quatro níveis:

## 1\. Objetivo

O que o sistema precisa resolver.

## 2\. Restrições arquiteturais

Como ele deve ser construído.

## 3\. Critérios de qualidade

Como você mede se ficou bom.

## 4\. Critérios de aceite operacionais

Como você prova que funciona.

---

## Exemplo de especificação arquitetural mínima

Você pode adicionar algo como:

```
architecture:
  style: "Layered Architecture with Lightweight DDD and Ports/Adapters"
  layers:
    - presentation
    - application
    - domain
    - infrastructure
  principles:
    - SOLID
    - Separation of Concerns
    - Dependency Inversion
    - Fail Fast on invalid inputs
    - Graceful Degradation on partial analysis failures
  patterns:
    - Strategy
    - Factory
    - Adapter
    - Facade
  constraints:
    - "CLI layer must not contain business rules"
    - "Domain layer must not depend on click, rich, loguru, gitpython or AI SDKs"
    - "Infrastructure layer must implement domain/application contracts"
    - "Every external integration must be wrapped by adapters"
    - "Every exported JSON must be validated against a versioned schema"
    - "Any directory outside /home/yves_marinho/Documentos/DevOps/ must be rejected"
  quality_gates:
    - "ruff check ."
    - "pylint src/"
    - "pytest --cov=src --cov-fail-under=90"
    - "type checking required"
    - "documentation required for all public functions/classes"
```

Isso já seria uma excelente base.

---

## Minha recomendação objetiva para o seu caso

Se eu estivesse definindo o mínimo padrão para seu projeto, eu escreveria assim:

## Padrão arquitetural mínimo recomendado

**Arquitetura em camadas com DDD leve e Ports/Adapters simplificado.**

### Regras:

- **CLI não contém regra de negócio**
- **Regras do domínio ficam centralizadas**
- **Infraestrutura encapsula filesystem/Git/IA**
- **Casos de uso orquestram o fluxo**
- **Validações são obrigatórias**
- **Testes por camada são obrigatórios**
- **Logs estruturados são obrigatórios**
- **Saídas versionadas e validadas por schema**
- **Falhas parciais não derrubam a execução completa**

Esse é o melhor equilíbrio entre:

- qualidade
- simplicidade
- escalabilidade
- manutenção
- curva de aprendizado

---

## Sobre DDD, TDD e GoF no seu contexto

## DDD

Use **leve**.  
Bom para modelar:

- projeto
- portfólio
- metadados
- análise
- qualidade
- resumo
- classificação

## TDD

Use principalmente para:

- validators
- regras de path seguro
- classificação de projeto
- parser de README
- schema generation
- agregação de métricas

Não precisa fazer TDD dogmático em tudo.

## GoF

Use só quando clarificar a solução.  
Para você, os mais úteis são:

- Strategy
- Factory
- Adapter
- Facade
- Builder

## SOLID

Use como checklist de revisão de design.

---

## O que define “software com menor probabilidade de erro”?

Em ordem de impacto real:

1. **requisitos claros**
2. **boas fronteiras entre módulos**
3. **validação de entradas**
4. **testes automatizados**
5. **logs úteis**
6. **baixo acoplamento**
7. **contratos claros**
8. **simplicidade**
9. **tipagem**
10. **revisão técnica**

Arquitetura ajuda, mas **a maior redução de erros vem da combinação entre clareza + contratos + testes + isolamento de responsabilidades**.

---

## O maior erro que você pode cometer agora

É tentar especificar “arquitetura enterprise” demais logo no começo.

Exemplos de erro:

- abstrair tudo antes de ter necessidade
- criar dezenas de interfaces sem benefício
- usar patterns por estética
- misturar domínio com framework
- criar um monólito “organizado” mas com regras espalhadas
- querer resolver escalabilidade extrema antes do MVP

Seu projeto precisa de:

- robustez
- legibilidade
- extensão futura
- segurança operacional

Não precisa de complexidade ornamental.

---

## Minha opinião técnica direta

Para o seu contexto, **o padrão mínimo ideal** é:

> **Layered Architecture + DDD leve + Strategy/Factory/Adapter + TDD nas regras críticas + quality gates obrigatórios**

Isso é suficientemente profissional para:

- gerar software sustentável
- diminuir bugs
- facilitar testes
- permitir evolução
- manter curva de aprendizado controlada

Se você adotar isso com disciplina, já estará muito acima da média de muitos projetos reais.

---

## Recomendação de texto pronto para colocar na especificação

Você pode usar este texto:

```
minimum_architecture_standard:
  description: >
    O projeto deverá seguir arquitetura em camadas com abordagem de DDD leve,
    separando interface, casos de uso, domínio e infraestrutura, com foco em
    baixo acoplamento, alta coesão, validação de contratos e facilidade de testes.
  mandatory_rules:
    - "A camada CLI/presentation não deve conter regras de negócio"
    - "Os casos de uso devem orquestrar o fluxo principal da aplicação"
    - "As regras centrais devem residir na camada de domínio"
    - "Integrações externas devem ser encapsuladas em adapters"
    - "Toda entrada deve ser validada quanto a tipo, vazio e formato"
    - "Toda saída relevante deve possuir contrato ou schema"
    - "Falhas parciais devem ser tratadas sem interromper o processamento global"
    - "Logs estruturados devem registrar etapas críticas do fluxo"
    - "Testes unitários, integração e contrato são obrigatórios"
    - "Cobertura mínima deve ser de 90%"
    - "Lint, tipagem estática e documentação são obrigatórios"
```

---

## Ajuste importante ao que você pediu

Você disse que quer:

- `try/except` em todo código
- em caso de erro, funções/classes retornarem `False`
- validação de vazio e tipagem em tudo

Vou te dar uma opinião técnica honesta:  
**isso precisa ser refinado**, porque aplicado literalmente pode **piorar a arquitetura**.

## Problema 1: “toda função retornar False”

Isso pode:

- esconder erro real
- misturar retorno válido com retorno de falha
- dificultar debugging
- quebrar tipagem
- gerar código confuso

Melhor:

- funções de domínio e infraestrutura levantam **exceções específicas**
- camada de aplicação decide tratamento
- camada CLI converte em mensagem amigável
- apenas pontos de fronteira retornam status controlado se necessário

## Problema 2: try/except em tudo

Isso pode criar:

- swallowing de exceções
- logs duplicados
- perda de stack trace
- código poluído

Melhor:

- `try/except` nas **fronteiras**:
	- CLI
		- I/O
		- integração externa
		- serialização
		- entrypoints
- e em trechos onde há estratégia de recuperação

## Problema 3: validação de tipo em toda função/classe

Sim, isso é bom, mas faça com método:

- `pydantic`, `dataclasses`, validadores utilitários, factories, DTOs
- não `if isinstance` espalhado de forma caótica

---

## Recomendação melhor para suas regras de implementação

Ao invés de:

- “todo código em try/except”
- “toda função retorna False”

Eu recomendo especificar assim:

```
error_handling_standard:
  rules:
    - "Toda fronteira externa deve possuir tratamento explícito de exceções"
    - "Exceções devem ser tipadas e semanticamente nomeadas"
    - "Funções não devem retornar False como substituto genérico para erro, exceto em contratos explicitamente booleanos"
    - "Falhas recuperáveis devem ser registradas em log e propagadas de forma controlada"
    - "Falhas não recuperáveis devem abortar a operação atual com mensagem clara"
    - "Processamentos em lote devem registrar falhas por item sem interromper o lote inteiro, quando aplicável"
```

Isso é muito mais sólido arquiteturalmente.

---

## Conclusão final

**Sim, existe um padrão mínimo.**  
Para o seu caso, o melhor padrão mínimo é:

## Arquitetura em camadas + DDD leve + contratos fortes + testes + logs + quality gates

Se quiser o resumo mais objetivo possível:

- **Use camadas**
- **Modele o domínio**
- **Isole infraestrutura**
- **Orquestre por casos de uso**
- **Valide tudo**
- **Teste regras críticas**
- **Não esconda erros com `False` em tudo**
- **Use patterns com propósito**
- **Prefira simplicidade com disciplina**

---

Se você quiser, no próximo passo eu posso fazer uma destas três coisas:

1. **reescrever seu `objetivo-init.yaml` com uma seção completa de arquitetura mínima recomendada**
2. **gerar um `spec.md` técnico inicial já alinhado com Spec-Driven Development**
3. **propor a estrutura real de pastas e módulos Python do `portfolio-generator` com justificativa arquitetural detalhada**

Se quiser, eu também posso fazer os **3 em sequência**.

---

## Complemento — Resolução de lacunas (sessão /grill-me, 01/07/2026)

Este documento foi originalmente escrito com exemplos específicos do projeto `portfolio-generator`. Como `scaffold-project` é o scaffold genérico que gera outros projetos (via `objetivo-init-minimal.yaml`), as lacunas e ambiguidades abaixo foram interrogadas e resolvidas para que o conteúdo acima sirva de **framework mínimo reutilizável**, não apenas de estudo de caso.

### 1. Conflito: tratamento de erro (CLAUDE.md global x recomendação deste guia)

O guia recomenda **não** usar "try/except em tudo" + "retorno `False` genérico em erro". O `CLAUDE.md` global do usuário exige exatamente esse padrão em todo arquivo `.py`. Os dois estavam em conflito direto.

**Decisão:** híbrido por camada.
- `domain/` e `application/` levantam **exceções tipadas e nomeadas semanticamente** (nunca retornam `False` como substituto genérico de erro).
- `infrastructure/` (adapters, I/O, Git, parsers, exportadores, clientes de IA) e a camada `cli/presentation` aplicam `try/except` + log estruturado + retorno `False`, conforme o padrão global do `CLAUDE.md`.
- Isso preserva o padrão global do usuário exatamente nas bordas (onde ele existe para blindar efeitos colaterais), sem contaminar o núcleo de domínio com lógica de controle de erro genérica.

**Atualiza:** a seção "Ajuste importante ao que você pediu" e o bloco `error_handling_standard` — a regra "Funções não devem retornar False como substituto genérico para erro" **vale apenas para domain/application**; infra/CLI seguem `CLAUDE.md` literalmente.

### 2. Escopo: exemplos específicos do `portfolio-generator`

**Decisão:** generalizar com placeholders. Os exemplos concretos deste documento (paths fixos como `/home/yves_marinho/Documentos/DevOps/`, entidades `Project`/`Portfolio`) permanecem como **estudo de caso ilustrativo já aplicado**, mas ao instanciar o framework mínimo em um novo `objetivo.yaml` do scaffold, esses valores devem ser parametrizados como `{{PROJECT_NAME}}`, `{{ALLOWED_BASE_PATH}}`, `{{DOMAIN_ENTITY_*}}` etc. O framework mínimo em si (camadas, DDD leve, SOLID, patterns, quality gates) é agnóstico de projeto.

### 3. Cobertura mínima de testes

**Decisão:** 90% fixo e global — mantido exatamente como proposto no documento original (`pytest --cov=src --cov-fail-under=90`), sem diferenciação por camada. Todo projeto gerado pelo scaffold herda esse piso.

### 4. Provider de IA

**Decisão:** agnóstico de provider. O framework mínimo não fixa Anthropic, OpenAI ou qualquer outro. Toda integração de IA deve implementar uma interface comum (`SummaryProvider`, `AIClientPort` ou equivalente) via **Strategy/Adapter**, permitindo trocar de provider sem alterar domínio ou application. A escolha concreta de provider fica a critério de cada `objetivo.yaml`. Credenciais seguem sempre o padrão global de `.secrets/` (nunca hardcoded, nunca via `curl`).

### 5. Formato de ADR

**Decisão:** MADR simplificado. Todo `docs/decisions/adr-NNN-*.md` segue o formato reduzido: **Contexto → Decisão → Consequências → Alternativas consideradas**. Leve o suficiente para não virar burocracia, mas padronizado entre todos os projetos gerados pelo scaffold.

### 6. Type checker e quality gates no CI

**Decisão:** `mypy` como type checker padrão, com gates **bloqueantes** no CI (não apenas informativos). Pipeline mínimo obrigatório: `ruff check .` → `mypy` → `pytest --cov=src --cov-fail-under=90`. Falha em qualquer etapa impede merge.

### 7. Logging estruturado dentro do domain

O `CLAUDE.md` global exige `logging`/`config_logging()` em todo arquivo `.py`, mas este guia proíbe o domain de depender de bibliotecas de infraestrutura (incluindo loggers concretos).

**Decisão:** domain não loga. A camada `domain/` permanece livre de qualquer chamada a `logging`; ela apenas levanta exceções tipadas ou retorna objetos de resultado/evento. A camada `application/infrastructure` é responsável por capturar esses eventos/exceções e aplicar `config_logging()`/`logging.*` do padrão global nas bordas do sistema.

### 8. Versionamento de schema JSON de saída

**Decisão:** SemVer simples por nome de arquivo. Cada schema vive em `schemas/<dominio>-schema-v<major>.json` (ex.: `schemas/portfolio-schema-v1.json`), e todo JSON de saída carrega um campo obrigatório `"schema_version"`. Mudança breaking de contrato = novo arquivo com major version incrementado; mudanças aditivas/compatíveis não exigem novo arquivo.

---

### Resumo das regras adicionadas ao `minimum_architecture_standard`

```yaml
error_handling_standard:
  rules:
    - "Domain e Application levantam exceções tipadas; nunca retornam False como substituto genérico de erro"
    - "Infrastructure e CLI/presentation aplicam try/except + log estruturado + retorno False nas fronteiras, conforme padrão global do projeto"
    - "Domain layer não deve conter chamadas a logging; apenas Application/Infrastructure registram logs"
ai_integration_standard:
  rules:
    - "Nenhum provider de IA é fixado no framework mínimo; toda integração implementa uma interface Strategy/Adapter comum"
    - "Credenciais de IA seguem o padrão global de .secrets/, nunca hardcoded ou via curl"
documentation_standard:
  adr_format: "MADR simplificado (Contexto, Decisão, Consequências, Alternativas)"
quality_gates:
  - "ruff check ."
  - "mypy (gate bloqueante no CI)"
  - "pytest --cov=src --cov-fail-under=90 (gate bloqueante no CI)"
schema_versioning:
  pattern: "schemas/<dominio>-schema-v<major>.json"
  required_field: "schema_version no JSON de saída"
  rule: "Mudança breaking = novo arquivo com major version incrementado"
```

---

## Complemento — Change Request (CR) sem refazer o workflow SpecKit (01/07/2026)

Pergunta resolvida via `/grill-me`: como incorporar atualizações de escopo/requisito ao workflow Spec-Driven Development (`specify → clarify → plan → tasks → implement`) sem forçar um novo ciclo completo toda vez que surge uma mudança pequena.

### Árvore de decisão

O custo de "refazer o SpecKit" vem de rodar `specify + clarify + plan` do zero. Isso só é necessário quando a mudança afeta arquitetura ou modelo de domínio. Nos demais casos, `spec.md`/`plan.md`/`tasks.md` devem ser tratados como documentos vivos, editados em delta:

- **Cenário A — feature ativa, `tasks.md` ainda em andamento**: editar `spec.md` só se mudar critério de aceite (delta, não reescrita); adicionar a(s) task(s) nova(s) direto em `tasks.md`; rodar `/speckit.analyze` para checar consistência. Não recriar `plan.md` nem repetir `clarify`. **Não abre CR** — o próprio `tasks.md` já é o rastro de auditoria.
- **Cenário B — feature ativa, `tasks.md` já fechado/implementado**: editar `spec.md` em delta se necessário; rodar `/speckit.converge`, que compara o código real contra spec/plan/tasks e **anexa** apenas o trabalho faltante como novas tasks; `/speckit.implement` conclui o delta. **Abre CR**.
- **Cenário C — requisito pequeno sem feature ativa relacionada**: rodar `/speckit.specify` (cria ou atualiza spec a partir de linguagem natural); pular `/speckit.clarify` se não houver ambiguidade; pular replanejamento completo se a arquitetura não mudar (reaproveitar plan/constituição vigente); `/speckit.tasks` → `/speckit.implement`. Se for trivial (nível typo/config), é legítimo aplicar a mudança direto e só documentar a decisão. **Abre CR**.

### Processo de Change Request (inspirado no PMI, adaptado ao SpecKit)

Análogo ao bug-report (`docs/bugs/BUG-NNN-*.md`), toda mudança de escopo que **não** se encaixa no Cenário A deve gerar um Change Request:

- **Template**: [docs/templates/change_request-template.yaml](../templates/change_request-template.yaml)
- **Instâncias**: `docs/changes/CR-NNN-slug.yaml`
- **Campo central — `routing`**: registra `feature_ativa`, `tasks_md_state`, o `scenario` (A/B/C) resultante e a `recommended_action` (qual comando SpecKit rodar), evitando que a decisão fique implícita na cabeça de quem está mudando o código.
- **`impact_analysis`**: se `affects_architecture` ou `affects_domain_model` for `true`, o CR sinaliza que o atalho não se aplica — volta ao ciclo completo `specify→clarify→plan`.
- **Quando não usar CR**: mudanças dentro do Cenário A, onde `tasks.md` já cumpre o papel de rastro auditável.

```yaml
change_request_standard:
  when_required:
    - "Cenário B — mudança pós-implementação em feature já concluída"
    - "Cenário C — requisito novo sem feature ativa relacionada"
  when_not_required:
    - "Cenário A — feature ativa com tasks.md em andamento (tasks.md já é o rastro)"
  routing_fields:
    - "feature_ativa"
    - "tasks_md_state"
    - "scenario (A|B|C)"
    - "recommended_action"
  escalation_rule: "Se impact_analysis.affects_architecture ou affects_domain_model for true, refazer specify→clarify→plan completo"
```