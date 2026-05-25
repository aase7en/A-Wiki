# LangChain Framework for LLM Applications

> **Type:** documentation
> **Domain:** AI Tools
> **Ref:** https://python.langchain.com/docs/get_started/introduction
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** LLM, framework, chains, agents, RAG

## Abstract

LangChain is an open-source framework for building applications powered by large language models. It provides modular abstractions for model I/O (prompts, LLMs, output parsers), retrieval-augmented generation (document loaders, text splitters, vector stores, retrievers), chains (LCEL — LangChain Expression Language), agents (ReAct, Plan-and-Execute), memory, and callbacks. LangServe exposes chains as REST APIs, while LangSmith provides observability. The ecosystem has over 700 integrations. LCEL enables streaming, batching, and async by default. LangGraph extends the framework with cyclic execution for agent workflows.

## Key Concepts

- **LCEL** — Declarative composition language unifying streaming, batching, and tracing
- **RAG** — Retrieval-Augmented Generation combining document retrieval with LLM generation
- **Agents** — Autonomous loops: observe-think-act with tool selection
- **LangGraph** — Graph-based state machine for complex agent orchestration
- **LangSmith** — Observability platform for LLM application debugging and evaluation

## Related Links

- https://python.langchain.com/docs/introduction/
- https://blog.langchain.dev/

---
*Auto-created by `scripts/ingest-source.py` — review abstract and concepts for accuracy.*