---
title: "GitHub Melhores práticas de atualização de repositórios"
source: "https://github.com/copilot/c/87a2182f-10eb-4cb3-9f8c-2de4717c9388"
author:
published:
created: 2026-05-17
description: "GitHub is where people build software. More than 150 million people use GitHub to discover, fork, and contribute to over 420 million projects."
tags:
  - "clippings"
---
A melhor prática **não é “consolidar todas as branches no `main` de uma vez”**, e sim **integrar mudanças ao `main` de forma controlada, auditável, reversível e com política de proteção**. Quando houve **perda de dados**, isso quase sempre aponta para problema de **processo**, não só de Git: merge sem revisão, force-push no `main`, rebase incorreto, branches longas demais, ausência de backup lógico, ou falta de proteção de branch.

## Resposta curta

Engenheiros de software normalmente consolidam branches no `main` usando este fluxo:

1. `main` sempre protegido e estável.
2. Todo trabalho sai de uma branch curta.
3. Integração volta por **Pull Request**, nunca por push direto.
4. PR passa por:
	- review,
		- CI,
		- testes,
		- checagens de conflito.
5. Merge usando uma estratégia definida:
	- **squash merge** para times que querem histórico limpo;
		- **merge commit** para preservar contexto;
		- **rebase and merge** só com disciplina alta.
6. Antes de mudanças perigosas:
	- tag/release,
		- backup,
		- plano de rollback.
7. `main` nunca recebe histórico “reescrito” sem extremo controle.

Se você teve perda de dados, a melhor prática é adotar **trunk-based development com branch protection forte** ou um **GitHub Flow bem disciplinado**.

---

## O que significa “consolidar todas as branches”

Tecnicamente, isso pode querer dizer coisas diferentes:

1. **Mesclar branches de feature no `main`**
	- caso normal do dia a dia.
2. **Trazer trabalho divergente de várias branches antigas para uma linha principal**
	- caso de limpeza/reorganização.
3. **Unificar branches que ficaram muito tempo separadas**
	- caso perigoso, porque conflitos acumulam.
4. **Substituir o `main` pelo conteúdo de outra branch**
	- quase sempre arriscado.

Quando alguém fala “consolidar tudo”, isso costuma ser um sinal amarelo. Em engenharia madura, o objetivo não é fazer uma “grande consolidação”, mas evitar que as branches se afastem demais.

---

## Melhor prática de verdade

## 1\. main deve ser sagrado

O `main` deve representar:

- estado mais confiável do sistema;
- código integrável;
- algo que pode ser versionado, publicado ou implantado;
- histórico rastreável.

### Regras usuais

- sem push direto no `main`;
- sem `force push` no `main`;
- PR obrigatório;
- CI obrigatório;
- ao menos 1 ou 2 aprovações;
- branch atualizada com `main` antes do merge;
- commits assinados, se o contexto exigir;
- tags para marcos importantes.

---

## 2\. Branches curtas e de vida curta

Quanto mais tempo uma branch vive, maior a chance de:

- conflito;
- regressão;
- perda de contexto;
- merge incorreto;
- exclusão acidental de código;
- duplicação de trabalho.

### Prática boa

- branch pequena;
- escopo único;
- merge rápido;
- sincronização frequente com `main`.

### Prática ruim

- branch gigante por semanas ou meses;
- “branch de integração” informal;
- várias pessoas empilhando commits em branch compartilhada sem controle;
- rebase tardio de branch muito antiga.

---

## 3\. Pull Request como unidade de integração

PR não é só burocracia. Ele serve para:

- revisar diff;
- identificar remoções indevidas;
- validar impacto;
- rodar testes;
- registrar decisão técnica;
- permitir rollback mais seguro.

### Um PR bom

- pequeno ou médio;
- objetivo claro;
- com descrição do que muda;
- com checklist de risco;
- com evidência de teste;
- com estratégia de rollback.

---

## Estratégias de merge: qual usar

## A. Squash merge

Junta todos os commits da branch em um único commit no `main`.

### Vantagens

- histórico limpo;
- fácil leitura;
- evita poluição de commits intermediários;
- bom para feature branches pequenas.

### Desvantagens

- perde granularidade da branch;
- pior para investigação detalhada da evolução interna.

### Quando usar

- times que valorizam histórico simples;
- maioria dos fluxos de produto/aplicação.

