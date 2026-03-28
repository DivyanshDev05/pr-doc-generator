# PR Doc Generator  v1.3

Generate Markdown PR documents from git diff using AI.
**7 providers supported** — paid, free, and fully local.

## ✨ What's New in v1.3

- **Streaming responses** — watch tokens appear in real-time
- **Config file support** — save per-project settings
- **Error handling** — automatic retry with exponential backoff
- **Unit tests** — 46+ tests for reliability

---

## 🤖 Supported AI Providers

| # | Provider | Type | Cost | Key needed? |
|---|---|---|---|---|
| 1 | **Anthropic Claude** | Paid | Pay-per-token | Yes — [console.anthropic.com](https://console.anthropic.com) |
| 2 | **OpenAI GPT** | Paid | Pay-per-token | Yes — [platform.openai.com](https://platform.openai.com/api-keys) |
| 3 | **Google Gemini** | Paid | Free tier + paid | Yes — [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| 4 | **Groq** 🆓 | Free | 14,400 req/day free | Yes (no credit card) — [console.groq.com](https://console.groq.com/keys) |
| 5 | **OpenRouter** 🆓 | Free | Many free models | Yes (no credit card) — [openrouter.ai](https://openrouter.ai/keys) |
| 6 | **Ollama** 💻 | Local | 100% free | None — runs on your machine |
| 7 | **LM Studio** 💻 | Local | 100% free | None — runs on your machine |

---

## 🚀 Quick Start

### Step 1 — Build the Docker image

```bash
# Default — installs all AI SDKs (~200MB, works with any provider)
docker build -t pr-doc-generator .

# Or install only the SDK you need (faster, leaner image)
docker build --build-arg AI_PROVIDER=groq      -t pr-doc-generator .
docker build --build-arg AI_PROVIDER=anthropic  -t pr-doc-generator .
docker build --build-arg AI_PROVIDER=ollama     -t pr-doc-generator .
```

During build you will see every dependency checked and verified:
```
▶  Checking: git...
✔  git installed.
▶  AI_PROVIDER = groq
   Installing SDK for: groq...
✔  groq SDK installed.
▶  Verifying installed packages...
  ✔  rich 13.7.0
  ✔  openai 1.30.0
✔  Package verification complete.
```

### Step 2 — Run it

```bash
# Interactive — app walks you through provider, model, project, branch
./generate-pr-doc.sh

# With args
./generate-pr-doc.sh /path/to/your/project main

# Specify provider directly (skips the interactive menu)
./generate-pr-doc.sh /path/to/project develop groq
```

At runtime the app asks:

```
Which type of AI do you want to use?
  1  💳 PAID    — Best quality (Anthropic, OpenAI, Gemini)
  2  🆓 FREE    — No credit card needed (Groq, OpenRouter)
  3  💻 LOCAL   — Runs on your machine (Ollama, LM Studio)
```

---

## 🔑 API Keys

Set the env var for your provider, or just run the app — it will prompt securely.

```bash
export ANTHROPIC_API_KEY=sk-ant-...       # Claude
export OPENAI_API_KEY=sk-...              # GPT
export GOOGLE_API_KEY=AIza...             # Gemini
export GROQ_API_KEY=gsk_...              # Groq (free)
export OPENROUTER_API_KEY=sk-or-...      # OpenRouter (free)
# Ollama and LM Studio need no key
```

---

## 💻 Local AI Setup (Ollama / LM Studio)

### Ollama

```bash
# Install on your host machine (not in Docker)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.3       # 4.7GB — recommended
ollama pull mistral        # 4.1GB — faster, lighter
ollama pull phi4           # 9GB — good quality

# Make sure it's running
ollama serve
```

Then run the generator and choose **Ollama** — it connects automatically.

### LM Studio

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Download a model inside the app
3. Go to **Local Server** tab → Start server (port 1234)
4. Run the generator and choose **LM Studio**

---

## 🔄 Switching AI Provider

The Dockerfile uses a build arg to install only the SDK you need.

```bash
# Built with Groq but want to switch to Claude?
docker build --build-arg AI_PROVIDER=anthropic -t pr-doc-generator .

# Or just rebuild with all providers
docker build --build-arg AI_PROVIDER=all -t pr-doc-generator .
```

The shell script creates a separate image tag per provider so you can have multiple installed simultaneously:
- `pr-doc-generator:groq`
- `pr-doc-generator:anthropic`
- `pr-doc-generator:ollama`

---

## ⚙️ All CLI Options

```
python main.py [OPTIONS]

  --project   PATH      Path to your git project root
  --base      BRANCH    Base branch to diff against
  --provider  NAME      anthropic | openai | gemini | groq | openrouter | ollama | lmstudio
  --model     NAME      Model override (e.g. llama3.3, gpt-4o-mini)
  --template  PATH      Path to PR template (default: <project>/pr_template.md)
  --output    DIR       Output directory (default: <project>/output/)
  --no-stream           Disable streaming response (show spinner instead)
```

---

## ⚙️ Config File

Create a `.pr-doc-gen.yaml` file in your project root to save default settings:

```yaml
# .pr-doc-gen.yaml
provider: groq
model: llama-3.3-70b-versatile
base_branch: develop
output_dir: ./pr-docs
```

### Config Priority

Settings are loaded in this order (later overrides earlier):
1. Hardcoded defaults
2. `~/.pr-doc-gen.yaml` (home directory)
3. `./.pr-doc-gen.yaml` (project root)
4. CLI flags (highest priority)

### Example Config

```yaml
# For a specific project
provider: openai
model: gpt-4o-mini
base_branch: main
output_dir: ./pr-outputs
```

**Note:** API keys should NOT be in the config file. Use environment variables instead.

---

Place a `pr_template.md` in your **project root** and it's detected automatically:

```
your-project/
├── pr_template.md    ← drop it here
└── src/
```

The bundled template is used as a fallback.

---

## 🔄 Streaming Response

By default, the app streams AI response tokens in real-time — you'll see the PR document appear as it's being generated.

```bash
# Default: streaming enabled
python main.py

# Disable streaming (show spinner instead)
python main.py --no-stream
```

Streaming provides:
- Better perceived performance (see progress instantly)
- Transparency (know it's working)
- Ability to cancel if wrong response starts

---

## 🔒 Git Safety Rules

The tool **never** runs: `commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `checkout`, `switch`, `rm`, `clean`.

Every allowed command is shown to you before it runs and requires `y` to proceed.

---

## 📂 Project Structure

```
pr-doc-generator/
├── .pr-doc-gen.yaml.example       ← config template
├── Dockerfile                     ← AI_PROVIDER build arg controls which SDK is installed
├── docker-compose.yml
├── generate-pr-doc.sh             ← run this
├── requirements-base.txt          ← rich, plyer, pyyaml, pytest
├── requirements-providers/
│   ├── all.txt                    ← all SDKs
│   ├── anthropic.txt
│   ├── openai.txt
│   ├── gemini.txt
│   ├── groq.txt                   ← uses openai SDK with Groq base_url
│   ├── openrouter.txt             ← uses openai SDK with OpenRouter base_url
│   ├── ollama.txt                 ← uses openai SDK with localhost base_url
│   └── lmstudio.txt              ← uses openai SDK with localhost:1234
├── src/
│   ├── main.py                   ← CLI with rich UI and provider picker
│   ├── providers.py              ← single source of truth for all providers
│   ├── doc_generator.py          ← calls chosen provider's SDK with streaming
│   ├── config.py                 ← YAML config loader
│   ├── git_diff.py               ← safe git runner
│   ├── doc_writer.py             ← writes .md output
│   └── notifier.py               ← desktop + terminal notifications
├── tests/                        ← unit tests (46+ tests)
│   ├── test_config.py
│   ├── test_providers.py
│   └── test_git_diff.py
├── templates/
│   └── pr_template.md
└── output/                       ← generated docs land here
```

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pyyaml

# Run all tests
pytest

# Run a specific test file
pytest tests/test_providers.py

# Run a specific test
pytest tests/test_providers.py::TestGetProvider::test_get_provider_valid_groq
```

---

## ➕ Adding a New Provider in Future

1. Add an entry to `src/providers.py`
2. If it's OpenAI-compatible (most are), set `"sdk": "openai_compat"` and set `base_url`
3. Add a `requirements-providers/<name>.txt`
4. Rebuild: `docker build --build-arg AI_PROVIDER=<name> -t pr-doc-generator .`
