#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  setup.sh  —  Interactive first-time setup for PR Doc Generator
#
#  Usage:
#    ./setup.sh                   # interactive wizard
#    ./setup.sh --quick groq      # non-interactive with provider preset
#    ./setup.sh --rebuild         # rebuild Docker image
#    ./setup.sh --uninstall       # remove Docker image + optional files
#
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="pr-doc-generator"

VALID_PROVIDERS=("all" "anthropic" "openai" "gemini" "groq" "openrouter" "ollama" "lmstudio")

show_banner() {
    echo ""
    echo "  ╔════════════════════════════════════════╗"
    echo "  ║     PR Doc Generator — Setup            ║"
    echo "  ╚════════════════════════════════════════╝"
    echo ""
}

show_help() {
    echo "Usage: ./setup.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install             Run interactive setup wizard (default)"
    echo "  --quick PROVIDER      Non-interactive setup with provider preset"
    echo "                         Valid: all, anthropic, openai, gemini, groq, openrouter, ollama, lmstudio"
    echo "  --rebuild             Rebuild Docker image"
    echo "  --uninstall           Remove Docker image and optional files"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh                                    # interactive"
    echo "  ./setup.sh --quick groq                       # free, no key needed"
    echo "  ./setup.sh --quick anthropic                  # paid, will ask for key"
    echo "  ./setup.sh --quick ollama                      # local, will check host"
    echo "  ./setup.sh --uninstall                        # remove everything"
}

check_prerequisites() {
    echo "  ▶ Checking prerequisites..."
    
    if ! command -v docker &>/dev/null; then
        echo "  ✖  Docker is not installed."
        echo ""
        echo "  Please install Docker first:"
        echo "    • macOS:     https://docs.docker.com/desktop/install/mac-install/"
        echo "    • Windows:  https://docs.docker.com/desktop/install/windows-install/"
        echo "    • Linux:    https://docs.docker.com/engine/install/"
        echo ""
        exit 1
    fi
    
    if ! docker info &>/dev/null; then
        echo "  ✖  Docker is not running."
        echo ""
        echo "  Please start Docker Desktop (macOS/Windows) or Docker daemon (Linux)."
        echo ""
        exit 1
    fi
    
    echo "  ✔  Docker is installed and running."
}

check_current_image() {
    local provider="$1"
    local image_tag="${IMAGE_NAME}:${provider}"
    
    if docker image inspect "${image_tag}" &>/dev/null; then
        return 0  # image exists
    fi
    return 1  # image does not exist
}

get_current_provider() {
    local image_tag="${IMAGE_NAME}:all"
    
    if docker image inspect "${image_tag}" &>/dev/null; then
        echo "all"
        return
    fi
    
    for prov in "${VALID_PROVIDERS[@]}"; do
        if docker image inspect "${IMAGE_NAME}:${prov}" &>/dev/null; then
            echo "$prov"
            return
        fi
    done
    
    echo "none"
}

show_provider_menu() {
    cat <<'EOF'
  Select your AI provider:

  #  │ Type    │ Cost           │ Key needed?
  ───┼─────────┼────────────────┼────────────
  1  │ Paid    │ Pay-per-token  │ Yes — Anthropic Claude
  2  │ Paid    │ Pay-per-token  │ Yes — OpenAI GPT
  3  │ Paid    │ Free tier      │ Yes — Google Gemini
  4  │ Free    │ 14,400 req/day │ Yes — Groq (recommended)
  5  │ Free    │ Many free      │ Yes — OpenRouter
  6  │ Local   │ 100% free      │ No — Ollama
  7  │ Local   │ 100% free      │ No — LM Studio
  8  │ All     │ Everything     │ Depends on use
EOF
    echo ""
    
    local choice
    read -p "  Enter your choice (1-8): " choice
    
    case "$choice" in
        1) PROVIDER_CHOICE="anthropic" ;;
        2) PROVIDER_CHOICE="openai" ;;
        3) PROVIDER_CHOICE="gemini" ;;
        4) PROVIDER_CHOICE="groq" ;;
        5) PROVIDER_CHOICE="openrouter" ;;
        6) PROVIDER_CHOICE="ollama" ;;
        7) PROVIDER_CHOICE="lmstudio" ;;
        8) PROVIDER_CHOICE="all" ;;
        *) PROVIDER_CHOICE="groq" ;;
    esac
}

get_api_key_env_var() {
    local provider="$1"
    case "$provider" in
        anthropic) echo "ANTHROPIC_API_KEY" ;;
        openai) echo "OPENAI_API_KEY" ;;
        gemini) echo "GOOGLE_API_KEY" ;;
        groq) echo "GROQ_API_KEY" ;;
        openrouter) echo "OPENROUTER_API_KEY" ;;
        *) echo "" ;;
    esac
}

