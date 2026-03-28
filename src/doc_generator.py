"""
doc_generator.py — Calls the chosen AI provider to generate the PR document.
Supports all providers defined in providers.py.
"""

import threading
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text

from providers import PROVIDERS, get_provider

console = Console()

SYSTEM_PROMPT = """You are a senior software engineer writing a Pull Request document.
You will be given:
1. A git diff showing all code changes
2. A PR document template with sections to fill in
3. The branch name

Your job is to fill in the template accurately and thoroughly based only on what the diff shows.

Rules:
- Follow the template structure EXACTLY. Do not add or remove sections.
- Keep the template emoji headings, dividers, and checkbox formatting intact.
- For the PR Summary: write a single clear one-liner describing what this PR does.
- For Scope: list specifically what files/components changed (in scope) and what did NOT change (out of scope).
- For Problem Solved: infer the ticket/issue from the branch name if possible.
- For Code Changes Per File: list each changed file with a brief description.
- For Database Changes: check for SQL, migrations, schema changes. If none, check "No DB changes".
- For Post-Deployment Steps: infer from the diff (cache clears, config updates, restarts).
- For How to Test: concrete steps a QA engineer can follow WITHOUT developer help.
- Be specific — use actual file paths, method names, variable names from the diff.
- Do NOT hallucinate changes that are not in the diff.
- Output ONLY the filled-in markdown document. No preamble, no explanation.
"""


def _build_prompt(diff, template, branch_name, base_branch, changed_files):
    files_list = "\n".join(f"  - {f}" for f in changed_files) if changed_files else "  (see diff)"
    return f"""## Branch name
{branch_name}

## Base branch (diffed against)
{base_branch}

## Changed files
{files_list}

## PR Document Template (fill this in exactly)
{template}

## Git Diff
```diff
{diff}
```

Fill in the PR document template completely based on the diff above.
Name the document after the branch: `{branch_name}`
"""


# ── Provider callers ──────────────────────────────────────────────────────────

def _call_anthropic(provider, api_key, model, prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _call_openai_compat(provider, api_key, model, prompt):
    """Handles OpenAI, Groq, OpenRouter, Ollama, LM Studio — all OpenAI-compatible."""
    from openai import OpenAI
    kwargs = {
        "base_url": provider["base_url"],
        "api_key":  api_key or "no-key-needed",
    }
    if "openrouter.ai" in (provider.get("base_url") or ""):
        kwargs["default_headers"] = {
            "HTTP-Referer": "https://github.com/pr-doc-generator",
            "X-Title": "PR Doc Generator",
        }
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_gemini(provider, api_key, model, prompt):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model_name=model, system_instruction=SYSTEM_PROMPT)
    return client.generate_content(prompt).text.strip()


CALLERS = {
    "anthropic":     _call_anthropic,
    "openai_compat": _call_openai_compat,
    "gemini":        _call_gemini,
}


# ── Progress spinner ──────────────────────────────────────────────────────────

SPINNER_MESSAGES = [
    "Reading the diff...",
    "Analysing changed files...",
    "Identifying the problem context...",
    "Drafting PR summary...",
    "Filling in scope section...",
    "Writing code change details...",
    "Checking for database changes...",
    "Writing post-deployment steps...",
    "Writing how-to-test section...",
    "Polishing the document...",
    "Almost there...",
]


class ProgressSpinner:
    def __init__(self, label):
        self.label = label
        self._live = None
        self._stop = False

    def __enter__(self):
        self._stop = False

        def _animate():
            idx = 0
            while not self._stop:
                msg = SPINNER_MESSAGES[idx % len(SPINNER_MESSAGES)]
                text = Text()
                text.append(f"  🤖  {self.label}  ", style="bold cyan")
                text.append(f"⏳ {msg}", style="dim")
                if self._live:
                    self._live.update(text)
                idx += 1
                time.sleep(2.8)

        self._live = Live(Text("  Connecting to AI..."), console=console, refresh_per_second=4)
        self._live.__enter__()
        self._thread = threading.Thread(target=_animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop = True
        self._thread.join(timeout=1)
        self._live.__exit__(*args)


# ── Public class ──────────────────────────────────────────────────────────────

class DocGenerator:
    def __init__(self, provider_key, api_key, model):
        self.provider     = get_provider(provider_key)
        self.provider_key = provider_key
        self.api_key      = api_key
        self.model        = model

    def generate(self, diff, template, branch_name, base_branch, changed_files):
        prompt = _build_prompt(diff, template, branch_name, base_branch, changed_files)
        caller = CALLERS[self.provider["sdk"]]

        console.print(
            f"\n  [bold cyan]🤖  Generating via {self.provider['label']}[/bold cyan] "
            f"[dim]({self.model})[/dim]"
        )

        with ProgressSpinner(self.provider["label"]):
            content = caller(self.provider, self.api_key, self.model, prompt)

        console.print("  [bold green]✔  AI generation complete.[/bold green]")

        header = f"# PR DOCUMENT: {branch_name}\n\n"
        if not content.startswith("# PR DOCUMENT"):
            content = header + content
        return content
