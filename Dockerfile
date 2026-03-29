# ─────────────────────────────────────────────────────────────────────────────
#  PR Doc Generator — Dockerfile
#
#  Build args:
#    AI_PROVIDER  — which AI SDK to install (default: all)
#                   Values: all | anthropic | openai | gemini | groq | openrouter | ollama | lmstudio
#
#  Examples:
#    docker build -t pr-doc-generator .                          # installs all SDKs
#    docker build --build-arg AI_PROVIDER=anthropic -t pr-doc-generator .
#    docker build --build-arg AI_PROVIDER=groq -t pr-doc-generator .
#    docker build --build-arg AI_PROVIDER=ollama -t pr-doc-generator .
#
#  To switch provider later: rebuild with a different AI_PROVIDER arg.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

ARG AI_PROVIDER=all
ENV AI_PROVIDER=${AI_PROVIDER}

LABEL maintainer="your-team"
LABEL description="PR Doc Generator — Multi-AI PR document generator"

# ── System dependencies (each checked before installing) ─────────────────────
RUN echo "" \
    && echo "════════════════════════════════════════" \
    && echo "  PR Doc Generator — Dependency Setup   " \
    && echo "════════════════════════════════════════" \
    && echo "" \
    && echo "▶  Updating package index..." \
    && apt-get update -qq \
    && echo "✔  Package index updated." \
    \
    && for pkg in git curl ca-certificates; do \
         echo "▶  Checking: ${pkg}..."; \
         if dpkg -s ${pkg} >/dev/null 2>&1; then \
           echo "✔  ${pkg} already present — skipping."; \
         else \
           echo "   Installing ${pkg}..."; \
           apt-get install -y --no-install-recommends ${pkg} \
             && echo "✔  ${pkg} installed."; \
         fi; \
       done \
    \
    && echo "▶  Checking: libnotify-bin (desktop notifications)..." \
    && if dpkg -s libnotify-bin >/dev/null 2>&1; then \
         echo "✔  libnotify-bin already present — skipping."; \
       else \
         apt-get install -y --no-install-recommends libnotify-bin 2>/dev/null \
           && echo "✔  libnotify-bin installed." \
           || echo "⚠  libnotify-bin unavailable on this OS — terminal alerts will be used instead."; \
       fi \
    \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && echo "✔  System dependencies ready."

WORKDIR /app

# ── Python base deps (always installed) ──────────────────────────────────────
COPY requirements-base.txt .

RUN echo "" \
    && echo "▶  Upgrading pip..." \
    && pip install --quiet --upgrade pip \
    && echo "✔  pip upgraded." \
    && echo "▶  Installing base Python dependencies..." \
    && pip install --no-cache-dir -r requirements-base.txt \
    && echo "✔  Base dependencies installed."

# ── AI provider SDK (selected at build time) ──────────────────────────────────
COPY requirements-providers/ ./requirements-providers/

RUN echo "" \
    && echo "▶  AI_PROVIDER = ${AI_PROVIDER}" \
    && if [ "${AI_PROVIDER}" = "all" ]; then \
         echo "   Installing ALL AI provider SDKs..."; \
         pip install --no-cache-dir -r requirements-providers/all.txt \
           && echo "✔  All AI SDKs installed."; \
       elif [ -f "requirements-providers/${AI_PROVIDER}.txt" ]; then \
         echo "   Installing SDK for: ${AI_PROVIDER}..."; \
         pip install --no-cache-dir -r "requirements-providers/${AI_PROVIDER}.txt" \
           && echo "✔  ${AI_PROVIDER} SDK installed."; \
       else \
         echo "✖  Unknown AI_PROVIDER: ${AI_PROVIDER}"; \
         echo "   Valid values: all, anthropic, openai, gemini, groq, openrouter, ollama, lmstudio"; \
         exit 1; \
       fi

# ── Verify installed packages ────────────────────────────────────────────────
RUN echo "" \
    && echo "▶  Verifying installed packages..." \
    && python -c "from importlib.metadata import version; print('  ✔  rich', version('rich'))" 2>/dev/null || python -c "import rich; print('  ✔  rich installed')" \
    && python -c "import plyer; print('  ✔  plyer ok')" \
    && if [ "${AI_PROVIDER}" = "all" ] || [ "${AI_PROVIDER}" = "anthropic" ]; then \
         python -c "import anthropic; print('  ✔  anthropic', anthropic.__version__)" 2>/dev/null || true; \
       fi \
    && if [ "${AI_PROVIDER}" = "all" ] || [ "${AI_PROVIDER}" = "openai" ] \
          || [ "${AI_PROVIDER}" = "groq" ] || [ "${AI_PROVIDER}" = "openrouter" ] \
          || [ "${AI_PROVIDER}" = "ollama" ] || [ "${AI_PROVIDER}" = "lmstudio" ]; then \
         python -c "import openai; print('  ✔  openai', openai.__version__)" 2>/dev/null || true; \
       fi \
    && if [ "${AI_PROVIDER}" = "all" ] || [ "${AI_PROVIDER}" = "gemini" ]; then \
         python -c "import google.generativeai; print('  ✔  google-generativeai ok')" 2>/dev/null || true; \
       fi \
    && echo "✔  Package verification complete."

# ── App source ────────────────────────────────────────────────────────────────
COPY src/       ./src/
COPY templates/ ./templates/
RUN mkdir -p /app/output

# ── Git trust ────────────────────────────────────────────────────────────────
RUN git config --global --add safe.directory /workspace \
    && git config --global --add safe.directory '*' \
    && echo "✔  Git safe directory configured."

ENV GIT_TERMINAL_PROMPT=0
ENV PYTHONUNBUFFERED=1

RUN echo "" \
    && echo "════════════════════════════════════════" \
    && echo "  Build complete!                       " \
    && echo "  Provider: ${AI_PROVIDER}              " \
    && echo "  To rebuild with a different provider: " \
    && echo "  docker build --build-arg AI_PROVIDER=groq -t pr-doc-generator ." \
    && echo "════════════════════════════════════════"

WORKDIR /app/src
ENTRYPOINT ["python", "main.py"]
