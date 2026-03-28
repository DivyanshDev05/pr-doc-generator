#!/usr/bin/env python3
"""
PR Doc Generator v1.2 — Multi-AI PR document generator.
Supports: Anthropic, OpenAI, Gemini (paid) | Groq, OpenRouter (free) | Ollama, LM Studio (local)
"""

import os
import sys
import time
import getpass
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box

from providers import PROVIDERS, providers_by_category, get_provider
from git_diff import GitDiffEngine
from doc_generator import DocGenerator
from doc_writer import DocWriter
from notifier import Notifier

console = Console()

BANNER = """
 ██████╗ ██████╗      ██████╗  ██████╗  ██████╗
 ██╔══██╗██╔══██╗     ██╔══██╗██╔═══██╗██╔════╝
 ██████╔╝██████╔╝     ██║  ██║██║   ██║██║
 ██╔═══╝ ██╔══██╗     ██║  ██║██║   ██║██║
 ██║     ██║  ██║     ██████╔╝╚██████╔╝╚██████╗
 ╚═╝     ╚═╝  ╚═╝     ╚═════╝  ╚═════╝  ╚═════╝
     Generator  v1.2  •  7 AI Providers
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def ok(msg):    console.print(f"  [bold green]✔[/bold green]  {msg}")
def info(msg):  console.print(f"  [cyan]ℹ[/cyan]  {msg}")
def warn(msg):  console.print(f"  [yellow]⚠[/yellow]  {msg}", style="yellow")
def err(msg):   console.print(f"  [bold red]✖[/bold red]  {msg}", style="bold red")


def confirm_git_command(command):
    console.print(f"\n  [bold yellow]⚡  Git command to run:[/bold yellow]")
    console.print(f"     [bold]$ {command}[/bold]")
    return Confirm.ask("  Run this command?", default=False)


def resolve_template_path(project_root, user_provided=None):
    if user_provided and os.path.isfile(user_provided):
        return user_provided
    default = os.path.join(project_root, "pr_template.md")
    if os.path.isfile(default):
        return default
    bundled = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "pr_template.md")
    )
    if os.path.isfile(bundled):
        info("No pr_template.md in project root — using bundled template.")
        return bundled
    raise FileNotFoundError(
        "No PR template found. Place pr_template.md in your project root or pass --template."
    )


# ── Provider selection ────────────────────────────────────────────────────────

CATEGORY_STYLES = {
    "paid":  ("💳", "cyan",   "Paid — requires API credits"),
    "free":  ("🆓", "green",  "Free — API key required, no credit card"),
    "local": ("💻", "yellow", "Local — runs on your machine, no internet"),
}


def pick_provider_interactive():
    """
    Step 1: Ask the category (paid / free / local).
    Step 2: Show only providers in that category and let the user pick.
    Step 3: Ask the model.
    Step 4: Ask for the API key (or confirm no key needed).
    Returns (provider_key, api_key, model).
    """
    groups = providers_by_category()

    # ── Category picker ───────────────────────────────────────────────────────
    console.print()
    cat_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    cat_table.add_column("", style="bold", width=4)
    cat_table.add_column("", width=8)
    cat_table.add_column("")
    cat_table.add_column("", style="dim")

    cat_keys = ["paid", "free", "local"]
    for i, cat in enumerate(cat_keys, 1):
        icon, color, desc = CATEGORY_STYLES[cat]
        providers_in_cat = ", ".join(
            p["label"].split("  ")[0] for p in groups[cat].values()
        )
        cat_table.add_row(
            f"[{color}]{i}[/{color}]",
            f"[bold {color}]{icon} {cat.upper()}[/bold {color}]",
            desc,
            f"({providers_in_cat})",
        )

    console.print(cat_table)
    cat_choice = Prompt.ask(
        "  [bold]Which type of AI do you want to use?[/bold]",
        choices=["1", "2", "3"],
        default="1",
    )
    chosen_category = cat_keys[int(cat_choice) - 1]
    cat_providers = groups[chosen_category]

    # ── Provider picker ───────────────────────────────────────────────────────
    console.print()
    prov_table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    prov_table.add_column("#", width=3)
    prov_table.add_column("Provider")
    prov_table.add_column("Description")
    prov_table.add_column("Get key", style="dim")

    prov_keys = list(cat_providers.keys())
    for i, key in enumerate(prov_keys, 1):
        p = cat_providers[key]
        note = p.get("note", p.get("key_url", ""))
        prov_table.add_row(str(i), p["label"], p["description"], p.get("key_url", "—"))

    console.print(prov_table)
    prov_choice = Prompt.ask(
        "  [bold]Choose provider[/bold]",
        choices=[str(i) for i in range(1, len(prov_keys) + 1)],
        default="1",
    )
    provider_key = prov_keys[int(prov_choice) - 1]
    provider = get_provider(provider_key)

    # ── Special note for local providers ─────────────────────────────────────
    if provider.get("note"):
        console.print(f"\n  [yellow]ℹ  Note:[/yellow] {provider['note']}")

    # ── Model picker ──────────────────────────────────────────────────────────
    models = provider["models"]
    console.print(f"\n  Available models for [bold]{provider['label']}[/bold]:")
    for i, m in enumerate(models, 1):
        tag = "  [dim](default)[/dim]" if m == provider["default_model"] else ""
        console.print(f"    [dim]{i}.[/dim]  {m}{tag}")

    model_choice = Prompt.ask(
        "  [bold]Choose model[/bold]",
        choices=[str(i) for i in range(1, len(models) + 1)],
        default="1",
    )
    model = models[int(model_choice) - 1]

    # ── API key ───────────────────────────────────────────────────────────────
    api_key = ""
    if provider["key_env"]:
        api_key = os.environ.get(provider["key_env"], "").strip()
        if api_key:
            ok(f"{provider['key_env']} found in environment.")
        else:
            console.print(f"\n  [dim]Get your key at: {provider['key_url']}[/dim]")
            api_key = getpass.getpass(
                f"  Enter your {provider['label'].split('  ')[0]} API key ({provider['key_hint']}): "
            ).strip()
            if not api_key:
                err("API key is required. Exiting.")
                sys.exit(1)
    else:
        info("No API key needed for local provider.")

    ok(f"Using [bold]{provider['label']}[/bold] — {model}")
    return provider_key, api_key, model


# ── Args ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a PR document from git diff using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Providers (--provider):
  PAID:   anthropic | openai | gemini
  FREE:   groq | openrouter
  LOCAL:  ollama | lmstudio

Examples:
  python main.py
  python main.py --project /path/to/repo --base main
  python main.py --provider groq --model llama-3.3-70b-versatile
  python main.py --provider ollama --model llama3.3
        """,
    )
    parser.add_argument("--project",  help="Path to the git project root")
    parser.add_argument("--base",     help="Base branch to diff against (e.g. main, develop)")
    parser.add_argument("--provider", choices=list(PROVIDERS), help="AI provider key")
    parser.add_argument("--model",    help="Model name override")
    parser.add_argument("--template", help="Path to PR markdown template")
    parser.add_argument("--output",   help="Output directory for the generated doc")
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    console.print(Panel(BANNER, style="bold cyan", expand=False))
    args = parse_args()
    notifier = Notifier()

    # ── Step 1: Project path ─────────────────────────────────────────────────
    console.rule("[bold]Step 1 — Project")
    project_root = args.project or Prompt.ask(
        "  [bold cyan]📁 Path to your git project[/bold cyan]",
        default=os.getcwd(),
    )
    project_root = os.path.abspath(project_root)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                  console=console, transient=True) as p:
        p.add_task("Verifying git repository...", total=None)
        time.sleep(0.3)
        if not os.path.isdir(project_root):
            err(f"Directory not found: {project_root}"); sys.exit(1)
        if not os.path.isdir(os.path.join(project_root, ".git")):
            err(f"Not a git repository: {project_root}"); sys.exit(1)

    ok(f"Project: {project_root}")

    # ── Step 2: AI provider ──────────────────────────────────────────────────
    console.rule("[bold]Step 2 — AI Provider")

    if args.provider:
        # Non-interactive: provider passed as flag
        provider_key = args.provider
        provider = get_provider(provider_key)
        if provider["key_env"]:
            api_key = os.environ.get(provider["key_env"], "").strip()
            if not api_key:
                api_key = getpass.getpass(
                    f"  Enter your {provider['label']} API key: "
                ).strip()
        else:
            api_key = ""
        model = args.model or provider["default_model"]
        if provider.get("note"):
            warn(provider["note"])
        ok(f"Using [bold]{provider['label']}[/bold] — {model}")
    else:
        provider_key, api_key, model = pick_provider_interactive()

    # ── Step 3: Git diff ─────────────────────────────────────────────────────
    console.rule("[bold]Step 3 — Git Diff")
    git = GitDiffEngine(project_root, confirm_callback=confirm_git_command)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                  console=console, transient=True) as p:
        p.add_task("Detecting current branch...", total=None)
        time.sleep(0.2)
        current_branch = git.current_branch()

    if not current_branch:
        err("Could not determine current branch."); sys.exit(1)
    ok(f"Current branch: [bold]{current_branch}[/bold]")

    base_branch = args.base or Prompt.ask(
        "  [bold cyan]🔀 Base branch to diff against[/bold cyan]", default="main"
    )
    ok(f"Diffing against: [bold]{base_branch}[/bold]")

    console.print()
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                  console=console, transient=True) as p:
        p.add_task(f"Fetching diff  {base_branch} → {current_branch}...", total=None)
        diff_result = git.get_diff(base_branch, current_branch)

    if diff_result.get("needs_password"):
        warn("Repository requires Bitbucket authentication.")
        app_password = getpass.getpass("  Enter your Bitbucket app password: ").strip()
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                      console=console, transient=True) as p:
            p.add_task("Retrying with credentials...", total=None)
            diff_result = git.get_diff(base_branch, current_branch, password=app_password)

    if not diff_result.get("diff"):
        warn("No diff found between branches. Nothing to document."); sys.exit(0)

    changed = diff_result.get("changed_files", [])
    ok(f"Diff ready — [bold]{len(changed)} file(s) changed[/bold]")
    for f in changed[:8]:
        console.print(f"     [dim]• {f}[/dim]")
    if len(changed) > 8:
        console.print(f"     [dim]  … and {len(changed) - 8} more[/dim]")

    # ── Step 4: Template ─────────────────────────────────────────────────────
    console.rule("[bold]Step 4 — Template")
    template_path = resolve_template_path(project_root, args.template)
    ok(f"Template: {template_path}")
    with open(template_path) as f:
        template_content = f.read()

    # ── Step 5: Generate ─────────────────────────────────────────────────────
    console.rule("[bold]Step 5 — Generating PR Document")
    generator = DocGenerator(provider_key=provider_key, api_key=api_key, model=model)
    pr_doc = generator.generate(
        diff=diff_result["diff"],
        template=template_content,
        branch_name=current_branch,
        base_branch=base_branch,
        changed_files=changed,
    )

    # ── Step 6: Save ─────────────────────────────────────────────────────────
    console.rule("[bold]Step 6 — Saving")
    output_dir = args.output or os.path.join(project_root, "output")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                  console=console, transient=True) as p:
        p.add_task("Writing document to disk...", total=None)
        writer = DocWriter(output_dir=output_dir)
        output_path = writer.write(content=pr_doc, branch_name=current_branch)
        time.sleep(0.2)

    ok(f"Saved: [bold]{output_path}[/bold]")

    # ── Step 7: Notify ────────────────────────────────────────────────────────
    provider_label = get_provider(provider_key)["label"]
    notifier.notify(
        title="PR Doc Ready ✅",
        message=f"Branch: {current_branch}\n{output_path}",
        output_path=output_path,
    )

    console.print()
    console.print(Panel(
        f"[bold green]✅  Done![/bold green]\n\n"
        f"[bold]Branch:[/bold]   {current_branch}\n"
        f"[bold]Provider:[/bold] {provider_label} ({model})\n"
        f"[bold]Output:[/bold]   {output_path}",
        title="PR Doc Generator",
        style="green",
        expand=False,
    ))


if __name__ == "__main__":
    main()
