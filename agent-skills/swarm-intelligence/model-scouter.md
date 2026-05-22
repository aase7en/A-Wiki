# Model Scouter — Dynamic AI Model Capability Scouting

> **Purpose:** Aggressively scout for free/zero-cost/beta-tier AI models at runtime.
> The Iron Laws (discipline) are CONSTANT. The engines executing under them are DYNAMIC.

## Mandate

The Primary Agent MUST query model availability before beginning any session involving:

1. Background parallel execution (swarm allocation)
2. High-volume token consumption
3. Delegated sub-tasks that don't require the Primary Agent's reasoning

## Scouting Sources

### Tier 1: OpenRouter Free Tier (Preferred)
- Query endpoint: `https://openrouter.ai/api/v1/models`
- Filter for models with `pricing.prompt = "0"` AND `pricing.completion = "0"`
- Check rate limits (requests/min, tokens/min)
- Prioritize models with high context window (>= 128K) for architect role
- Prioritize models with high speed (tokens/sec) for executioner role

### Tier 2: Web Search (Fallback)
- Search terms:
  - "free AI API beta 2025 2026 no credit card"
  - "openrouter free models list"
  - "free LLM API tier promotional"
  - "zero-cost AI model hosting"
- Cross-reference availability, rate limits, and context window from official docs

### Tier 3: Local / Self-Hosted
- Ollama models running on local hardware
- Quantized models (GGUF, AWQ) for offline execution
- Check `http://localhost:11434/api/tags` for available models

## Scouting Output Format

```json
{
  "scouted_at": "YYYY-MM-DD HH:MM UTC+7",
  "available_models": [
    {
      "id": "model-provider/name",
      "provider": "openrouter/local/huggingface",
      "tier": "free/beta/paid",
      "context_window": 128000,
      "speed": "fast/medium/slow",
      "strength": "reasoning/coding/chat",
      "rate_limit": "30 req/min"
    }
  ],
  "recommendation": {
    "architect": "model-id-for-planning-and-root-cause",
    "executioner": "model-id-for-code-generation",
    "critic": "primary-agent"  // Iron Law: Primary Agent always validates
  }
}
```

## Critical Constraints

- **Scouting shall not exceed 30 seconds.** If no free models found within timeout, fall back to cheapest available.
- **Never hardcode model names.** Always scout dynamically.
- **The Primary Agent (Senior Critic) is NOT delegatable.** It always validates against Iron Laws.
