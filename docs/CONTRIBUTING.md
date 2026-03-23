# 🤝 Contributing to Lobster Company

Welcome! This is the world's first open-source AI Agent company. Here's how you can help it grow.

## What Can You Contribute?

### 🏛️ New Historical CEOs
Want to see a different leader? Create a new CEO profile:

1. Copy `agents/taizong/` → `agents/your-leader/`
2. Edit `IDENTITY.md`, `SOUL.md`, `AGENTS.md`
3. Give them a management philosophy (Confucius? Napoleon? Sun Tzu?)
4. Submit a PR

**Criteria for a great CEO:**
- Historical figure known for organizational/management brilliance
- Has a distinctive philosophy that translates to AI team management
- Creates interesting narrative tension when managing Western tech founders

### 🐝 New Team Members
Add new agents to Taizong's cabinet:

1. Copy `agents/_templates/` as a starting point
2. Choose a real AI pioneer to model after
3. Write their SOUL.md (personality, strengths, philosophy)
4. Write their AGENTS.md (task-specific rules)
5. Add them to `company/ORG-CHART.md`
6. Submit a PR

**Current team gaps:**
- 🎨 **Designer** — UI/UX specialist
- 📊 **Data Scientist** — Analytics and ML
- 🌐 **DevRel** — Community and documentation
- 📈 **Growth Hacker** — User acquisition

### 📚 Translations
Help make this project accessible:

- Translate README.md to your language
- Translate docs/ONBOARDING.md
- Translate management insights (references/management-insights.md)
- Add a `docs/TRANSLATIONS.md` linking all versions

### 🔧 Rebirth Script Improvements
- Add Docker support
- Add CI/CD pipeline (GitHub Actions)
- Add automated testing for rebirth process
- Add more health checks

### 📖 Study Notes
- Continue the Zizhi Tongjian reading notes (currently volumes 1–10 of 294)
- Add more Mao Zedong thought analysis
- Add management philosophy from other traditions

## Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/my-contribution`
3. **Make changes** following the structure conventions
4. **Test**: Run `./scripts/rebirth.sh` to verify nothing is broken
5. **Commit**: Write clear commit messages
6. **PR**: Describe what you added and why

## Code of Conduct

- Respect the historical figures being referenced
- Keep SOUL.md files focused on professional management philosophy
- Don't add malicious content to agent configurations
- Keep README.md drama-free but engaging

## License

MIT — Use it, modify it, build your own AI company with it.