setup_api_key() {
    local provider="$1"
    local env_var
    env_var=$(get_api_key_env_var "$provider")
    
    if [[ -z "$env_var" ]]; then
        return 1  # no key needed
    fi
    
    echo ""
    echo "  Provider '$provider' requires an API key."
    echo "  Environment variable: $env_var"
    echo ""
    
    local existing_key=""
    if [[ -n "${!env_var:-}" ]]; then
        existing_key="***${!env_var: -4}"
    fi
    
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        local env_key
        env_key=$(grep "^${env_var}=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d'=' -f2-)
        if [[ -n "$env_key" ]]; then
            existing_key="***${env_key: -4}"
        fi
    fi
    
    if [[ -n "$existing_key" ]]; then
        echo "  Current key: $existing_key"
        echo ""
        read -p "  Keep existing key? [Y/n]: " keep
        if [[ "$keep" =~ ^[Nn]$ ]]; then
            :
        else
            return 0  # keep existing
        fi
    fi
    
    echo "  Get your free key at:"
    case "$provider" in
        anthropic) echo "    https://console.anthropic.com/keys" ;;
        openai) echo "    https://platform.openai.com/api-keys" ;;
        gemini) echo "    https://aistudio.google.com/app/apikey" ;;
        groq) echo "    https://console.groq.com/keys" ;;
        openrouter) echo "    https://openrouter.ai/keys" ;;
    esac
    echo ""
    
    read -p "  Enter your $env_var: " api_key
    
    if [[ -z "$api_key" ]]; then
        echo "  ✖  No API key provided. Skipping."
        return 1
    fi
    
    echo "" >> "$SCRIPT_DIR/.env"
    echo "# $env_var - added $(date +%Y-%m-%d)" >> "$SCRIPT_DIR/.env"
    echo "${env_var}=${api_key}" >> "$SCRIPT_DIR/.env"
    
    echo "  ✔  API key saved to .env"
    
    # Export for current session (in case we test immediately)
    export "$env_var"="$api_key"
    
    return 0
}

check_local_ai_host() {
    local provider="$1"
    
    if [[ "$provider" != "ollama" && "$provider" != "lmstudio" ]]; then
        return 0
    fi
    
    echo ""
    echo "  ℹ  Local AI requires setup on your host machine (not in Docker)."
    echo ""
    
    if [[ "$provider" == "ollama" ]]; then
        if command -v ollama &>/dev/null; then
            echo "  ✔  Ollama is installed."
            
            if curl -s http://localhost:11434/api/version &>/dev/null; then
                echo "  ✔  Ollama server is running."
            else
                echo "  ⚠  Ollama is installed but not running."
                echo "     Run: ollama serve"
            fi
        else
            echo "  ⚠  Ollama is not installed on your host."
            echo ""
            echo "  Install instructions:"
            echo "    curl -fsSL https://ollama.com/install.sh | sh"
            echo ""
            echo "  Then pull a model:"
            echo "    ollama pull llama3.3       # 4.7GB — recommended"
            echo "    ollama pull mistral        # 4.1GB — faster"
            echo ""
            echo "  Then start the server:"
            echo "    ollama serve"
        fi
    elif [[ "$provider" == "lmstudio" ]]; then
        echo "  ℹ  LM Studio must be downloaded and run manually."
        echo ""
        echo "  Steps:"
        echo "    1. Download from https://lmstudio.ai/"
        echo "    2. Download a model in the app"
        echo "    3. Go to 'Local Server' tab → Start server (port 1234)"
        echo ""
        
        if curl -s http://localhost:1234/v1/models &>/dev/null; then
            echo "  ✔  LM Studio server is running."
        else
            echo "  ⚠  LM Studio server is not running."
            echo "     Start it in the app → Local Server tab"
        fi
    fi
    
    echo ""
    read -p "  Continue with setup? [Y/n]: " cont
    if [[ "$cont" =~ ^[Nn]$ ]]; then
        echo "  Setup cancelled."
        exit 0
    fi
}

add_to_gitignore() {
    if [[ ! -f "$SCRIPT_DIR/.gitignore" ]]; then
        touch "$SCRIPT_DIR/.gitignore"
    fi
    
    if ! grep -q "^\\.env$" "$SCRIPT_DIR/.gitignore" 2>/dev/null; then
        echo ".env" >> "$SCRIPT_DIR/.gitignore"
        echo "  ✔  Added .env to .gitignore"
    fi
}

