#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  generate-pr-doc.sh  —  Convenience wrapper for PR Doc Generator
#
#  Usage:
#    ./generate-pr-doc.sh                                   # interactive
#    ./generate-pr-doc.sh /path/to/project main             # with args
#    ./generate-pr-doc.sh /path/to/project main groq        # specify provider
#
#  To rebuild with a specific AI provider SDK only:
#    AI_PROVIDER=groq ./generate-pr-doc.sh
#    AI_PROVIDER=ollama ./generate-pr-doc.sh
#    AI_PROVIDER=all ./generate-pr-doc.sh                  # install everything
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT="${1:-}"
BASE_BRANCH="${2:-}"
CLI_PROVIDER="${3:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_PROVIDER="${AI_PROVIDER:-all}"   # can be overridden via env

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║     PR Doc Generator  v1.2           ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# ── Build image if not present ────────────────────────────────────────────────
IMAGE_TAG="pr-doc-generator:${AI_PROVIDER}"

# Check for existing image: prefer 'latest', then specific provider, then build
if docker image inspect "pr-doc-generator:latest" &>/dev/null; then
  IMAGE_TAG="pr-doc-generator:latest"
  echo "  ✔  Using cached image: ${IMAGE_TAG}"
elif ! docker image inspect "${IMAGE_TAG}" &>/dev/null; then
  echo "  🔨 Building Docker image (AI_PROVIDER=${AI_PROVIDER})..."
  echo "     This installs only the SDK you need — faster and leaner."
  echo ""
  docker build \
    --progress=plain \
    --build-arg "AI_PROVIDER=${AI_PROVIDER}" \
    -t "${IMAGE_TAG}" \
    -t "pr-doc-generator:latest" \
    "$SCRIPT_DIR"
  echo ""
  echo "  ✔  Image built: ${IMAGE_TAG}"
else
  echo "  ✔  Using cached image: ${IMAGE_TAG}"
fi

# ── Build docker run args ─────────────────────────────────────────────────────
DOCKER_ARGS=(
  --rm
  -it
  --add-host=host.docker.internal:host-gateway   # lets container reach host (Ollama/LM Studio)
  -v "${PROJECT:-/tmp}:/workspace:rw"
)

# Mount .env file if it exists (for API keys)
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  DOCKER_ARGS+=(-v "$SCRIPT_DIR/.env:/app/.env:ro")
fi

# Pass whichever API keys are set in the shell environment
for KEY_ENV in ANTHROPIC_API_KEY OPENAI_API_KEY GOOGLE_API_KEY GROQ_API_KEY OPENROUTER_API_KEY; do
  if [[ -n "${!KEY_ENV:-}" ]]; then
    DOCKER_ARGS+=(-e "${KEY_ENV}=${!KEY_ENV}")
  fi
done

# ── App args ──────────────────────────────────────────────────────────────────
APP_ARGS=()
[[ -n "$PROJECT" ]]      && APP_ARGS+=(--project /workspace)
[[ -n "$BASE_BRANCH" ]]  && APP_ARGS+=(--base "$BASE_BRANCH")
[[ -n "$CLI_PROVIDER" ]] && APP_ARGS+=(--provider "$CLI_PROVIDER")

echo "  🚀 Starting PR Doc Generator..."
echo ""
docker run "${DOCKER_ARGS[@]}" "${IMAGE_TAG}" "${APP_ARGS[@]}"
