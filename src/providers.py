"""
providers.py — Single source of truth for every supported AI provider.

Categories:
  paid    — requires a paid subscription / API credits
  free    — genuinely free tier, no credit card needed
  local   — runs entirely on your own machine, no internet required

Adding a new provider in future:
  1. Add an entry to PROVIDERS dict below
  2. If it needs a special SDK (not openai-compatible), add a caller in doc_generator.py
  3. Rebuild the Docker image: docker build -t pr-doc-generator:latest .
"""

PROVIDERS = {

    # ── PAID PROVIDERS ───────────────────────────────────────────────────────

    "anthropic": {
        "label":        "Anthropic Claude",
        "category":     "paid",
        "description":  "Best quality. Claude Opus / Sonnet / Haiku.",
        "models": [
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5-20251001",
        ],
        "default_model": "claude-opus-4-5",
        "key_env":       "ANTHROPIC_API_KEY",
        "key_hint":      "sk-ant-api03-...",
        "key_url":       "https://console.anthropic.com/",
        "sdk":           "anthropic",   # uses anthropic SDK
        "base_url":      None,
    },

    "openai": {
        "label":        "OpenAI GPT",
        "category":     "paid",
        "description":  "GPT-4o and family. Pay-per-token.",
        "models": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4o-mini",
        ],
        "default_model": "gpt-4o",
        "key_env":       "OPENAI_API_KEY",
        "key_hint":      "sk-...",
        "key_url":       "https://platform.openai.com/api-keys",
        "sdk":           "openai_compat",
        "base_url":      "https://api.openai.com/v1",
    },

    "gemini": {
        "label":        "Google Gemini",
        "category":     "paid",
        "description":  "Gemini Pro / Flash. Free tier available (rate limited).",
        "models": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
        ],
        "default_model": "gemini-1.5-pro",
        "key_env":       "GOOGLE_API_KEY",
        "key_hint":      "AIza...",
        "key_url":       "https://aistudio.google.com/app/apikey",
        "sdk":           "gemini",      # uses google-generativeai SDK
        "base_url":      None,
    },

    # ── FREE PROVIDERS (API key required, no credit card) ────────────────────

    "groq": {
        "label":        "Groq  🆓",
        "category":     "free",
        "description":  "14,400 free requests/day. Extremely fast LPU inference.",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
            "gemma2-9b-it",
        ],
        "default_model": "llama-3.3-70b-versatile",
        "key_env":       "GROQ_API_KEY",
        "key_hint":      "gsk_...",
        "key_url":       "https://console.groq.com/keys",
        "sdk":           "openai_compat",
        "base_url":      "https://api.groq.com/openai/v1",
    },

    "openrouter": {
        "label":        "OpenRouter  🆓",
        "category":     "free",
        "description":  "Access 100s of models. Many are free. $5 signup credit.",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-2-9b-it:free",
            "deepseek/deepseek-r1:free",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "key_env":       "OPENROUTER_API_KEY",
        "key_hint":      "sk-or-...",
        "key_url":       "https://openrouter.ai/keys",
        "sdk":           "openai_compat",
        "base_url":      "https://openrouter.ai/api/v1",
    },

    # ── LOCAL PROVIDERS (no API key, no internet, runs on your machine) ──────

    "ollama": {
        "label":        "Ollama  💻 (local)",
        "category":     "local",
        "description":  "Run models locally. Free, private, offline. Must have Ollama installed on your host.",
        "models": [
            "llama3.3",
            "llama3.1",
            "mistral",
            "deepseek-coder-v2",
            "phi4",
            "gemma3",
            "qwen2.5-coder",
        ],
        "default_model": "llama3.3",
        "key_env":       None,          # no key needed
        "key_hint":      None,
        "key_url":       "https://ollama.com/",
        "sdk":           "openai_compat",
        "base_url":      "http://host.docker.internal:11434/v1",  # Docker → host
        "extra_headers": {},
        "note":          "Make sure Ollama is running on your host machine (ollama serve) and the model is pulled (ollama pull llama3.3).",
    },

    "lmstudio": {
        "label":        "LM Studio  💻 (local)",
        "category":     "local",
        "description":  "GUI app for running local models. OpenAI-compatible server.",
        "models": [
            "local-model",       # LM Studio uses whatever is loaded — name doesn't matter
        ],
        "default_model": "local-model",
        "key_env":       None,
        "key_hint":      None,
        "key_url":       "https://lmstudio.ai/",
        "sdk":           "openai_compat",
        "base_url":      "http://host.docker.internal:1234/v1",
        "note":          "Start LM Studio, load a model, and enable the local server (port 1234) before running.",
    },
}


def providers_by_category() -> dict:
    """Return providers grouped by category."""
    groups = {"paid": {}, "free": {}, "local": {}}
    for key, p in PROVIDERS.items():
        groups[p["category"]][key] = p
    return groups


def get_provider(key: str) -> dict:
    if key not in PROVIDERS:
        raise ValueError(f"Unknown provider '{key}'. Available: {list(PROVIDERS)}")
    return PROVIDERS[key]