build_image() {
    local provider="$1"
    local image_tag="${IMAGE_NAME}:${provider}"
    
    echo ""
    echo "  ▶  Building Docker image (AI_PROVIDER=$provider)..."
    echo "     This installs only the SDK you need — faster and leaner."
    echo ""
    
    docker build \
        --progress=plain \
        --build-arg "AI_PROVIDER=${provider}" \
        -t "${image_tag}" \
        -t "${IMAGE_NAME}:latest" \
        "$SCRIPT_DIR"
    
    echo ""
    echo "  ✔  Image built: ${image_tag}"
}

test_connection() {
    local provider="$1"
    
    echo ""
    echo "  ▶  Testing connectivity..."
    
    # For local AI, test localhost
    if [[ "$provider" == "ollama" ]]; then
        if curl -s http://localhost:11434/api/version &>/dev/null; then
            echo "  ✔  Ollama server is reachable."
            return 0
        else
            echo "  ⚠  Cannot reach Ollama server. Is it running?"
            return 1
        fi
    elif [[ "$provider" == "lmstudio" ]]; then
        if curl -s http://localhost:1234/v1/models &>/dev/null; then
            echo "  ✔  LM Studio server is reachable."
            return 0
        else
            echo "  ⚠  Cannot reach LM Studio server. Is it running?"
            return 1
        fi
    fi
    
    # For cloud providers, test with a simple call
    local env_var
    env_var=$(get_api_key_env_var "$provider")
    
    if [[ -z "$env_var" ]]; then
        echo "  ✔  No API key needed for this provider."
        return 0
    fi
    
    # Check if we have the key
    local api_key=""
    if [[ -n "${!env_var:-}" ]]; then
        api_key="${!env_var}"
    elif [[ -f "$SCRIPT_DIR/.env" ]]; then
        api_key=$(grep "^${env_var}=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d'=' -f2-)
    fi
    
    if [[ -z "$api_key" ]]; then
        echo "  ⚠  No API key found. Skipping connectivity test."
        echo "     Set $env_var or add it to .env to test."
        return 0
    fi
    
    # Simple test based on provider
    case "$provider" in
        anthropic)
            if curl -s -X POST "https://api.anthropic.com/v1/messages" \
                -H "x-api-key: $api_key" \
                -H "anthropic-version: 2023-06-01" \
                -H "content-type: application/json" \
                -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' \
                2>/dev/null | grep -q "id"; then
                echo "  ✔  API key is valid."
                return 0
            fi
            ;;
        openai)
            if curl -s -H "Authorization: Bearer $api_key" \
                "https://api.openai.com/v1/models" 2>/dev/null | grep -q "data"; then
                echo "  ✔  API key is valid."
                return 0
            fi
            ;;
        groq)
            if curl -s -H "Authorization: Bearer $api_key" \
                "https://api.groq.com/openai/v1/models" 2>/dev/null | grep -q "data"; then
                echo "  ✔  API key is valid."
                return 0
            fi
            ;;
        openrouter)
            if curl -s -H "Authorization: Bearer $api_key" \
                "https://openrouter.ai/api/v1/models" 2>/dev/null | grep -q "data"; then
                echo "  ✔  API key is valid."
                return 0
            fi
            ;;
        gemini)
            echo "  ℹ  Skipping Gemini connectivity test (requires specific setup)."
            ;;
    esac
    
    echo "  ⚠  Could not verify API key. It may be invalid or network issue."
    return 1
}

show_next_steps() {
    local provider="$1"
    
    echo ""
    echo "  ═════════════════════════════════════════"
    echo "  ✔  Setup complete!"
    echo "  ═════════════════════════════════════════"
    echo ""
    echo "  Next steps:"
    echo ""
    echo "  1. Run the generator:"
    echo "       ./generate-pr-doc.sh"
    echo ""
    echo "     Or with arguments:"
    echo "       ./generate-pr-doc.sh /path/to/your/project <base-branch>"
    echo ""
    echo "       # Example: ./generate-pr-doc.sh . main"
    echo "       # <base-branch> = branch to compare against (main, develop, master, etc.)"
    echo ""
    
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        echo "  2. Your API key is saved in .env"
        echo "     To use in current shell: source .env"
        echo ""
    fi
    
    if [[ "$provider" == "ollama" ]]; then
        echo "  ℹ  Make sure Ollama is running: ollama serve"
    elif [[ "$provider" == "lmstudio" ]]; then
        echo "  ℹ  Make sure LM Studio server is running (port 1234)"
    fi
    
    echo ""
}

