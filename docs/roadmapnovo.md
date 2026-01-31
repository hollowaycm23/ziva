# ROADMAP TÉCNICO — IA GENERATIVA LOCAL AUTÔNOMA

## 1. Objetivo do Projeto
Construir uma **IA generativa local**, offline-first, com **RAG híbrido**, **autonomia por ferramentas dinâmicas** (auto-extensão funcional), **governança explícita via LangGraph**, e **uso seguro de GPU (≤ 12 GB VRAM)**.

O sistema deve **projetar, validar, registrar e reutilizar ferramentas** (funções Python), integrando-as ao seu próprio runtime, **sem execução arbitrária de código**.

---

## 2. Restrições Fixas (Hard Constraints)
- Hardware: **i7-12700KF | 32 GB RAM | RTX 4070 12 GB**
- VRAM máxima operacional: **10.5 GB**
- LLM local (CUDA) — **sem cloud**
- Ferramentas: **Python only**
- Execução: **controlada, versionada, auditável**

---

## 3. Arquitetura de Alto Nível

```
Usuário
 ↓
API / Interface
 ↓
Agent Controller (LangGraph)
 ↓
LLM (Planner / Tool Designer)
 ↓
Tool Validator (AST + Tests)
 ↓
Tool Registry (Persistente)
 ↓
Tool Runtime
 ↓
Resposta
```

---

## 4. Stack Tecnológica Congelada

### LLM
- **Qwen2.5 7B (Q5_K_M)** — principal
- Execução: Ollama (bare-metal)

### Embeddings
- **nomic-embed-text** (CPU)

### RAG
- Framework: **LlamaIndex**
- Vector DB: **Qdrant**
- Offline KB: **Kiwix (ZIM)**
- Web fallback: **SearXNG**

### Agente
- **LangGraph** (máquina de estados explícita)

### Interface
- FastAPI

---

## 5. Estrutura de Repositório

```
/core
  /agent
  /graph
  /memory
/tools
  /registry
  /validators
  /runtime
/rag
  /ingestion
  /retrieval
/api
/config
/docker
```

---

## 6. Diagrama Cognitivo (LangGraph)

### Estados
- INPUT
- ANALYZE
- NEED_TOOL?
- DESIGN_TOOL
- VALIDATE_TOOL
- REGISTER_TOOL
- USE_TOOL
- RESPOND

### Regras
- Máx 3 ciclos por requisição
- Nenhuma transição implícita
- Toda ferramenta passa por validação

---

## 7. Sistema de Ferramentas Dinâmicas

### Contrato Obrigatório
```python
def tool_name(input: dict) -> dict:
    """Descrição clara da função"""
    return {...}
```

### Validações
- AST parsing
- Allowlist de imports
- Proibição de:
  - os.system
  - subprocess
  - acesso à rede
  - filesystem livre

### Testes
- Execução unitária
- Inputs controlados
- Timeout

### Registro
- Versionamento
- Metadados
- Histórico de uso

---

## 8. Pipeline RAG

1. Recebe pergunta
2. Busca em Qdrant
3. Fallback SearXNG se necessário
4. Integra Kiwix offline
5. Re-ranking simples
6. Envia contexto ao LLM

### Parâmetros
- Chunk: 600 tokens
- Overlap: 100
- Top-K: 4

---

## 9. Governança, Qualidade e Segurança de Conhecimento

### 9.1 Busca Controlada na Internet
O sistema **pode consultar a internet** (via SearXNG) exclusivamente para:
- Comparação de informações
- Atualização do banco local de conhecimento
- Validação cruzada de dados existentes

A busca **nunca é usada diretamente para responder o usuário** sem passar por ingestão e validação.

---

### 9.2 Sistema de Pontuação de Confiança e Credibilidade
Todo documento externo candidato à ingestão recebe uma **pontuação de confiança**, baseada em critérios objetivos:

**Critérios de Pontuação (exemplo):**
- Fonte institucional / técnica conhecida (+30)
- Autor identificado (+10)
- Data recente (+10)
- Consistência com base local (+20)
- Ausência de linguagem opinativa (+10)
- Estrutura técnica (código, normas, RFC, docs) (+20)

**Score mínimo para ingestão:** 70/100

Documentos abaixo do score:
- São descartados ou
- Mantidos apenas em área de quarentena

---

### 9.3 Pipeline de Ingestão com Qualidade

```
Internet (SearXNG)
 → Pré-filtragem
 → Avaliação de Credibilidade
 → Normalização
 → Deduplicação
 → Ingestão Qdrant
```

---

### 9.4 Proteção contra Contaminação por Outras IAs

O sistema **nunca ingere conteúdo claramente gerado por IA**, utilizando:
- Detecção de padrões estilísticos (excesso de hedge, frases genéricas)
- Repetição de estruturas típicas de LLMs
- Falta de autoria verificável

Conteúdos com suspeita de geração por IA:
- Recebem penalidade severa no score
- São rejeitados por padrão

---

### 9.5 Proteção contra Contaminação de Persona

Separação rígida entre:
- **Base de conhecimento factual**
- **Persona da IA local**

Regras:
- Nenhum documento externo pode alterar prompt system
- Nenhuma ingestão pode modificar identidade, tom ou objetivos do agente
- Persona é definida **exclusivamente em configuração local versionada**

---

### 9.6 Auditoria e Rastreabilidade

- Todo documento ingerido possui:
  - Fonte
  - Data
  - Score de confiança
  - Justificativa de aceitação
- Possibilidade de rollback da base

---

- Limite de criação de ferramentas
- Auditoria completa
- Logs por estado
- Fallback seguro
- Nenhuma execução direta no host

---

## 10. Observabilidade

- Logs estruturados
- Monitoramento VRAM (nvidia-smi)
- Métricas por estado do LangGraph
- Detecção de loop

---

## 11. Roadmap por Fases

### Fase 0 — Arquitetura (Semana 0)
- Congelar decisões
- Diagramas

### Fase 1 — Infraestrutura (Semana 1)
- Docker (Qdrant, SearXNG)
- Ollama
- Kiwix

### Fase 2 — LLM Estável (Semana 1)
- Testes VRAM
- Prompt base

### Fase 3 — RAG Completo (Semana 2)
- Ingestão
- Retrieval

### Fase 4 — Agente LangGraph (Semana 2)
- Estados
- Transições

### Fase 5 — Ferramentas Dinâmicas (Semana 3)
- Validator
- Registry

### Fase 6 — Tool Calling (Semana 3)
- Runtime
- Memória funcional

### Fase 7 — Segurança (Semana 4)
- Hardening

### Fase 8 — API e Interface (Semana 4)

### Fase 9 — Estabilidade (Semana 5)

### Fase 10 — Refinamento Cognitivo (Semana 6)

---

## 12. Critérios de Sucesso Final

- LLM estável ≤ 10.5 GB VRAM
- RAG funcional e citável
- Criação de ferramentas segura
- Reutilização automática
- Nenhuma execução arbitrária
- Sistema auditável

---

## 13. Resultado Esperado

Uma **IA local autônoma**, com **memória funcional**, **auto-extensível**, **segura**, **offline**, e **operacionalmente previsível**, no padrão de agentes avançados (Antigravity / Devin-like), porém sob controle arquitetural explícito.

