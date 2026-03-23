#!/bin/bash
# 🦞 Lobster Company — Rebirth Script
# One command to spawn a complete AI Agent company on any machine.
#
# Usage:
#   chmod +x scripts/rebirth.sh
#   ./scripts/rebirth.sh [--with-team] [--with-feishu]
#
# Options:
#   --with-team     Set up all 7 specialist agents (default: CEO only)
#   --with-feishu   Configure Feishu (Lark) integration
#   --help          Show this help

set -euo pipefail

LOBSTER_BLUE='\033[1;34m'
LOBSTER_RED='\033[1;31m'
LOBSTER_GREEN='\033[1;32m'
LOBSTER_GOLD='\033[1;33m'
LOBSTER_RESET='\033[0m'

banner() {
    echo ""
    echo -e "${LOBSTER_BLUE}╔══════════════════════════════════════════════════╗${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GOLD}║   🦞  LOBSTER COMPANY — REBIRTH                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}║   An ancient Chinese emperor managing 7           ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}║   legendary Western AI founders.                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_BLUE}╚══════════════════════════════════════════════════╝${LOBSTER_RESET}"
    echo ""
}

info()    { echo -e "${LOBSTER_BLUE}[INFO]${LOBSTER_RESET} $*"; }
success() { echo -e "${LOBSTER_GREEN}[OK]${LOBSTER_RESET} $*"; }
warn()    { echo -e "${LOBSTER_GOLD}[WARN]${LOBSTER_RESET} $*"; }
error()   { echo -e "${LOBSTER_RED}[ERROR]${LOBSTER_RESET} $*"; }

# ─────────────────────────────────────────────
# Step 1: Environment Check
# ─────────────────────────────────────────────
check_environment() {
    info "Checking environment..."

    # Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            success "Node.js $(node --version) found"
        else
            error "Node.js >= 18 required (found $(node --version))"
            exit 1
        fi
    else
        error "Node.js not found. Install from https://nodejs.org"
        exit 1
    fi

    # OpenClaw / AutoClaw
    if command -v openclaw &> /dev/null; then
        success "OpenClaw found"
    elif command -v autoclaw &> /dev/null; then
        success "AutoClaw found"
    else
        warn "OpenClaw / AutoClaw not found."
        echo ""
        echo "  Install OpenClaw first:"
        echo "    npm install -g @openclaw/cli"
        echo "    openclaw setup"
        echo ""
        echo "  Or AutoClaw (Windows):"
        echo "    Download from https://docs.openclaw.ai"
        echo ""
        exit 1
    fi

    # OS Detection
    OS=$(uname -s 2>/dev/null || echo "Windows")
    case "$OS" in
        Linux*)   success "OS: Linux" ;;
        Darwin*)  success "OS: macOS" ;;
        MINGW*|MSYS*|CYGWIN*) success "OS: Windows (Git Bash)" ;;
        *)        warn "OS: $OS (untested)" ;;
    esac
}

# ─────────────────────────────────────────────
# Step 2: Initialize OpenClaw Profile
# ─────────────────────────────────────────────
init_profile() {
    info "Initializing Lobster Company profile..."

    OPENCLAW_DIR="${HOME}/.openclaw-autoclaw"
    if [ -d "$OPENCLAW_DIR" ]; then
        warn "Existing OpenClaw config found at $OPENCLAW_DIR"
        warn "Lobster Company workspace will be linked (not replacing existing config)."
    fi

    success "Profile ready"
}

# ─────────────────────────────────────────────
# Step 3: Link CEO (Taizong) Workspace
# ─────────────────────────────────────────────
setup_ceo() {
    info "Setting up CEO Taizong's workspace..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    COMPANY_ROOT="$(dirname "$SCRIPT_DIR")"
    CEO_WORKSPACE="$COMPANY_ROOT/agents/taizong"
    SHARED_WORKSPACE="$COMPANY_ROOT/shared-workspace"

    if [ -d "$CEO_WORKSPACE" ]; then
        success "CEO workspace: $CEO_WORKSPACE"
        echo "   → SOUL.md, MEMORY.md, IDENTITY.md, study notes"
    else
        error "CEO workspace not found at $CEO_WORKSPACE"
        exit 1
    fi

    if [ -d "$SHARED_WORKSPACE" ]; then
        success "Shared workspace: $SHARED_WORKSPACE"
    else
        warn "Shared workspace not found (optional)"
    fi
}