do_uninstall() {
    echo ""
    echo "  ╔════════════════════════════════════════╗"
    echo "  ║     PR Doc Generator — Uninstall       ║"
    echo "  ╚════════════════════════════════════════╝"
    echo ""
    
    # Remove Docker images
    echo "  ▶  Removing Docker images..."
    local removed_any=0
    
    for prov in "${VALID_PROVIDERS[@]}"; do
        if docker image inspect "${IMAGE_NAME}:${prov}" &>/dev/null; then
            docker rmi "${IMAGE_NAME}:${prov}" 2>/dev/null || true
            echo "  ✔  Removed ${IMAGE_NAME}:${prov}"
            removed_any=1
        fi
    done
    
    if docker image inspect "${IMAGE_NAME}:latest" &>/dev/null; then
        docker rmi "${IMAGE_NAME}:latest" 2>/dev/null || true
        echo "  ✔  Removed ${IMAGE_NAME}:latest"
        removed_any=1
    fi
    
    if [[ $removed_any -eq 0 ]]; then
        echo "  ℹ  No Docker images found."
    fi
    
    # Ask about .env
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        echo ""
        read -p "  Delete .env file with API keys? [y/N]: " del_env
        if [[ "$del_env" =~ ^[Yy]$ ]]; then
            rm "$SCRIPT_DIR/.env"
            echo "  ✔  Removed .env"
        else
            echo "  ℹ  Kept .env"
        fi
    fi
    
    # Ask about output
    if [[ -d "$SCRIPT_DIR/output" ]]; then
        echo ""
        read -p "  Delete output/ folder? [y/N]: " del_output
        if [[ "$del_output" =~ ^[Yy]$ ]]; then
            rm -rf "$SCRIPT_DIR/output"
            echo "  ✔  Removed output/"
        else
            echo "  ℹ  Kept output/"
        fi
    fi
    
    echo ""
    echo "  ✔  Uninstall complete."
    echo ""
}

do_install() {
    local provider="$1"
    
    show_banner
    check_prerequisites
    
    # Check current state
    local current
    current=$(get_current_provider)
    
    if [[ "$current" != "none" ]]; then
        echo "  ℹ  Current provider: $current"
        echo ""
        read -p "  Rebuild or change provider? [Y/n]: " rebuild
        if [[ "$rebuild" =~ ^[Nn]$ ]]; then
            echo "  Exiting."
            exit 0
        fi
    fi
    
    # Setup API key if needed
    setup_api_key "$provider" || true
    
    # Check local AI host
    check_local_ai_host "$provider"
    
    # Add to gitignore
    add_to_gitignore
    
    # Build
    build_image "$provider"
    
    # Test connection
    test_connection "$provider" || true
    
    # Show next steps
    show_next_steps "$provider"
}

do_rebuild() {
    local provider="${1:-}"
    
    show_banner
    
    if [[ -z "$provider" ]]; then
        provider=$(get_current_provider)
        if [[ "$provider" == "none" ]]; then
            echo "  ✖  No image found. Run setup first."
            exit 1
        fi
        echo "  ℹ  Current provider: $provider"
    fi
    
    check_prerequisites
    
    echo ""
    read -p "  Rebuild with provider '$provider'? [Y/n]: " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo "  Cancelled."
        exit 0
    fi
    
    # Setup API key if needed
    setup_api_key "$provider" || true
    
    build_image "$provider"
    test_connection "$provider" || true
    
    echo ""
    echo "  ✔  Rebuild complete."
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
MODE="install"
PROVIDER=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install)
            MODE="install"
            shift
            ;;
        --quick)
            MODE="quick"
            PROVIDER="${2:-}"
            if [[ -z "$PROVIDER" ]]; then
                echo "Error: --quick requires a provider argument"
                echo "Valid: ${VALID_PROVIDERS[*]}"
                exit 1
            fi
            if [[ ! " ${VALID_PROVIDERS[*]} " =~ " ${PROVIDER} " ]]; then
                echo "Error: Invalid provider '$PROVIDER'"
                echo "Valid: ${VALID_PROVIDERS[*]}"
                exit 1
            fi
            shift 2
            ;;
        --rebuild)
            MODE="rebuild"
            shift
            ;;
        --uninstall)
            MODE="uninstall"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

case "$MODE" in
    install)
        if [[ -z "$PROVIDER" ]]; then
            show_provider_menu
            PROVIDER="$PROVIDER_CHOICE"
        fi
        do_install "$PROVIDER"
        ;;
    quick)
        do_install "$PROVIDER"
        ;;
    rebuild)
        do_rebuild "$PROVIDER"
        ;;
    uninstall)
        do_uninstall
        ;;
esac