---

## B. Merge commit

Preserva a topologia da branch.

### Vantagens

- mantém contexto exato da integração;
- melhor para auditoria;
- útil em branches mais complexas.

### Desvantagens

- histórico mais “barulhento”;
- pode virar grafo confuso se usado sem disciplina.

### Quando usar

- times com necessidade de rastreabilidade maior;
- integrações maiores;
- projetos com várias linhas paralelas relevantes.

---

## C. Rebase and merge

Reaplica os commits da branch sobre o topo do `main`, sem merge commit.

### Vantagens

- histórico linear;
- mantém commits individuais.

### Desvantagens

- mais perigoso se a equipe não domina bem rebase;
- pode confundir autoria temporal;
- risco maior em branches compartilhadas.

### Quando usar

- equipe madura em Git;
- branches pessoais curtas;
- cultura forte de histórico linear.

---

## Minha recomendação prática

Para evitar novos problemas de perda de dados:

## Se o time é pequeno ou médio

Use:

- **GitHub Flow**
- branch curta por tarefa
- PR obrigatório
- **squash merge**
- `main` protegido
- sem force push no `main`

Isso resolve a maioria dos problemas organizacionais.

## Se há alta frequência de integração

Use:

- **trunk-based development**
- feature flags
- branches curtíssimas
- merges diários
- CI forte

Isso reduz divergência e evita “megaconsolidação”.

## Se o projeto tem releases longos e manutenção paralela

Use:

- `main`
- branches de release
- hotfix branch controlada
- PR para tudo

Mas ainda assim evite branches de feature muito longas.

---

## O que geralmente causa perda de dados em Git

Perda de dados real em Git é menos comum do que parece; muitas vezes os dados ainda existem no histórico. As causas comuns são:

## 1\. Force push

Exemplo conceitual:

- alguém reescreve histórico;
- commits deixam de ser referenciados;
- equipe acha que “sumiu tudo”.

## 2\. Rebase incorreto

- commits podem parecer desaparecer;
- squash/rebase mal feito pode omitir mudanças;
- resolução de conflito pode aceitar remoções erradas.

## 3\. Merge conflict resolvido incorretamente

- arquivo fica com versão errada;
- bloco de código é removido sem perceber;
- configuração crítica é sobrescrita.

## 4\. Branch antiga integrada tarde demais

- conflitos acumulados;
- código incompatível;
- chance maior de erro humano.

## 5\. Push direto no main

- sem review;
- sem CI;
- sem barreira organizacional.

## 6\. Problema de “dados” que na verdade não era Git

Às vezes a perda foi em:

- banco de dados;
- arquivos gerados;
- artefatos;
- secrets/configuração;
- volume Docker;
- storage externo.

Git protege código versionado, **não protege estado operacional**.

---

## Melhor prática para evitar perda de dados

## Camada 1 — Proteção de branch

No GitHub, configure no `main`:

- bloquear push direto;
- exigir PR;
- exigir status checks;
- exigir branch up-to-date antes de merge;
- exigir review;
- bloquear force push;
- bloquear delete da branch principal.

## Camada 2 — Estratégia de integração

- branches pequenas;
- merge frequente;
- PR pequeno;
- resolução de conflito com revisão cuidadosa;
- evitar branches antigas.

## Camada 3 — Recuperabilidade

- tags frequentes;
- releases;
- backup de banco e dados críticos;
- snapshots antes de migrações;
- plano de rollback por deploy.

## Camada 4 — Governança

- definir política única de merge;
- definir quando usar squash/merge/rebase;
- documentar fluxo;
- treinar o time.

---

## Fluxo recomendado para consolidação segura

Se você hoje tem várias branches e quer consolidar sem repetir problema:

## Opção segura

1. congelar merges temporariamente;
2. escolher o `main` atual como baseline;
3. levantar todas as branches ainda relevantes;
4. descartar branches obsoletas;
5. para cada branch relevante:
	- atualizar com `main`;
		- resolver conflitos;
		- validar testes;
		- abrir PR individual;
		- revisar;
		- mergear;
6. depois apagar branch já integrada;
7. criar tag de estabilização.

## O que não fazer

- mergear tudo “no braço” sem revisão;
- fazer um mega-merge de dezenas de branches;
- sobrescrever `main` com branch “mais completa”;
- usar force push para “arrumar rápido”.

