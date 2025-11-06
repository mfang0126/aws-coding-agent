# Documentation Archive

This folder contains **historical documentation and superseded guides**. These files are kept for reference but are no longer actively maintained.

## 📦 What's Here

### Development Workflow (Outdated)
- **`implementation-workflow.md`** - Old implementation plan
  - Status: Superseded by actual implementation
  - References: Old directory structure (`src/prompts/`, old `src/auth/`)
  - Keep For: Historical context of how project was built

- **`incremental-testing-strategy.md`** - Old testing approach
  - Status: Superseded by actual testing
  - References: Old directory structure
  - Keep For: Understanding testing philosophy

### Quick Start Guides (Superseded)
- **`quick-start-guide-old.md`** - Original quick start
  - Status: Replaced by [docs/QUICK_START.md](../QUICK_START.md)
  - Current Quick Start: [See docs/QUICK_START.md](../QUICK_START.md) instead

### Reference Materials (Partial Updates Needed)
- **`agentcore-gateway-oauth-setup.md`** - OAuth setup details
  - Status: Partially outdated (references old structure)
  - Current Guide: [See docs/AUTHENTICATION.md](../AUTHENTICATION.md)
  - Still Useful: Contains detailed OAuth explanation

- **`architecture-review.md`** - System design analysis
  - Status: Partially outdated (references old structure)
  - Current Guide: [See AGENT_DEVELOPMENT_GUIDE.md](../../AGENT_DEVELOPMENT_GUIDE.md)
  - Still Useful: Contains architectural thinking

## 🔄 Recent Changes (Nov 4, 2025)

These files reference the **old directory structure** before alignment with AGENT_DEVELOPMENT_GUIDE.md:

### What Changed
- `src/prompts/` → `src/constants/`
- Added `src/gateway/` with auth protocols
- Added `src/utils/response.py` and `src/utils/helpers.py`
- Created clean public API in `src/__init__.py`

### Current References
- **Up-to-date imports**: See [claudedocs/alignment-with-guide.md](../../claudedocs/alignment-with-guide.md)
- **Architecture patterns**: See [AGENT_DEVELOPMENT_GUIDE.md](../../AGENT_DEVELOPMENT_GUIDE.md)
- **Current tests**: See `tests/` folder (all updated)

## 📖 How to Use This Archive

### Reading Historical Context
If you want to understand how the project was designed:
1. `implementation-workflow.md` - Shows the original planned structure
2. `architecture-review.md` - Shows analysis of architectural decisions
3. `agentcore-gateway-oauth-setup.md` - Shows OAuth implementation thinking

### Migrating Old Code to New Structure
If you find old code referencing these structures, update using:
- Old: `from src.prompts.system_prompts import ...`
- New: `from src.constants.prompts import ...`

- Old: `from src.auth.github_auth import GitHubAuth`
- New: `from src.gateway import AgentCoreGitHubAuth`

- Old: Manual response formatting
- New: `from src import format_success, format_error`

See [claudedocs/alignment-with-guide.md](../../claudedocs/alignment-with-guide.md) for complete migration guide.

## ✅ What You Should Use Instead

| Old File | New Resource | Purpose |
|----------|--------------|---------|
| `quick-start-guide-old.md` | [docs/QUICK_START.md](../QUICK_START.md) | Get started in 5 minutes |
| `implementation-workflow.md` | [AGENT_DEVELOPMENT_GUIDE.md](../../AGENT_DEVELOPMENT_GUIDE.md) | Understand architecture |
| `agentcore-gateway-oauth-setup.md` | [docs/AUTHENTICATION.md](../AUTHENTICATION.md) | Setup GitHub auth |
| `incremental-testing-strategy.md` | [tests/](../../tests/) | See actual test implementation |
| `architecture-review.md` | [claudedocs/alignment-with-guide.md](../../claudedocs/alignment-with-guide.md) | Understand current design |

## 📝 Notes

- **Not deleted**: These files are kept for historical reference
- **Not updated**: To maintain accurate historical record
- **Why kept**: To understand project evolution and decisions made

If you need to reference these, **update the import paths** to match the current structure before using code examples.

---

**Last organized**: November 4, 2025