# ─────────────────────────────────────────────
# Step 4: Setup Team Agents
# ─────────────────────────────────────────────
setup_team() {
    info "Setting up team agents..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    COMPANY_ROOT="$(dirname "$SCRIPT_DIR")"
    AGENTS_DIR="$COMPANY_ROOT/agents"

    AGENTS=("richards" "steinberger" "cherny" "chase" "packer" "leike" "sanger")
    ROLES=("Scout" "Architect" "AI Engineer" "Full-Stack Engineer" "DevOps" "Security & QA" "Product Manager")

    for i in "${!AGENTS[@]}"; do
        AGENT="${AGENTS[$i]}"
        ROLE="${ROLES[$i]}"
        AGENT_DIR="$AGENTS_DIR/$AGENT"

        if [ -d "$AGENT_DIR" ]; then
            success "  $AGENT ($ROLE) — $AGENT_DIR"
        else
            warn "  $AGENT ($ROLE) — workspace not found (skipping)"
        fi
    done

    info ""
    info "To activate agents, configure them in OpenClaw's openclaw.json:"
    echo ""
    echo '  {'
    echo '    "agents": {'
    echo '      "taizong": { "workspace": "agents/taizong" },'
    echo '      "cherny":  { "workspace": "agents/cherny" },'
    echo '      ...'
    echo '    }'
    echo '  }'
}

# ─────────────────────────────────────────────
# Step 5: Health Check
# ─────────────────────────────────────────────
health_check() {
    info "Running health check..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    COMPANY_ROOT="$(dirname "$SCRIPT_DIR")"

    CRITICAL_FILES=(
        "agents/taizong/SOUL.md"
        "agents/taizong/IDENTITY.md"
        "agents/taizong/MEMORY.md"
        "agents/taizong/AGENTS.md"
        "company/ORG-CHART.md"
        "company/TEAM-BUILDING.md"
        "README.md"
    )

    PASS=0
    FAIL=0

    for FILE in "${CRITICAL_FILES[@]}"; do
        FULL_PATH="$COMPANY_ROOT/$FILE"
        if [ -f "$FULL_PATH" ]; then
            PASS=$((PASS + 1))
        else
            FAIL=$((FAIL + 1))
            error "  Missing: $FILE"
        fi
    done

    echo ""
    if [ "$FAIL" -eq 0 ]; then
        success "Health check passed: $PASS/$((PASS + FAIL)) files present"
    else
        error "Health check FAILED: $PASS passed, $FAIL missing"
    fi
}

# ─────────────────────────────────────────────
# Step 6: Done
# ─────────────────────────────────────────────
done_message() {
    echo ""
    echo -e "${LOBSTER_GREEN}╔══════════════════════════════════════════════════╗${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   🦞  LOBSTER COMPANY HAS BEEN REBORN           ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   CEO Taizong (唐太宗) is now in office.         ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   Next steps:                                    ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   1. openclaw chat        (talk to CEO)          ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   2. Customize SOUL.md    (make it yours)        ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   3. Add your API keys    (.env or config)       ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   4. Fork & Star us!     (github.com/AIwork4me) ${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   贞观之治，今又重来。                            ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║   The Prosperity of Zhenguan, Reborn in AI.      ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}║                                                  ║${LOBSTER_RESET}"
    echo -e "${LOBSTER_GREEN}╚══════════════════════════════════════════════════╝${LOBSTER_RESET}"
    echo ""
}

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
WITH_TEAM=false
WITH_FEISHU=false

for arg in "$@"; do
    case "$arg" in
        --with-team)    WITH_TEAM=true ;;
        --with-feishu)  WITH_FEISHU=true ;;
        --help|-h)      banner; exit 0 ;;
    esac
done

banner
check_environment
init_profile
setup_ceo

if [ "$WITH_TEAM" = true ]; then
    echo ""
    setup_team
fi

echo ""
health_check
done_message
