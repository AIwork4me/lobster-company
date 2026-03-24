# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Lobster Company, please report it responsibly.

**Do NOT open a public issue.**

Instead, please email: lobster-company@users.noreply.github.com

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix**: Depends on severity

## Scope

This policy applies to:
- Agent configuration files (SOUL.md, AGENTS.md, GUIDELINES.md)
- Python code in agent missions
- Rebirth scripts (`scripts/rebirth.sh`, `scripts/rebirth.ps1`)
- Any credentials or secrets accidentally committed

## Security by Design

Lobster Company uses these security practices:
- Zero external dependencies in all Python code (standard library only)
- Dedicated Security & QA agent (Leike) trained in vulnerability detection
- `.gitignore` configured to prevent credential leaks
- No hardcoded API keys, tokens, or passwords in any source file
