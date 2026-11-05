<div align="center">

# SWE-AF

### Runtime de equipe autônoma de engenharia, desenvolvido sobre o [AgentField](https://github.com/Agent-Field/agentfield)

**Pronúncia:** _“swee-AF”_ (uma palavra)

[![Beta pública](https://img.shields.io/badge/status-public%20beta-0ea5e9?style=for-the-badge)](#)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Licença](https://img.shields.io/badge/License-Apache%202.0-16a34a?style=for-the-badge)](LICENSE)
[![Testes](https://img.shields.io/badge/Tests-make%20check-blue?style=for-the-badge)](.github/workflows/ci.yml)
[![Desenvolvido com AgentField](https://img.shields.io/badge/Built%20with-AgentField-0A66C2?style=for-the-badge)](https://github.com/Agent-Field/agentfield)
[![Mais projetos da Agent-Field](https://img.shields.io/badge/More_from-Agent--Field-111827?style=for-the-badge&logo=github)](https://github.com/Agent-Field)
![Desenvolvedor da comunidade WorldSpace](https://img.shields.io/badge/WorldSpace-Community%20Developer-111827?style=for-the-badge)
[![PR de exemplo](https://img.shields.io/badge/Example-PR%20%23179-ff6b35?style=for-the-badge&logo=github)](https://github.com/Agent-Field/agentfield/pull/179)

**Uma chamada de API → uma equipe completa de engenharia → código entregue.**

<p>
  <a href="#início-rápido">Início rápido</a> •
  <a href="#por-que-o-swe-af">Por que SWE-AF</a> •
  <a href="#em-ação">Em ação</a> •
  <a href="#controle-adaptativo-da-fábrica">Controle da fábrica</a> •
  <a href="#benchmark">Benchmark</a> •
  <a href="#modos-de-operação">Modos</a> •
  <a href="#referência-da-api">API</a> •
  <a href="docs/ARCHITECTURE.md">Arquitetura</a>
</p>

</div>

Uma chamada de API inicia uma equipe autônoma completa de engenharia — gerentes de produto, arquitetos, programadores, revisores e testadores — que define o escopo, desenvolve, adapta e entrega software complexo de ponta a ponta.
O SWE-AF é um primeiro passo rumo a **fábricas autônomas de engenharia de software**, escalando de objetivos simples até programas complexos com centenas ou milhares de chamadas a agentes.

<p align="center">
  <img src="assets/banner.jpg" alt="Banner da frota autônoma de engenharia do SWE-AF" width="100%" />
</p>

> **Status da tradução:** em andamento. Esta versão ainda não traduz todo o README original; a versão em inglês permanece em [`README.md`](README.md).

## Experiência com uma chamada

Acione o sistema com a CLI `af` (requer af ≥ 0.1.87). Ela transmite o progresso em tempo real e exibe o resultado:

```bash
af call swe-planner.build --in '{
  "goal": "Refatorar e fortalecer os fluxos de autenticação e cobrança",
  "repo_url": "https://github.com/user/my-project",
  "config": {
    "runtime": "claude_code",
    "models": { "default": "sonnet", "coder": "opus", "qa": "opus" },
    "enable_learning": true
  }
}'
```

Prefere HTTP diretamente? Acesse a API com `curl`:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Refatorar e fortalecer os fluxos de autenticação e cobrança",
    "repo_url": "https://github.com/user/my-project",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "sonnet",
        "coder": "opus",
        "qa": "opus"
      },
      "enable_learning": true
    }
  }
}
JSON
```

Substitua `models.default` e as chaves de função (`coder`, `qa`, `architect` etc.) por qualquer modelo compatível com o runtime escolhido.

## Modos de operação

O SWE-AF funciona de duas formas: pode receber um único repositório ou coordenar alterações em vários repositórios durante a mesma execução.

### Modo de repositório único

Este é o modo padrão. Informe `repo_url` (remoto) ou `repo_path` (local), e o SWE-AF cuida do restante:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Adicionar autenticação JWT",
      "repo_url": "https://github.com/user/my-project"
    }
  }'
```

### Modo de vários repositórios

Quando o trabalho envolve várias bases de código — por exemplo, um aplicativo principal e bibliotecas compartilhadas, subprojetos ou microsserviços dependentes — passe `config.repos` como uma lista com as respectivas funções:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Adicionar autenticação JWT na API e na biblioteca compartilhada",
      "config": {
        "repos": [
          {
            "repo_url": "https://github.com/org/main-app",
            "role": "primary"
          },
          {
            "repo_url": "https://github.com/org/shared-lib",
            "role": "dependency"
          }
        ],
        "runtime": "claude_code",
        "models": {
          "default": "sonnet"
        }
      }
    }
  }'
```

**Funções:**
- `primary` — Aplicação principal. As alterações nela orientam a execução; falhas impedem o avanço.
- `dependency` — Bibliotecas ou serviços alterados para dar suporte ao repositório principal. As falhas são registradas, mas não bloqueiam o processo.

**Casos de uso:**
- Aplicação principal e SDK ou biblioteca de utilitários compartilhada
- Subprojetos de um monorepo mantidos em repositórios separados
- Funcionalidade que abrange vários microsserviços (por exemplo, API e fila de tarefas)

## Destaque: build autônomo

Benchmark de um compilador de Python baseado em Rust, desenvolvido autonomamente:

| Métrica | CPython (subprocesso) | RustPython (SWE-AF) | Melhoria |
| --- | --- | --- | --- |
| Execução em regime estável | Referência (~19 ms) | Runtime otimizado em processo | **88,3x–602,3x mais rápido** |
| Média geométrica | 1,0x da referência | 253,8x | **253,8x** |
| Vazão máxima | ~52 operações/s | 31.807 operações/s | **~612x** |

<details>
<summary>Metodologia de medição</summary>

A comparação de vazão considera modelos de execução diferentes: inicialização de um subprocesso CPython (~19 ms por chamada → ~52 operações/s) versus um conjunto de interpretadores RustPython aquecidos e persistentes, executados em processo. Essa é a troca prática que o sistema busca otimizar: substituir invocações repetidas de subprocessos por um pool persistente para executar trechos curtos de código.

</details>

O registro de artefatos inclui **175 agentes autônomos rastreados** nas etapas de planejamento, programação, revisão, integração e verificação.

Mais detalhes: [`examples/llm-rust-python-compiler-sonnet/README.md`](examples/llm-rust-python-compiler-sonnet/README.md)

## Por que o SWE-AF

A maioria dos frameworks de agentes envolve um único ciclo de programação. O SWE-AF é uma fábrica de engenharia coordenada: agentes de planejamento, execução e governança trabalham como uma camada de controle que se adapta em tempo real.

- **Execução sensível à dificuldade** — tarefas simples avançam rapidamente; tarefas difíceis acionam adaptação mais profunda e replanejamento do DAG, em vez de tentativas repetidas sem mudança.
- **Arquitetura de fábrica** — não é apenas um invólucro para um agente. Agentes de planejamento, execução e governança formam uma camada de controle coordenada. A arquitetura codifica a estratégia de engenharia, não apenas os prompts (veja [The Atomic Unit of Intelligence](https://www.santoshkumarradha.com/writing/atomic-unit-of-intelligence)).
- **Vários modelos e provedores** — escolha modelos diferentes para cada função (`coder: opus`, `qa: haiku`). Compatível com Claude, OpenRouter, OpenAI e Google.
- **Aprendizado contínuo** — com `enable_learning=true`, convenções e padrões de falha descobertos no início são repassados às tarefas seguintes.
- **Paralelismo na escala de agentes** — o agendamento por dependências e os worktrees Git isolados permitem distribuir tarefas sem colisões entre branches.
- **Orquestração em escala de frota** — vários nós SWE-AF podem operar continuamente em paralelo via AgentField, executando milhares de chamadas de agentes em builds simultâneos.
- **Registro explícito de concessões** — quando o escopo é reduzido, a dívida técnica é classificada por tipo e gravidade e propagada às tarefas seguintes.
- **Confiabilidade em execuções longas** — checkpoints permitem retomar um build com `resume_build` após falhas ou interrupções.

## Em ação

[PR #179: Registro DID/VC do SDK Go](https://github.com/Agent-Field/agentfield/pull/179) — criado integralmente pelo SWE-AF (runtime Claude com modelos da categoria Haiku). Uma chamada de API, nenhum código escrito por humanos.

| Métrica | Valor |
| --- | ---: |
| Tarefas concluídas | 10/10 |
| Testes aprovados | 217 |
| Critérios de aceitação | 34/34 |
| Chamadas a agentes | 79 |
| Modelo | `claude-haiku-4-5` |
| **Custo total** | **US$ 19,23** |

