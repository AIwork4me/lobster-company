# 🦞 Lobster Company — Rebirth Script (Windows)

# One command to spawn a complete AI Agent company on any Windows machine.
#
# Usage:
#   .\scripts\rebirth.ps1 [-WithTeam] [-WithFeishu]
#
# Options:
#   -WithTeam      Set up all 7 specialist agents (default: CEO only)
#   -WithFeishu    Configure Feishu (Lark) integration

param(
    [switch]$WithTeam,
    [switch]$WithFeishu,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║                                                  ║" -ForegroundColor Blue
    Write-Host "║   🦞  LOBSTER COMPANY — REBIRTH                  ║" -ForegroundColor Yellow
    Write-Host "║                                                  ║" -ForegroundColor Blue
    Write-Host "║   An ancient Chinese emperor managing 7           ║" -ForegroundColor Blue
    Write-Host "║   legendary Western AI founders.                  ║" -ForegroundColor Blue
    Write-Host "║                                                  ║" -ForegroundColor Blue
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

function Write-Info    { Write-Host "[INFO] " -ForegroundColor Blue -NoNewline; Write-Host $args }
function Write-Ok      { Write-Host "[OK]   " -ForegroundColor Green -NoNewline; Write-Host $args }
function Write-Warn    { Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline; Write-Host $args }
function Write-Err     { Write-Host "[ERROR]" -ForegroundColor Red -NoNewline; Write-Host $args }

# ── Step 1: Environment Check ──
function Check-Environment {
    Write-Info "Checking environment..."

    # Node.js
    try {
        $nodeVer = (node --version)
        $major = [int]($nodeVer -replace 'v(\d+)\..*', '$1')
        if ($major -ge 18) {
            Write-Ok "Node.js $nodeVer found"
        } else {
            Write-Err "Node.js >= 18 required (found $nodeVer)"
            exit 1
        }
    } catch {
        Write-Err "Node.js not found. Install from https://nodejs.org"
        exit 1
    }

    # OpenClaw / AutoClaw
    $hasOpenclaw = $false
    try {
        $null = Get-Command openclaw -ErrorAction Stop
        Write-Ok "OpenClaw found"
        $hasOpenclaw = $true
    } catch {}

    if (-not $hasOpenclaw) {
        try {
            $null = Get-Command autoclaw -ErrorAction Stop
            Write-Ok "AutoClaw found"
        } catch {
            Write-Warn "OpenClaw / AutoClaw not found."
            Write-Host ""
            Write-Host "  Install AutoClaw: https://docs.openclaw.ai"
            Write-Host "  Install OpenClaw: npm install -g @openclaw/cli"
            Write-Host ""
            exit 1
        }
    }

    Write-Ok "OS: Windows"
}

# ── Step 2: Setup CEO ──
function Setup-CEO {
    Write-Info "Setting up CEO Taizong's workspace..."

    $scriptDir = $PSScriptRoot
    $companyRoot = Split-Path $scriptDir -Parent
    $ceoWorkspace = Join-Path $companyRoot "agents\taizong"
    $sharedWorkspace = Join-Path $companyRoot "shared-workspace"

    if (Test-Path $ceoWorkspace) {
        Write-Ok "CEO workspace: $ceoWorkspace"
        Write-Host "   → SOUL.md, MEMORY.md, IDENTITY.md, study notes"
    } else {
        Write-Err "CEO workspace not found at $ceoWorkspace"
        exit 1
    }

    if (Test-Path $sharedWorkspace) {
        Write-Ok "Shared workspace: $sharedWorkspace"
    } else {
        Write-Warn "Shared workspace not found (optional)"
    }
}

# ── Step 3: Setup Team ──
function Setup-Team {
    Write-Info "Setting up team agents..."

    $scriptDir = $PSScriptRoot
    $companyRoot = Split-Path $scriptDir -Parent
    $agentsDir = Join-Path $companyRoot "agents"

    $agents = @(
        @("richards", "Scout"),
        @("steinberger", "Architect"),
        @("cherny", "AI Engineer"),
        @("chase", "Full-Stack Engineer"),
        @("packer", "DevOps"),
        @("leike", "Security & QA"),
        @("sanger", "Product Manager")
    )

    foreach ($a in $agents) {
        $name = $a[0]
        $role = $a[1]
        $dir = Join-Path $agentsDir $name
        if (Test-Path $dir) {
            Write-Ok "  $name ($role) — $dir"
        } else {
            Write-Warn "  $name ($role) — workspace not found (skipping)"
        }
    }
}

# ── Step 4: Health Check ──
function Health-Check {
    Write-Info "Running health check..."

    $scriptDir = $PSScriptRoot
    $companyRoot = Split-Path $scriptDir -Parent

    $criticalFiles = @(
        "agents\taizong\SOUL.md",
        "agents\taizong\IDENTITY.md",
        "agents\taizong\MEMORY.md",
        "agents\taizong\AGENTS.md",
        "company\ORG-CHART.md",
        "company\TEAM-BUILDING.md",
        "README.md"
    )

    $pass = 0
    $fail = 0

    foreach ($f in $criticalFiles) {
        $fullPath = Join-Path $companyRoot $f
        if (Test-Path $fullPath) {
            $pass++
        } else {
            $fail++
            Write-Err "  Missing: $f"
        }
    }

    Write-Host ""
    if ($fail -eq 0) {
        Write-Ok "Health check passed: $pass/$($pass + $fail) files present"
    } else {
        Write-Err "Health check FAILED: $pass passed, $fail missing"
    }
}

# ── Step 5: Done ──
function Write-Done {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                  ║" -ForegroundColor Green
    Write-Host "║   🦞  LOBSTER COMPANY HAS BEEN REBORN           ║" -ForegroundColor Green
    Write-Host "║                                                  ║" -ForegroundColor Green
    Write-Host "║   CEO Taizong (唐太宗) is now in office.         ║" -ForegroundColor Green
    Write-Host "║                                                  ║" -ForegroundColor Green
    Write-Host "║   Next steps:                                    ║" -ForegroundColor Green
    Write-Host "║   1. openclaw chat        (talk to CEO)          ║" -ForegroundColor Green
    Write-Host "║   2. Customize SOUL.md    (make it yours)        ║" -ForegroundColor Green
    Write-Host "║   3. Add your API keys    (.env or config)       ║" -ForegroundColor Green
    Write-Host "║   4. Fork & Star us!     (github.com/AIwork4me) " -ForegroundColor Green
    Write-Host "║                                                  ║" -ForegroundColor Green
    Write-Host "║   贞观之治，今又重来。                            ║" -ForegroundColor Green
    Write-Host "║   The Prosperity of Zhenguan, Reborn in AI.      ║" -ForegroundColor Green
    Write-Host "║                                                  ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
}

# ── Main ──
if ($Help) { Write-Banner; exit 0 }

Write-Banner
Check-Environment
Setup-CEO

if ($WithTeam) {
    Write-Host ""
    Setup-Team
}

Write-Host ""
Health-Check
Write-Done