---

## Política ideal para times profissionais

## Política mínima aceitável

- `main` protegida;
- PR obrigatório;
- CI obrigatório;
- backup fora do Git para dados;
- sem branch longa;
- sem force push no `main`.

## Política boa

- tudo da política mínima;
- templates de PR;
- CODEOWNERS;
- revisão obrigatória por domínio;
- deploy automatizado;
- feature flags;
- releases etiquetadas.

## Política excelente

- trunk-based development;
- observabilidade;
- rollback automatizado;
- ambiente de preview;
- banco com estratégia formal de migração e reversão;
- auditoria de mudanças.

---

## Quando usar merge, rebase ou cherry-pick

## Merge

Use para integração normal. É o padrão mais seguro para equipes.

## Rebase

Use para limpar branch pessoal antes do PR, com cuidado. Evite rebase em branch compartilhada.

## Cherry-pick

Use para portar correção específica. Não use como estratégia principal de consolidação.

---

## Se houve perda de dados, o que eu faria agora

## 1\. Parar mudanças destrutivas

- sem force push;
- sem rebase adicional;
- sem “tentar arrumar” às pressas.

## 2\. Preservar estado atual

- tag no estado atual;
- branch de recuperação;
- snapshot dos dados fora do Git.

## 3\. Identificar a natureza da perda

Perguntas:

- foi código versionado?
- foi arquivo removido?
- foi banco de dados?
- foi segredo/config?
- foi histórico reescrito?

## 4\. Investigar histórico

- reflog local;
- commits órfãos;
- PRs mergeados;
- branches remotas;
- tags;
- GitHub UI / compare.

## 5\. Só depois definir estratégia de consolidação

A resposta depende de:

- quantas branches existem;
- quanto divergiram;
- se há conflitos estruturais;
- se o problema foi no código ou nos dados operacionais.

---

## Melhor prática resumida por cenário

## Cenário 1 — Projeto comum de aplicação

**Melhor prática**:

- GitHub Flow
- feature branch curta
- PR
- squash merge
- `main` protegida

## Cenário 2 — Time muito ativo

**Melhor prática**:

- trunk-based development
- feature flags
- merges pequenos e constantes

## Cenário 3 — Muitas branches antigas acumuladas

**Melhor prática**:

- triagem primeiro
- integração branch por branch
- evitar big bang merge

## Cenário 4 — Houve perda de dados operacional

**Melhor prática**:

- separar problema de Git do problema de persistência
- Git para código, backup para dados
- processo de restore testado

---

## Minha opinião técnica

Se você quer a **melhor prática mais robusta e menos propensa a desastre**, eu recomendo:

- **`main` protegida**
- **nada de push direto**
- **PR obrigatório**
- **squash merge**
- **branches curtas**
- **integração diária**
- **tag antes de mudanças sensíveis**
- **backup real para banco/arquivos**
- **nunca tratar Git como sistema de backup de dados operacionais**

Se o repositório já teve incidente, eu subiria o nível de rigor imediatamente:

- branch protection,
- CODEOWNERS,
- CI obrigatória,
- revisão obrigatória,
- bloqueio de force push,
- política formal de merge.

---

## Recomendação objetiva para o seu caso

Pelo que você descreveu, **não tente consolidar tudo manualmente de uma vez no `main`**.

Faça assim:

1. proteja `main`;
2. congele integrações temporariamente;
3. catalogue quais branches ainda importam;
4. recupere o que foi perdido primeiro;
5. integre **uma branch por vez via PR**;
6. valide diff e teste em cada merge;
7. apague branches obsoletas;
8. documente uma política oficial de branching.

---

## Regra prática simples

Se precisar de uma regra única:

> **Toda mudança entra no `main` apenas por PR pequeno, revisado, testado e rastreável.**

Essa é a prática que mais reduz risco.

Se você quiser, eu posso ir para o próximo nível e te entregar uma resposta bem mais prática em um destes formatos:

1. **plano de recuperação do repositório após perda de dados**
2. **política de branching para o seu time**
3. **passo a passo Git/GitHub para consolidar branches com segurança**
4. **checklist de proteção do `main` no GitHub para o repositório `yvesmarinho/scaffold-project`**

Se quiser, eu também posso montar um **playbook completo de incident response Git** em português.