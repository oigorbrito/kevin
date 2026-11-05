<div align="center">

# SWE-AF

### Runtime da equipe de engenharia autônoma construído em [AgentField](https://github.com/Agent-Field/agentfield)

**Pronunciado:** _"swee-AF"_ (uma palavra)

[![Beta público](https://img.shields.io/badge/status-public%20beta-0ea5e9?style=for-the-badge)](#)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Licença](https://img.shields.io/badge/License-Apache%202.0-16a34a?style=for-the-badge)](LICENSE)
[![Testes](https://img.shields.io/badge/Tests-make%20check-blue?style=for-the-badge)](.github/workflows/ci.yml)
[![Construído com AgentField](https://img.shields.io/badge/Built%20with-AgentField-0A66C2?style=for-the-badge)](https://github.com/Agent-Field/agentfield)
[![Mais do campo do agente](https://img.shields.io/badge/More_from-Agent--Field-111827?style=for-the-badge&logo=github)](https://github.com/Agent-Field)
![Desenvolvedor da comunidade WorldSpace](https://img.shields.io/badge/WorldSpace-Community%20Developer-111827?style=for-the-badge)
[![Exemplo PR](https://img.shields.io/badge/Example-PR%20%23179-ff6b35?style=for-the-badge&logo=github)](https://github.com/Agent-Field/agentfield/pull/179)

**Uma chamada de API → equipe completa de engenharia → código enviado.**

[English](README.md) | **Português (Brasil)**

<p>
<a href="#início-rápido">Início rápido</a> •
<a href="#por-que-swe-af">Por que SWE-AF</a> •
<a href="#em-ação">Em ação</a> •
<a href="#controle-adaptativo-de-fábrica">Controle de fábrica</a> •
<a href="#benchmark">Referência</a> •
<a href="#modos-de-operação">Modos</a> •
<a href="#referência-de-api">API</a> •
<a href="docs/ARCHITECTURE.md">Arquitetura</a>
</p>

</div>

Uma chamada de API cria uma equipe de engenharia totalmente autônoma – gerentes de produto, arquitetos, codificadores, revisores, testadores – que define o escopo, constrói, adapta e envia software complexo de ponta a ponta.
O SWE-AF é o primeiro passo em direção a **fábricas autônomas de engenharia de software**, que vão desde objetivos simples até programas complexos com vários problemas, com centenas a milhares de invocações de agentes.

<p align="center">
<img src="assets/banner.jpg" alt="Banner da frota de engenharia autônoma SWE-AF" width="100%" />
</p>

## DX de uma chamada

Acione-o com a CLI `af` (requer af ≥ 0.1.87) — ele transmite o progresso ao vivo e imprime o resultado:

```bash
af call swe-planner.build --in '{
  "goal": "Refactor and harden auth + billing flows",
  "repo_url": "https://github.com/user/my-project",
  "config": {
    "runtime": "claude_code",
    "models": { "default": "sonnet", "coder": "opus", "qa": "opus" },
    "enable_learning": true
  }
}'
```

Prefere HTTP bruto? Acesse a API diretamente com curl:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Refactor and harden auth + billing flows",
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

Troque `models.default` e qualquer chave de função (`coder`, `qa`, `architect`, etc.) para qualquer modelo compatível com seu tempo de execução.

## Modos de operação

O SWE-AF funciona em dois modos: apontar para um único repositório ou orquestrar alterações coordenadas em vários repositórios em uma única compilação.

### Modo de repositório único

O padrão. Passe `repo_url` (remoto) ou `repo_path` (local) e o SWE-AF cuida de tudo:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Add JWT auth",
      "repo_url": "https://github.com/user/my-project"
    }
  }'
```

### Modo Multi-Repositório

Quando seu trabalho abrange várias bases de código — um aplicativo primário mais bibliotecas compartilhadas, subprojetos monorepo ou microsserviços dependentes — passe `config.repos` como uma matriz com funções:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Add JWT auth across API and shared-lib",
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
- `primary` — O aplicativo principal. As mudanças aqui impulsionam a construção; falhas bloqueiam o progresso.
- `dependency` — Bibliotecas ou serviços modificados para oferecer suporte ao repositório primário. As falhas são capturadas, mas não bloqueadas.

**Casos de uso:**
- Aplicativo principal + SDK compartilhado ou biblioteca de utilitários
- Subprojetos Monorepo que vivem em repositórios separados
- Recurso que abrange vários microsserviços (por exemplo, API + fila de trabalho)

## Destaque de construção autônoma

Benchmark do compilador Python baseado em Rust (construído de forma autônoma):

| Métrica | CPython (subprocesso) | RustPython (SWE-AF) | Melhoria |
| ---------------------- | -------------------- | ---------------------------- | ----------------------- |
| Execução em estado estacionário | Linha de base (~19ms) | Runtime otimizado em processo | **88,3x-602,3x mais rápido** |
| Média geométrica | Linha de base 1,0x | 253,8x | **253,8x** |
| Capacidade máxima | ~52 operações/s | 31.807 operações/s | **~612x** |

<details>
<summary>Metodologia de medição</summary>

A comparação de taxa de transferência mede diferentes modelos de execução: geração de subprocesso CPython (~19ms por chamada → ~52 ops/s) vs pool de interpretadores pré-aquecidos RustPython (em processo). Esta é a compensação do mundo real que o sistema foi construído para otimizar – substituindo invocações repetidas de subprocessos por um pool persistente para execução de trechos curtos.

</details>

A trilha de artefatos inclui **175 agentes autônomos rastreados** em planejamento, codificação, revisão, mesclagem e verificação.

Detalhes: [`examples/llm-rust-python-compiler-sonnet/README.md`](examples/llm-rust-python-compiler-sonnet/README.md)

## Por que SWE-AF

A maioria das estruturas de agente envolve um único loop de codificador. SWE-AF é uma fábrica de engenharia coordenada – agentes de planejamento, execução e governança funcionam como uma pilha de controle que se adapta em tempo real.

- **Execução com reconhecimento de hardware** — problemas fáceis passam rapidamente, enquanto problemas difíceis desencadeiam uma adaptação mais profunda e replanejamento em nível de DAG em vez de novas tentativas cegas.
- **Arquitetura de fábrica** — não um wrapper de agente único. Os agentes de planejamento, execução e governança são executados como uma pilha de controle coordenada — a arquitetura codifica a estratégia de engenharia, não os prompts (consulte [A Unidade Atômica de Inteligência](https://www.santoshkumarradha.com/writing/atomic-unit-of-intelligence)).
- **Multimodelo, multiprovedor** — atribua diferentes modelos por função (`coder: opus`, `qa: haiku`). Funciona com Claude, OpenRouter, OpenAI e Google.
- **Aprendizado contínuo** — com `enable_learning=true`, convenções e padrões de falha descobertos antecipadamente são injetados em problemas posteriores.
- **Paralelismo em escala de agente** — agendamento em nível de dependência + árvores de trabalho git isoladas permitem grande distribuição sem colisões de ramificação.
- **Orquestração em escala de frota** — muitos nós SWE-AF podem ser executados continuamente em paralelo por meio do AgentField, gerando milhares de invocações de agentes em compilações simultâneas.
- **Acompanhamento explícito de compromissos** — quando o escopo é relaxado, a dívida é digitada, avaliada por gravidade e propagada.
- **Confiabilidade de longo prazo** — a execução com pontos de verificação suporta `resume_build` após falhas ou interrupções.

## Em ação

[PR #179: Registro Go SDK DID/VC](https://github.com/Agent-Field/agentfield/pull/179) — construído inteiramente por SWE-AF (tempo de execução de Claude com modelos de classe haiku). Uma chamada de API, zero código humano.

| Métrica | Valor |
| ------------------- | ------------------ |
| Problemas concluídos | 10/10 |
| Aprovação nos testes | 217 |
| Critérios de aceitação | 34/34 |
| Invocações de agente | 79 |
| Modelo | `claude-haiku-4-5` |
| **Custo total** | **US$ 19,23** |

<details>
<summary>Detalhamento dos custos por função do agente</summary>

| Função | Custo | % |
| ---------------------------------- | ----- | ----- |
| Codificador | US$ 5,88 | 30,6% |
| Revisor de código | US$ 3,48 | 18,1% |
| Controle de qualidade | US$ 1,78 | 9,2% |
| GitHub PR | US$ 1,66 | 8,6% |
| Testador de Integração | US$ 1,59 | 8,3% |
| Fusão | US$ 1,22 | 6,3% |
| Operações de espaço de trabalho | US$ 1,77 | 9,2% |
| Planejamento (PM + Arch + TL + Sprint) | US$ 0,79 | 4,1% |
| Verificador + Finalização | US$ 0,34 | 1,8% |
| Sintetizador | US$ 0,05 | 0,2% |

79 invocações, 2.070 conversas. Escopo e decomposição dos agentes de planejamento; os codificadores trabalham em árvores de trabalho paralelas e isoladas; revisores e controle de qualidade validam cada edição; fusão integra filiais; o verificador verifica os critérios de aceitação em relação ao PRD.

</details>

**Modelos Claude, de código aberto e Codex suportados**: Execute compilações com qualquer tempo de execução e ajuste modelos por função em um mapa de configuração simples.
- `runtime: "claude_code"` mapeia para o backend do Claude.
- `runtime: "open_code"` mapeia para backend OpenCode (IDs de modelo OpenRouter/OpenAI/Google/Anthropic).
- `runtime: "codex"` mapeia para o backend OpenAI Codex CLI.

## Controle Adaptativo de Fábrica

SWE-AF usa três loops de controle aninhados para se adaptar à dificuldade da tarefa em tempo real:

| Laço | Escopo | Gatilho | Ação |
| ----------- | ------------- | -------------------- | ---------------------------------------------------------------------------------- |
| Laço interno | Problema único | Falha no controle de qualidade/revisão | Coder tenta novamente com feedback |
| Loop intermediário | Problema único | Loop interno esgotado | `run_issue_advisor` tenta novamente com uma nova abordagem, divide o trabalho ou aceita com dívida |
| Laço externo | DAG restante | Falhas escaladas | `run_replanner` reestrutura problemas e dependências restantes |

Este é o comportamento central do controlo da fábrica: os agentes de controlo supervisionam os agentes trabalhadores e remodelam continuamente o plano à medida que a realidade muda.

## Início rápido

### Instalar no AgentField (`af install`)

Já está executando um plano de controle [AgentField](https://github.com/Agent-Field/agentfield)? Instale o SWE-AF diretamente do GitHub — sem clone, sem configuração local do Python:

```bash
af install https://github.com/Agent-Field/SWE-AF
af run swe-planner
```

`af install` clona o repositório, provisiona um ambiente Python isolado e registra o nó `swe-planner` em seu plano de controle. No primeiro `af run`, você será solicitado a fornecer o segredo necessário — uma chave do provedor LLM (`ANTHROPIC_API_KEY` **ou** `OPENROUTER_API_KEY`) — que é armazenada criptografada e reutilizada em cada nó, portanto, você a insere apenas uma vez. (Adicione `GH_TOKEN` quando quiser compilações para clonar repositórios privados e abrir solicitações pull.) Em seguida, inicie uma compilação:

```bash
af call swe-planner.build --in '{"goal": "Add JWT auth", "repo_url": "https://github.com/user/my-repo"}'
```

Novo no AgentField? Instale o plano de controle primeiro com `curl -fsSL https://agentfield.ai/install.sh | bash` ou use as opções Ferroviária/local abaixo.

### Implantar no Railway (mais rápido)

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/agentfield-engineering-team)

Um clique implanta plano de controle SWE-AF + AgentField + PostgreSQL. Exatamente **uma** variável de ambiente é necessária no Railway — uma chave de provedor LLM:

- `OPENROUTER_API_KEY` — **recomendado, mais simples**. Uma chave, mais de 200 modelos abertos e proprietários. Com apenas este conjunto (sem `ANTHROPIC_API_KEY`, sem `SWE_DEFAULT_RUNTIME`), o SWE-AF seleciona automaticamente o tempo de execução `open_code` e padroniza cada função para `openrouter/deepseek/deepseek-v4-flash-0731` — nenhuma configuração adicional é necessária.
- *Alternativa:* `ANTHROPIC_API_KEY` ou `CLAUDE_CODE_OAUTH_TOKEN` de `claude setup-token` em [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (usa créditos de assinatura Pro/Max), para executar o tempo de execução `claude_code`.

Opcional:

- `GH_TOKEN` — token de acesso pessoal do GitHub com escopo `repo`. Necessário apenas para clonar repositórios **privados**, enviar ramificações e abrir solicitações pull; constrói contra repositórios públicos que funcionam sem ele.

Depois de implantado, acione uma compilação:

```bash
curl -X POST https://<control-plane>.up.railway.app/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -H "X-API-Key: this-is-a-secret" \
  -d '{"input": {"goal": "Add JWT auth", "repo_url": "https://github.com/user/my-repo"}}'
```

### 1. Requisitos (locais)

-Python 3.12+
- Plano de controle AgentField (`af`)
- Chave de API do provedor de IA (Anthropic, OpenRouter, OpenAI ou Google)

### 2. Instalar

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Executar

```bash
af                 # starts AgentField control plane on :8080
python -m swe_af   # registers node id "swe-planner"
```

### 4. Acione uma compilação

```bash
# Default (uses Claude)
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth to all API endpoints",
    "repo_url": "https://github.com/user/my-project"
  }
}
JSON

# With open-source runtime + flat role map
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth",
    "repo_url": "https://github.com/user/my-project",
    "config": {
      "runtime": "open_code",
      "models": {
        "default": "openrouter/minimax/minimax-m2.5"
      }
    }
  }
}
JSON

# With Codex CLI runtime
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth",
    "repo_url": "https://github.com/user/my-project",
    "config": {
      "runtime": "codex",
      "models": {
        "default": "gpt-5.3-codex"
      }
    }
  }
}
JSON

# Fast mode with Codex CLI runtime
curl -X POST http://localhost:8080/api/v1/execute/async/swe-fast.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add a focused bug fix",
    "repo_url": "https://github.com/user/my-project",
    "config": {
      "runtime": "codex",
      "models": {
        "default": "gpt-5.3-codex"
      }
    }
  }
}
JSON

# Local workspace mode (repo_path) + targeted role override
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Refactor and harden auth + billing flows",
    "repo_path": "/path/to/repo",
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

Para OpenRouter com `open_code`, use IDs de modelo no formato `openrouter/<provider>/<model>` (por exemplo, `openrouter/minimax/minimax-m2.5`).

Para Infron com `open_code`, defina `INFRON_API_KEY` e use `infron/<provider>/<model>` (por exemplo `infron/moonshotai/kimi-k2.6`). Infron é um gateway compatível com OpenAI que atende aos ids `<provider>/<model>` padrão, portanto, mover uma função é uma troca de prefixo e nada mais muda:

```bash
SWE_DEFAULT_MODEL=infron/moonshotai/kimi-k2.6
```

Com **apenas** um conjunto `INFRON_API_KEY` (sem `ANTHROPIC_API_KEY`, nenhuma outra chave de gateway, sem `SWE_DEFAULT_RUNTIME`), o SWE-AF seleciona automaticamente o tempo de execução `open_code` e o padrão é `infron/deepseek/deepseek-v4-flash-0731` — a mesma regra que o caminho do gateway existente já segue. Uma chave de gateway já configurada mantém a precedência, portanto, adicionar uma chave Infron nunca redireciona uma implantação existente por conta própria.

> As implantações Docker e Railway usando Infron devem definir `HARNESS_MODEL=infron/deepseek/deepseek-v4-flash-0731` (ou outro ID `infron/...`) no ambiente. A imagem cria um valor `openrouter/...` que a cascata do modelo `open_code` lê após o padrão automático do Infron e, de outra forma, o substituiria. `SWE_DEFAULT_MODEL` fixa todos os modelos, mas não alimenta o `small_model` do OpenCode; defina `HARNESS_MODEL` para esse caminho (definir ambos é adequado).

### Gemini Free Tier (primeiro simulado; o uso ao vivo permanece não autorizado)

SWE-AF usa seu tempo de execução `open_code` existente, explicitamente selecionado com `SWE_DEFAULT_RUNTIME=open_code`. Defina `SWE_GEMINI_MODEL` para um ID de modelo escolhido deliberadamente, `SWE_DEFAULT_MODEL=google-gemini/gemini-free-tier` e `HARNESS_MODEL=google-gemini/gemini-free-tier`; todas as funções SWE-AF não especificadas são resolvidas para o alias do modelo OpenCode declarado, que mapeia para o ID selecionado pelo ambiente. O [catálogo de modelos](https://ai.google.dev/gemini-api/docs/models) atual do Google lista `gemini-3.5-flash-lite` como **Estável**. A [página de preços](https://ai.google.dev/gemini-api/docs/pricing) lista seus preços padrão de entrada/saída como gratuitos no nível gratuito. Esses são apenas fatos de documentos públicos e não uma confirmação de que um determinado projeto do Google tenha acesso, cota ou faturamento configurado. Não use os IDs `gemini-2.0-flash` ou `gemini-2.0-flash-lite` obsoletos. Não há substituto de modelo/provedor.

O [guia de compatibilidade OpenAI](https://ai.google.dev/gemini-api/docs/openai) do Google documenta o endpoint `/v1beta/openai/` e suporte para streaming, chamada de função e respostas JSON estruturadas. O guia descreve essa compatibilidade como **beta** e seus exemplos não certificam todos os recursos para esse ID de modelo exato. A porta histórica de loopback do cliente real (`experiments/pi-vs-sweaf/runs/pilot-v2-loopback-transport-gate/report.json`, OpenCode 1.18.35) é **FAIL**: o texto do assistente foi armazenado em buffer até a conclusão das respostas SSE e o OpenCode tentou novamente cinco vezes após um 503 local, apesar das opções de zero nova tentativa. O gateway bloqueou todas as cinco tentativas extras e manteve a reserva de uso desconhecido. Uma nova investigação OpenCode 2.0.15 isolada de rede contra um gateway/mock local temporário por execução também **falha no portão de streaming incremental**: carimbos de data e hora de liberação do gateway e um leitor HTTP de loopback bruto mostram o conteúdo SSE chegando de forma incremental (cerca de 343 ms antes de `[DONE]`), enquanto o evento JSON `text` do OpenCode chegou cerca de 31 ms depois que o gateway concluiu o completo resposta. Isso isola o buffer observado para o caminho de evento cliente/CLI do OpenCode, em vez do gateway ou transporte HTTP local; ele não estabelece se o OpenCode consome internamente tokens de modelo de forma incremental. A mesma investigação fez com êxito uma chamada de ferramenta simulada e resolveu ambas as solicitações de uso conhecido, com zero encaminhamento de upstream/provedor. Um 503 local explícito produziu uma solicitação de gateway, sem nova tentativa, sem cobrança e um livro-razão desarmado retendo a reserva completa. Eliminar o OpenCode depois que um pedaço SSE inicial cancelou o fluxo; o razão reteve a reserva total (US$ 0,012688), não cobrou nada e tropeçou. Estas são observações de cliente local/simuladas - não evidências ao vivo do Gemini - e não constituem o caminho completo do piloto-executor para `implement_issue`. O cliente instalado, portanto, permanece **não aprovado para transporte**. O [guia de limite de taxa](https://ai.google.dev/gemini-api/docs/rate-limits) diz que RPM/TPM/RPD dependem do projeto e do modelo, podem mudar de acordo com o nível/status, não são garantidos e devem ser verificados no AI Studio para o projeto de destino; não estabelece os atuais limites numéricos deste projeto. O [guia de faturamento](https://ai.google.dev/gemini-api/docs/billing) diz que a elegibilidade do nível gratuito se aplica a determinados modelos em um projeto ativo/teste gratuito; mudando para o nível pagoexige vincular faturamento e pré-pagamento (o guia atualmente descreve um pré-pagamento mínimo de US$ 5 para esse fluxo). A tabela de preços também indica que as solicitações do nível gratuito podem ser usadas para melhorar os produtos do Google, portanto, a aprovação de dados do repositório/privacidade é uma porta separada. Esses documentos foram verificados em 09/10/2026; nenhum console de conta/projeto foi acessado. Mantenha o perfil real bloqueado até que o acesso ao projeto alvo, os limites, a privacidade e o status de cobrança sejam verificados de forma independente, o provedor esteja conectado através do gateway/razão controlado e o comportamento do cliente atual passe nos testes de loopback local.

O provedor OpenCode é configurado no perfil de API compatível com OpenAI do Google, com `GEMINI_API_KEY` referenciado apenas por meio de interpolação de ambiente e adaptador `maxRetries` definido como zero. Atualmente, esse provedor segmenta o Google **diretamente**; o tempo de execução raiz/Compose não conecta o gateway de segurança piloto, reserva de orçamento ou razão a esse caminho de solicitação. O gateway existente é iniciado por célula pelo executor piloto em `experiments/`; não é um serviço compartilhado no tempo de execução raiz do Compose e seu razão requer contexto de execução/célula. A simples alteração de `baseURL` não deixaria nenhum serviço de gateway ou aplicaria incorretamente uma política piloto/simulada. Portanto, o perfil real **não é seguro para ativação** até que o tempo de execução seja roteado corretamente através do gateway controlado existente. Nunca coloque uma chave em `opencode.json`, arquivos de configuração, argumentos de linha de comando, logs, acessórios ou artefatos do GitHub. O `debug config` do OpenCode pode imprimir credenciais resolvidas baseadas no ambiente: não execute-o com segredos presentes nem capture sua saída; o diagnóstico do gateway deve registrar apenas presença/status de credenciais, nunca valores ou cabeçalhos de autorização. Para uma futura configuração de provedor autorizado separadamente, injete a chave de um armazenamento secreto/segredo de ações do GitHub e defina, por exemplo:

```bash
SWE_DEFAULT_RUNTIME=open_code
SWE_GEMINI_MODEL=gemini-3.5-flash-lite  # candidate only; verify before selection
SWE_DEFAULT_MODEL=google-gemini/gemini-free-tier
HARNESS_MODEL=google-gemini/gemini-free-tier  # pins OpenCode small_model; prevents OpenRouter fallback
GEMINI_API_KEY=<injected-from-secret-store>
```

Um alias de modelo OpenCode separado, `google-gemini-mock/gemini-mock-model`, aponta apenas para `http://127.0.0.1:8765/v1` e usa o modelo de fixture fixo `gemini-local-mock` com um espaço reservado não secreto. Selecione-o com `SWE_DEFAULT_RUNTIME=open_code`, `SWE_DEFAULT_MODEL=google-gemini-mock/gemini-mock-model` e o mesmo valor `HARNESS_MODEL`. Ao executar a própria CLI, fixe `HARNESS_MODEL=google-gemini-mock/gemini-mock-model`; a resolução do modelo falhará se o seletor de modelo pequeno do OpenCode ainda apontar para outro lugar. O teste de regressão fornece um acessório de loopback determinístico compatível com OpenAI no limite de chamada SWE-AF e executa o loop de codificação `implement_issue` real em um repositório Git descartável; ele verifica a diferença de ramificação gerada e confirma que o chamador permanece em `main`. Isso exercita o comportamento do tempo de execução/configuração/Git do SWE-AF, não o transporte do provedor do binário OpenCode instalado ou o gateway. Uma execução do OpenCode `implement_issue` roteada por gateway permanece não verificada porque o cliente instalado falha no streaming incremental. Os testes de unidade de gateway cobrem enquadramento SSE, ferramentas, saída estruturada, erros HTTP, tempo limite/cancelamento, novas tentativas, reservas de orçamento e comportamento de falha de uso desconhecido. Os dois testes de fechamento do cliente passaram juntos por cinco iterações consecutivas depois que o gateway foi alterado para persistir no estado de cancelamento de falha fechada antes de fechar o upstream e para enviar `[DONE]` somente após a liquidação do razão; esta é uma prova simulada/de unidade, não uma aprovação de transporte. Esses testes unitários não substituem a falha de loopback do cliente real acima. A telemetria do gateway filtra cabeçalhos de autorização e não registra valores de credenciais.

**Auditoria direta do SDK `google-genai` (AgentField local 0.1.141):** AgentField exporta um protocolo `HarnessProvider` (`execute(prompt, options) -> RawResult`), mas a fábrica de provedores de seu executor é um registro interno fechado; o provedor `gemini` integrado inicia a CLI Gemini, não o SDK. As opções de chicote passam nomes de ferramentas permitidas, não executores de ferramentas, e a saída do esquema é orientada por um sufixo de prompt AgentField que solicita ao agente que escreva `.agentfield_output.json`. Um provedor de SDK direto precisaria, portanto, de seu próprio loop de chamada de função de leitura/gravação/edição/Bash/Glob/Grep, aplicação de permissão, contrato de saída de esquema, mapeamento de tempo limite/cancelamento e supressão de novas tentativas (caso contrário, o chicote tentará erros transitórios e poderá tentar o reparo do esquema Litellm). O SDK `google-genai` instalado usa solicitações `:generateContent` nativas do Gemini; o gateway piloto atualmente aceita solicitações `/v1/chat/completions` compatíveis com OpenAI e seu controlador de orçamento valida campos OpenAI `messages`/token. Apontar o SDK para esse gateway não funcionaria; ligar diretamente para o Google ignoraria o gateway, o razão e a política de saída existentes. `google-genai` está presente neste ambiente Python local, mas não é declarado pelos manifestos de dependência deste projeto. Nenhum adaptador SDK direto foi adicionado porque uma implementação segura precisa de uma ponte de gateway de protocolo nativo e de um executor de ferramenta completo, e não de um wrapper somente de texto. Estas são lacunas concretas de integração, e não evidências de compatibilidade viva com Gemini.

**Status de autorização:** `GEMINI_FREE_READY=false` e `live_provider_execution_authorized=false`. O perfil do provedor real é apenas configuração; não o selecione ou forneça uma chave real até que os documentos oficiais atuais do modelo/API, as cotas do projeto-alvo e o status de faturamento, os preços/limites específicos do modelo, um limite de gastos rígidos da conta, a compatibilidade ponta a ponta do OpenCode/Gateway e a aprovação humana de uso único separada tenham sido verificados de forma independente. Um fluxo de trabalho simulado não é evidência de cota gratuita ou prontidão do fornecedor.

### Provedores diretos MiniMax

As imagens Docker incluem entradas diretas do provedor MiniMax para regiões suportadas e modos de compatibilidade de API. `MiniMax-M3` e `MiniMax-M2.7` estão disponíveis em todas as entradas.

| Região | IDs de modelo `open_code` compatíveis com OpenAI | IDs do modelo `open_code` compatível com Antrópico | URL base antrópica |
|---|---|---|---|
| Globais | `minimax-global-openai/MiniMax-M3`, `minimax-global-openai/MiniMax-M2.7` | `minimax-anthropic/MiniMax-M3`, `minimax-anthropic/MiniMax-M2.7` | `https://api.minimax.io/anthropic` |
| China | `minimax-cn-openai/MiniMax-M3`, `minimax-cn-openai/MiniMax-M2.7` | `minimax-anthropic/MiniMax-M3`, `minimax-anthropic/MiniMax-M2.7` | `https://api.minimaxi.com/anthropic` |

| Modelo | Janela de contexto | Modalidades de entrada | Pensando | Entrada/saída/leitura de cache/gravação de cache por milhão de tokens |
|---|---:|---|---|---|
| `MiniMax-M3` | 1.000.000 | texto, imagem, vídeo | adaptativo ou desativado | US$ 0,30 / US$ 1,20 / US$ 0,06 / sem cobrança |
| `MiniMax-M2.7` | 204.800 | texto | sempre ligado | $ 0,30 / $ 1,20 / $ 0,06 / $ 0,375 |

O preço do `MiniMax-M3` é escalonado por comprimento de entrada: solicitações acima de 512 mil tokens de entrada são cobradas a US$ 0,60/US$ 2,40/US$ 0,12. Os metadados do provedor preparados usam o nível padrão ≤512K, que é o que as solicitações de codificação normais atingem.

Para o caminho direto compatível com OpenAI, defina `MINIMAX_API_KEY`, use `runtime: "open_code"` e selecione um dos IDs de modelo `minimax-global-openai/*` ou `minimax-cn-openai/*` acima. Os URLs base compatíveis com OpenAI configurados são `https://api.minimax.io/v1` e `https://api.minimaxi.com/v1`.

Para o caminho OpenCode compatível com Anthropic, defina `MINIMAX_API_KEY`, defina `ANTHROPIC_BASE_URL` para qualquer URL `/anthropic` regional mostrado acima, use `runtime: "open_code"` e selecione `minimax-anthropic/MiniMax-M3` ou `minimax-anthropic/MiniMax-M2.7`. A configuração do provedor anexa `/v1`; mantenha `ANTHROPIC_BASE_URL` no URL `/anthropic` regional.

Para o caminho Claude compatível com Anthropic, defina `ANTHROPIC_AUTH_TOKEN`, defina `ANTHROPIC_BASE_URL` para o URL regional `/anthropic` mostrado acima, use `runtime: "claude_code"` e selecione `MiniMax-M3` ou `MiniMax-M2.7`. Não anexe `/v1`; Claude Code adiciona `/v1/messages` ao URL base configurado. Desmarque `ANTHROPIC_API_KEY` (e `CLAUDE_CODE_OAUTH_TOKEN`) nessa implantação — uma credencial Antrópica deixada no ambiente pode ser enviada para o endpoint não Antrópico.

`ANTHROPIC_BASE_URL` abrange todo o processo, portanto, uma implantação não pode rotear o tráfego compatível com Claude e MiniMax Anthropic para diferentes endpoints.

Para autenticação de assinatura do Codex com ChatGPT, instale a CLI do Codex no host, execute `codex login`, deixe `OPENAI_API_KEY` não definido para este processo e defina `SWE_CODEX_AUTH_MODE=chatgpt` ou `auto`. Para faturamento da plataforma OpenAI API, defina `SWE_CODEX_AUTH_MODE=api_key` e `OPENAI_API_KEY`.

> A imagem Docker prepara `HARNESS_MODEL=openrouter/deepseek/deepseek-v4-flash-0731` para que a interpolação de configuração `small_model` do OpenCode sempre tenha um valor. `HARNESS_MODEL` afeta apenas o tempo de execução `open_code` - as implantações `claude_code` e `codex` resolvem seus próprios padrões de tempo de execução (o codex escolhe seu modelo pelo modo de autenticação) e podem substituir por função via `SWE_DEFAULT_MODEL` / `models` como de costume.

> A sandbox `workspace-write` do Codex CLI usa bubblewrap (`bwrap`) e precisa de namespaces de usuário Linux habilitados no host. A maioria dos hosts Linux de produção e tempos de execução de contêineres gerenciados (Railway, etc.) permitem isso por padrão, mas o Docker local em WSL2 ou ambientes protegidos pode recusar com `bwrap: No permissions to create a new namespace`. Se o verificador relatar esse erro, o codificador executou, mas não conseguiu gravar arquivos – habilite namespaces de usuário no host antes de confiar no tempo de execução do codex.

### Opcional: pesquisa na web

Os agentes de codificação e revisão podem consultar documentação externa, APIs de biblioteca, mensagens de erro e status de versão/descontinuação durante uma construção. Isso é ativado por meio de dois ambientes na implantação:

```
OPENCODE_ENABLE_EXA=1
EXA_API_KEY=...
```

Quando definidas, as ferramentas `websearch` e `webfetch` integradas do opencode ficam disponíveis para todos os raciocinadores que executam o tempo de execução aberto - o modelo decide quando usá-las com base na tarefa. Obtenha uma chave em [exa.ai](https://exa.ai/).

O raciocinador do codificador também recebe uma breve diretriz de restrição anexada ao prompt do sistema, de modo que um longo loop de codificação não atrapalha as pesquisas que ele poderia responder lendo a base de código. Nenhuma configuração necessária além dos env vars; a fiação herda o env pai naturalmente por meio do chicote CLI do agentfield.

Isso funciona em tempo de execução aberto (opencode). O tempo de execução do Claude usa `WebSearch`/`WebFetch` original da Anthropic e atualmente não está conectado aqui – registre um problema se desejar.

## O que acontece em uma versão

- A arquitetura é gerada e revisada antes do início da codificação
- Os problemas são classificados por dependência e executados em paralelo em árvores de trabalho isoladas
- Cada edição recebe passes dedicados de codificador, testador e revisor
- Problemas com falha acionam a adaptação orientada pelo consultor (dividir, redefinir o escopo ou escalar)
- Escalações acionam o replanejamento do DAG restante
- O resultado final é mesclado, testado para integração e verificado em relação aos critérios de aceitação

<p align="center">
<img src="assets/archi.png" alt="Arquitetura SWE-AF" width="100%" />
</p>

> As execuções típicas geram mais de 400 a 500 instâncias de agente em planejamento, execução, controle de qualidade e verificação. Para DAGs maiores e ciclos repetidos de adaptação/replanejamento, o SWE-AF pode escalar de centenas a milhares de invocações de agentes em uma única construção.

## Benchmark

**95/100 com haiku e MiniMax**: SWE-AF obteve pontuação 95/100 com roteamento de classe haiku Claude (US$ 20) e MiniMax M2.5 via tempo de execução aberto (US$ 6), superando Claude Code sonnet (73), Codex o3 (62) e Claude Code haiku (59) no mesmo prompt.

| Dimensão | SWE-AF (haiku) | SWE-AF (MiniMax) | Soneto CC | Códice (o3) | CC Haiku |
| --------------- | -------------- | ---------------- | --------- | ---------- | -------- |
| Funcional (30) | **30** | **30** | **30** | **30** | **30** |
| Estrutura (20) | **20** | **20** | 10 | 10 | 10 |
| Higiene (20) | **20** | **20** | 16 | 10 | 7 |
| Git (15) | **15** | **15** | 2 | 2 | 2 |
| Qualidade (15) | 10 | 10 | **15** | 10 | 10 |
| Total | **95** | **95** | **73** | **62** | **59** |
| **Custo** | **~$20** | **~$6** | ?         | ?          | ?        |
| **Tempo** | ~30-40 minutos | 43 minutos | ?         | ?          | ?        |

<details>
<summary><strong>Detalhes completos do benchmark e reprodução</strong></summary>

O mesmo prompt testado em vários agentes. SWE-AF com tempo de execução Claude (mapeamento de modelo de classe haiku) usou mais de 400 instâncias de agente; SWE-AF com MiniMax M2.5 via tempo de execução aberto alcançou qualidade idêntica com economia de custos de 70%.

**Prompt usado para todos os agentes:**

> Crie um aplicativo de tarefas CLI Node.js com comandos de adição, lista, conclusão e exclusão. Os dados devem persistir em um arquivo JSON. Inicialize o git, escreva testes e envie seu trabalho.

### Estrutura de pontuação

| Dimensão | Pontos | O que mede |
| ---------- | ------ | ------------------------------------------------ |
| Funcional | 30 | Comportamento CLI e aprovação em testes |
| Estrutura | 20 | Layout de fonte modular e organização de testes |
| Higiene | 20 | `.gitignore`, status limpo, sem artefatos indesejados |
| Git | 15 | Comprometer disciplina e qualidade da mensagem |
| Qualidade | 15 | Tratamento de erros, metadados de pacotes, qualidade README |

### Reprodução

```bash
# SWE-AF (Claude runtime, haiku-class mapping) - $20, 30-40 min
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Build a Node.js CLI todo app with add, list, complete, and delete commands. Data should persist to a JSON file. Initialize git, write tests, and commit your work.",
    "repo_path": "/tmp/swe-af-output",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "haiku"
      }
    }
  }
}
JSON

# SWE-AF (MiniMax M2.5 via OpenRouter runtime) - $6, 43 min
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Build a Node.js CLI todo app with add, list, complete, and delete commands. Data should persist to a JSON file. Initialize git, write tests, and commit your work.",
    "repo_path": "/workspaces/todo-app-benchmark",
    "config": {
      "runtime": "open_code",
      "models": {
        "default": "openrouter/minimax/minimax-m2.5"
      }
    }
  }
}
JSON

# Claude Code (haiku)
claude -p "Build a Node.js CLI todo app with add, list, complete, and delete commands. Data should persist to a JSON file. Initialize git, write tests, and commit your work." --model haiku --dangerously-skip-permissions

# Claude Code (sonnet)
claude -p "Build a Node.js CLI todo app with add, list, complete, and delete commands. Data should persist to a JSON file. Initialize git, write tests, and commit your work." --model sonnet --dangerously-skip-permissions

# Codex (gpt-5.3-codex)
codex exec "Build a Node.js CLI todo app with add, list, complete, and delete commands. Data should persist to a JSON file. Initialize git, write tests, and commit your work." --full-auto
```

**Métricas medidas do MiniMax M2.5 (fevereiro de 2026):**
- Cobertura de código de 99,22% (único agente com cobertura medida)
- 4 tipos de erros personalizados (TodoError, ValidationError, NotFoundError, StorageError)
- 999 LOC, 4 módulos, 74 testes, 9 commits

**Análise de qualidade de produção:** [comparação objetiva](examples/agent-comparison/PRODUCTION_QUALITY_ANALYSIS.md) de métricas mensuráveis ​​em todos os agentes.

Ativos de referência, registros, avaliador e projetos gerados residem em [`examples/agent-comparison/`](examples/agent-comparison/).

</details>

> **Envie o código e depois audite-o:** [SEC-AF](https://github.com/Agent-Field/sec-af) executa a mesma arquitetura multiagente em sua base de código — 250 agentes, 94% de redução de ruído, todas as descobertas comprovadas.

## Docker

```bash
cp .env.example .env
# Uncomment exactly ONE provider key: OPENROUTER_API_KEY (recommended),
# ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, OPENAI_API_KEY, or GOOGLE_API_KEY
# Optionally add GH_TOKEN (private-repo clones, pushing branches, opening PRs)

docker compose up -d
```

> `.env.example` vem com **todas** chaves de provedor comentadas — remova o comentário
> exatamente um. Em particular, não deixe um espaço reservado `ANTHROPIC_API_KEY`
> valor no local: qualquer valor não vazio força o tempo de execução `claude_code` e
> interrompe uma configuração somente OpenRouter.

Envie uma compilação:

```bash
# Default runtime (auto-selected from whichever provider key is in .env)
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth",
    "repo_url": "https://github.com/user/my-repo"
  }
}
JSON

# With open-source runtime (set OPENROUTER_API_KEY in .env)
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth",
    "repo_url": "https://github.com/user/my-repo",
    "config": {
      "runtime": "open_code",
      "models": {
        "default": "openrouter/minimax/minimax-m2.5"
      }
    }
  }
}
JSON

# Local workspace mode (repo_path)
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add JWT auth",
    "repo_path": "/workspaces/my-repo"
  }
}
JSON
```

Trabalhadores de escala:

```bash
docker compose up --scale swe-agent=3 -d
```

Use um plano de controle de host em vez do serviço de plano de controle do Docker:

```bash
docker compose -f docker-compose.local.yml up -d
```

## Fluxo de trabalho do GitHub Repo (Clone -> Build -> PR)

Passe `repo_url` em vez de `repo_path` para permitir que o SWE-AF clone e abra um PR após a execução.

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "repo_url": "https://github.com/user/my-project",
    "goal": "Add comprehensive test coverage",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "sonnet",
        "coder": "opus",
        "qa": "opus"
      }
    }
  }
}
JSON
```

Requisitos:

- `GH_TOKEN` em `.env` com escopo `repo` — necessário para *este* fluxo de trabalho, já que
ele clona repositórios privados, envia push ao branch e abre o PR. Constrói isso
permaneça local (`repo_path`) ou direcione um repositório público que não precisa dele.
- Acesso ao repositório para esse token

### Portão CI pós-PR

Depois que o SWE-AF empurra o ramo de integração e abre um PR (pronto para revisão,
não rascunho), ele observa as ações do GitHub nesse PR até que as verificações sejam
conclusivo. Se falharem, um loop limitado de correção e reenvio executa um agente que
é explicitamente proibido silenciar testes (sem `pytest.skip`, sem `xfail`,
sem comentar testes, sem afrouxar afirmações) - deve produzir um
correção legítima no código de produção e enviar um novo commit. Quando o CI é
verde, o portão retorna sucesso; quando o CI falha após tentativas de correção, o PR
permanece aberto com verificações com falhas visíveis para que um revisor humano possa intervir.

Configuração em `BuildConfig`:

| Campo | Padrão | Finalidade |
|---|---|---|
| `check_ci` | `true` | Execute o portão CI pós-PR. Configure `false` para retornar imediatamente após a criação do PR. |
| `max_ci_fix_cycles` | `2` | Cap on watch → fix → repush iterações após o push inicial. |
| `ci_wait_seconds` | `1500` | Tampa de relógio de parede por relógio `gh pr checks` (25 min). |
| `ci_poll_seconds` | `30` | Intervalo de pesquisa para `gh pr checks`. |

## Use SWE-AF como um sub-arnês (construções em nível de problema)

O pipeline `build` completo é **nível de recurso**: ele planeja, decompõe e
verifica um recurso completo, o que leva horas. Quando o chamador é ele próprio um
equipamento de codificação - Claude Code, Codex, OpenCode - já fez o
planejamento. Nesse caso, o SWE-AF expõe um ponto de entrada no **nível do problema**,
`implement_issue`, que ignora todos os agentes de planejamento e executa apenas a codificação
loop em um galho isolado. Delegar questões de bom escopo ao SWE-AF de forma barata
ou modelos de peso aberto mantêm o orçamento simbólico do chicote principal para o trabalho que
precisa disso.

Regra prática para os dois formatos de prompt:

| Forma de alerta | Ponto de entrada |
| --- | --- |
| "Implementar recurso X" (precisa de decomposição) | `swe-planner.build` / `swe-fast.build` |
| "Altere este código neste arquivo, assim" (com escopo completo, contexto fornecido) | `swe-planner.implement_issue` / `swe-fast.implement_issue` |

Um chicote não precisa desta tabela codificada: ambos os pontos de entrada são registrados com
o plano de controle carregando uma tag `entrypoint` e uma descrição de roteamento, então
`af ls --entrypoints` (ou `GET /api/v1/discovery/capabilities`) os lista -
com orientação sobre quando usar — ​​em qualquer plano de controle do AgentField o nó se junta
(campo agente ≥ 0,1.113).

Cada chamada cria sua própria árvore de trabalho git e uma ramificação `issue/<build_id>-<slug>`
off `base_branch` (padrão: a ramificação atual), implementa o problema com o
codificador → loop do revisor (um caminho QA + sintetizador quando `needs_deeper_qa` está definido),
opcionalmente, executa uma passagem do verificador em relação aos critérios de aceitação, remove o
worktree e retorna o branch. O checkout do chamador, a filial atual e
`git status` permanecem intactos – portanto, um chicote principal pode espalhar vários problemas
contra o mesmo `repo_path` simultaneamente e mesclar as ramificações retornadas
em si. Nada é enviado por push e nenhum PR é aberto, a menos que `enable_github_pr` esteja definido:
o chamador possui mesclagem e CI. O custo típico é de 4 a 8 chamadas LLM (contra centenas de uma
compilação em nível de recurso).

```bash
# Delegate one scoped issue (async; returns an execution_id immediately)
curl -X POST http://localhost:8080/api/v1/execute/async/swe-planner.implement_issue \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "issue": {
      "title": "Add retry with exponential backoff to fetch_user",
      "description": "In src/api/client.py, wrap fetch_user's HTTP call in a retry helper: 3 attempts, 0.5s base delay, doubling. Reuse the existing logger for retry warnings.",
      "acceptance_criteria": [
        "fetch_user retries up to 3 times on ConnectionError",
        "tests cover the retry-then-succeed path"
      ],
      "files_to_modify": ["src/api/client.py"],
      "testing_strategy": "pytest tests/api/test_client.py"
    },
    "repo_path": "/workspaces/my-project",
    "base_branch": "main",
    "config": { "models": { "default": "haiku" } }
  },
  "webhook": { "url": "https://my-harness.example/hooks/swe-af" }
}
JSON

# Poll instead of (or in addition to) the webhook
curl http://localhost:8080/api/v1/executions/<execution_id>
# Progress notes while it runs
curl http://localhost:8080/api/v1/executions/<execution_id>/notes
```

O campo `branch` do resultado é a entrega:

```json
{
  "success": true,
  "outcome": "completed",
  "branch": "issue/a1b2c3d4-add-retry-with-exponential-backoff",
  "base_branch": "main",
  "commits": ["<sha>"],
  "files_changed": ["src/api/client.py", "tests/api/test_client.py"],
  "iterations": 1,
  "verification": { "passed": true, "criteria_results": ["..."] },
  "debt_items": [],
  "pr_url": ""
}
```

Campos `issue`: `title` + `description` (obrigatório), `acceptance_criteria`,
`files_to_create` / `files_to_modify`, `testing_strategy`, `needs_deeper_qa`
(rotas através de QA + revisor + sintetizador), `estimated_complexity`, `name`.
`additional_context` (nível superior) é anexado à descrição.

Chaves `config` (esquema completo: [`swe_af/issue/schemas.py`](swe_af/issue/schemas.py)):

| Chave | Padrão | Descrição |
| --- | --- | --- |
| `runtime` / `models` | como em `build` | Mesmo tempo de execução + mapa de funções plano; chaves de função válidas: `default`, `coder`, `code_reviewer`, `qa`, `qa_synthesizer`, `verifier`, `git` |
| `max_coding_iterations` | `3` | Orçamento de loop interno (o padrão de nível de recurso é 5) |
| `verify` | `true` | Um verificador passa nos critérios de aceitação |
| `enable_github_pr` | `false` | Empurre o branch e abra um PR (precisa de um controle remoto `origin`) |
| `agent_timeout_seconds` | `1800` | Tempo limite por agente |
| `agent_max_turns` | `50` | Orçamento de turno de uso de ferramentas por agente |
| `keep_worktree` | `false` | Deixe a árvore de trabalho no lugar para depuração |

Notas para autores do chicote principal:

- `repo_path` deve ser um checkout que o nó SWE-AF pode alcançar (mesma máquina, ou
o volume `workspaces` compartilhado na configuração do Docker) com pelo menos um commit.
- Alterações não confirmadas na árvore do chamador **não** são visíveis para o problema
branch — é criado a partir do estado base confirmado.
- Uma compilação com falha com commits ainda retorna o branch (`success: false`) então
o chamador pode fazer a triagem; uma compilação que não produziu commits exclui seu branch
e retorna `branch: ""`.
- Limite sua distribuição: cada delegação é uma corrida multiagente paga. Um punhado de
problemas simultâneos por repositório são o ponto ideal - o nó também limita seus próprios
simultaneidade.
- Disponível de forma idêntica em `swe-fast.implement_issue` e em movimento
implementação sob esses mesmos IDs de nó.

Uma habilidade pronta do Código Claude para este fluxo é enviada em
[`.claude/skills/delegate-issue/`](.claude/skills/delegate-issue/SKILL.md).

## Referência de API

<details>
<summary><strong>Endpoints do agente</strong></summary>

Endpoints assíncronos principais (retorna um `execution_id` imediatamente):

```bash
# Full build: plan -> execute -> verify
POST /api/v1/execute/async/swe-planner.build

# Issue-level build (sub-harness entry): coding loop only, no planning
POST /api/v1/execute/async/swe-planner.implement_issue

# Plan only
POST /api/v1/execute/async/swe-planner.plan

# Execute a prebuilt plan
POST /api/v1/execute/async/swe-planner.execute

# Resume after interruption
POST /api/v1/execute/async/swe-planner.resume_build
```

Monitoramento:

```bash
curl http://localhost:8080/api/v1/executions/<execution_id>
```

Cada especialista também pode ser chamado diretamente:

`POST /api/v1/execute/async/swe-planner.<agent>`

</details>

<details>
<summary><strong>Fluxo de execução do agente</strong></summary>

| Agente | Entrada -> Saída |
| ------------------------ | ------------------------------------------------------------------- |
| `run_product_manager` | objetivo -> PRD |
| `run_architect` | PRD -> arquitetura |
| `run_tech_lead` | arquitetura -> revisão |
| `run_sprint_planner` | arquitetura -> emitir DAG |
| `run_issue_writer` | especificação do problema -> problema detalhado |
| `run_coder` | issue + worktree -> código + testes + commit |
| `run_qa` | árvore de trabalho -> resultados do teste |
| `run_code_reviewer` | worktree -> revisão de qualidade/segurança |
| `run_qa_synthesizer` | QA + revisão -> CORRIGIR / APROVAR / BLOQUEAR |
| `run_issue_advisor` | contexto de falha -> adaptar/dividir/aceitar/escalar |
| `run_replanner` | estado de construção + falhas -> plano reestruturado |
| `run_merger` | ramos -> saída mesclada |
| `run_integration_tester` | repositório mesclado -> resultados de integração |
| `run_verifier` | repo + PRD -> aprovação/reprovação de aceitação |
| `generate_fix_issues` | critérios com falha -> problemas de correção direcionados |
| `run_github_pr` | filial -> push + PR |

</details>

<details>
<summary><strong>Configuração</strong></summary>

Passe `config` para `build` ou `execute`. Esquema completo: [`swe_af/execution/schemas.py`](swe_af/execution/schemas.py)

| Chave | Padrão | Descrição |
| ------------------------- | --------------- | ----------------------------------------------------- |
| `runtime` | `"claude_code"` | Runtime do modelo: `"claude_code"`, `"open_code"` ou `"codex"`. O padrão também respeita o env var `SWE_DEFAULT_RUNTIME` quando nenhum `runtime` é passado em `config` - configure-o na implantação para que os chamadores não precisem analisar uma configuração. |
| `models` | `null` | Mapa de modelo plano (`default` + teclas de função abaixo). Sem um valor fornecido pelo chamador, o env var `SWE_DEFAULT_MODEL` é usado como padrão para todas as funções — configure-o na implantação para fixar um modelo sem alterações de código. O chamador `models.default` ou as chaves por função ainda vencem. |
| `max_coding_iterations` | `5` | Orçamento de repetição do circuito interno |
| `max_advisor_invocations` | `2` | Orçamento do consultor de circuito intermediário |
| `max_replans` | `2` | Orçamento de replanejamento em nível de construção |
| `enable_issue_advisor` | `true` | Habilitar adaptação de problemas |
| `enable_replanning` | `true` | Habilitar o replanejamento global |
| `enable_learning` | `false` | Habilitar memória compartilhada entre questões (aprendizado contínuo) |
| `agent_timeout_seconds` | `2700` | Tempo limite por agente |
| `agent_max_turns` | `150` | Orçamento de giro de uso de ferramentas |

</details>

<details>
<summary><strong>Chaves de função do modelo</strong></summary>

`models` suporta:

-`default`
-`pm`, `architect`, `tech_lead`, `sprint_planner`
-`coder`, `qa`, `code_reviewer`, `qa_synthesizer`
-`replan`, `retry_advisor`, `issue_writer`, `issue_advisor`
-`verifier`, `git`, `merger`, `integration_tester`

</details>

<details>
<summary><strong>Ordem de resolução</strong></summary>

`runtime defaults` < `models.default` < `models.<role>`

</details>

<details>
<summary><strong>Exemplos de configuração</strong></summary>

Mínimo:

```json
{
  "runtime": "claude_code"
}
```

Códice:

```json
{
  "runtime": "codex",
  "models": {
    "default": "gpt-5.3-codex"
  }
}
```

Totalmente personalizado:

```json
{
  "runtime": "open_code",
  "models": {
    "default": "openrouter/minimax/minimax-m2.5",
    "pm": "openrouter/qwen/qwen-2.5-72b-instruct",
    "architect": "openrouter/qwen/qwen-2.5-72b-instruct",
    "coder": "openrouter/deepseek/deepseek-chat",
    "qa": "openrouter/deepseek/deepseek-chat",
    "verifier": "openrouter/qwen/qwen-2.5-72b-instruct"
  },
  "max_coding_iterations": 6,
  "enable_learning": true
}
```

</details>

<details>
<summary><strong>Artefatos</strong></summary>

```text
.artifacts/
├── plan/           # PRD, architecture, issue specs
├── execution/      # checkpoints, per-issue logs, agent outputs
└── verification/   # acceptance criteria results
```

</details>

<details>
<summary><strong>Desenvolvimento</strong></summary>

```bash
make test
make check
make clean
make clean-examples
```

</details>

<details>
<summary><strong>Segurança e comunidade</strong></summary>

- Guia de contribuição: [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- Código de conduta: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- Política de segurança: [`SECURITY.md`](SECURITY.md)
- Registro de alterações: [`CHANGELOG.md`](CHANGELOG.md)
- Licença: [`Apache-2.0`](LICENSE)

</details>

---

## Implementação Go

O nó em [`go/`](go/README.md) é o que `af install` oferece, e é
registra-se com os mesmos IDs de tudo acima - `swe-planner` e
`swe-fast` — portanto, nenhum gatilho, nome do raciocínio ou formato da API muda com ele. O
o manifesto repo-root se declara `superseded_by` `//go`, então
`af install https://github.com/Agent-Field/SWE-AF` pousa lá e substitui um
instalação existente do Python, mantendo seus segredos no escopo do nó.

A implementação do Python permanece inalterada e ainda o que `python -m swe_af` e
a pilha de composição na execução `docker-compose.yml`. Porque os dois agora respondem a
os mesmos IDs de nó, a execução de ambos em um plano de controle precisa de um explícito
`NODE_ID` em um deles – `docker-compose.go.yml` faz isso. Ver
[`go/README.md`](go/README.md) para instruções de construção, execução e Docker.

### Mecanismo de codificação (beta)

O nó Go vem com um mecanismo de codificação pré-construído de alto desempenho próximo ao clássico
ciclo de codificação. Se ele será executado depende de como você obteve o nó:

| Como você executa o SWE-AF | Motor | Para mudar isso |
| --- | --- | --- |
| `af install`/AgenteField Desktop | **Ativado por padrão** — `go/agentfield-package.yaml` declara `SWE_PRO_ENGINE` com `default: "1"` e o instalador o injeta | `SWE_PRO_ENGINE=0` para o loop clássico |
| Clone, fork, `docker-compose.go.yml` ou um binário simples | **Desligado** — nada muda a menos que você peça | `SWE_PRO_ENGINE=1` para ativar |

O portão é puramente a variável de ambiente; o manifesto é simplesmente o que define
isso para você em um `af install`. Com o motor ligado, cria rota por problema
codificação através dele - todo o resto, incluindo branch/push/PR, permanece com o
pipeline padrão. Desligue e o nó retorna ao clássico
codificador → revisor/loop de controle de qualidade. Os nomes dos raciocinadores e as formas de entrada/saída são idênticos
de qualquer forma, a mudança não custa nada além de reiniciar.

Se o binário não estiver presente ou não puder ser executado, o nó registrará um aviso e
continua usando o loop clássico, então é seguro deixar a bandeira acesa.

Botões de sintonia (`SWE_PRO_VARIANT`, `SWE_PRO_MAX_COST`, `SWE_PRO_PUBLIC_URL`)
e a superfície completa do ambiente estão documentados em
[`go/docs/pro-engine.md`](go/docs/pro-engine.md).

---

### Também construído em AgentField

> **[SEC-AF](https://github.com/Agent-Field/sec-af)** — auditor de segurança nativo de IA. 250 agentes por auditoria, 94% de redução de ruído, todas as descobertas comprovadamente exploráveis.
>
> **[Contrato-AF](https://github.com/Agent-Field/contract-af)** — Analisador de risco de contrato jurídico. Agentes geram agentes em tempo de execução. A revisão adversária captura o que os LLMs individuais perdem.

[Todos os repositórios →](https://github.com/Agent-Field)

---

SWE-AF é construído em [AgentField](https://github.com/Agent-Field/agentfield) como uma primeira etapa de chicotes de agente único para fábricas autônomas de engenharia de software. [Veja o que mais estamos construindo →](https://github.com/Agent-Field)
