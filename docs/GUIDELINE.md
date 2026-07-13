# isekaitavern Contribution Guidelines

> This document provides comprehensive guidelines for contributors to the `isekaitavern` project. Please read it thoroughly before submitting code.

---

## Project Overview

**isekaitavern** is a Discord bot built with `discord.py`, featuring:

- **Slash commands** (`app_commands`) for modern Discord interactions
- **MongoDB** persistence via **Beanie ODM**
- **Redis** for caching and state management
- **Modular cog architecture** for feature separation
- **Internationalization (i18n)** support with JSON-based translations

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13.5 |
| Bot Framework | discord.py |
| Database ODM | Beanie (async MongoDB) |
| Cache | Redis |
| Config Loading | TOML + dacite |
| Data Validation | Pydantic / dataclasses |
| Linting | ruff |
| Package Manager | uv |

---

## Development Environment

### Prerequisites

- Python 3.13.5
- MongoDB instance (local or remote)
- Redis instance (local or remote)

### Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --group=dev,test

# Configure environment
cp .env.example .env
# Edit .env with your DISCORD_BOT_TOKEN, MONGO_URL, REDIS_URL

# Run the bot
uv run main.py
```

### Quality Commands

| Command | Purpose |
|---------|---------|
| `uv run ruff check .` | Lint all code |
| `uv run ruff format .` | Format all code |
| `uv run python db_test.py` | Run manual DB test script |

**All code MUST pass `ruff check` before submission.**

---

## Code Style

### Formatting

- **Line length**: 120 characters
- **Quotes**: Double quotes (`"`) exclusively
- **Indentation**: 4 spaces
- **Type hints**: Required on all function signatures
- **Async**: Use `async`/`await` consistently (this is an async codebase)

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Folders | Singular | `cog/`, `util/`, `model/` |
| Modules (collections) | Plural | `schemes.py`, `services.py` |
| Classes | PascalCase | `DiscordBot`, `TicketService` |
| Functions / Variables | snake_case | `get_default()`, `user_count` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |

> **Note**: Existing `isekaitavern/cogs/` is a historical exception. Follow the current structure for existing modules, but use singular for new top-level packages.

### Path Handling

Always use `pathlib` instead of `os.path`:

```python
# Good
from pathlib import Path
config_path = Path("config.toml")

# Bad
import os
config_path = os.path.join(".", "config.toml")
```

---

## Import Rules

### 1. Internal Project (Relative Imports)

Always use relative imports for intra-package references:

```python
from .config import app_config
from .services import TicketService
from ..utils.logging import logger
```

### 2. Built-in Modules

Direct import, but classes can be imported specifically:

```python
import os
import json
from dataclasses import dataclass
```

### 3. Third-Party Libraries

Use `import package` except for `discord`, which follows `discord.py` conventions:

```python
import discord
from discord import app_commands
import beanie
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

# For very long paths, use aliases
import a.b.very.long.module as avlm
```

---

## Project Architecture

### The Cog Pattern

Features are organized into **cogs** (modules). Each complex cog should separate concerns into:

| File | Responsibility |
|------|---------------|
| `cog.py` | Discord commands, event listeners, `Cog` class |
| `model.py` | Pydantic / Beanie data models |
| `repository.py` | Direct database interactions (CRUD) |
| `services.py` | Business logic, orchestration |
| `views.py` | Discord UI components (`discord.ui.View`, `Button`, `Select`) |

### Core Components

```
isekaitavern/
├── bot.py              # Bot class, setup hook, connection management
├── config/
│   ├── settings.py     # Pydantic/dataclass models, config loading
│   └── ...             # TOML-based configuration
├── core/
│   └── formatter.py    # Shared formatting utilities
├── cogs/
│   ├── ticket/         # Ticket system cog
│   ├── anonymous/      # Anonymous messaging cog
│   ├── welcome_farewell/  # Welcome/farewell messages cog
│   ├── reminder/       # Reminder system cog
│   └── ...
├── i18n/
│   ├── i18n.py         # Translation loading and retrieval
│   ├── zh-TW.json      # Traditional Chinese strings
│   └── en.json         # English strings
├── errno/
│   └── basic.py        # Custom exception classes
├── utils/
│   ├── logging.py      # Centralized logging setup
│   ├── validators.py   # Input validation helpers
│   ├── helpers.py      # General utility functions
│   └── extensions.py   # Extension loading utilities
└── types.py            # Shared type definitions
```

---

## Configuration

### config.toml

The main configuration file. **Do not create new config files** unless absolutely necessary—add settings to `config.toml` instead.

```toml
[bot]
name = "isekaitavern"
lang = "zh-TW"
cogs = ["ticket", "anonymous", "welcome_farewell", "reminder"]

[log]
name = "discord.bot"
format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
```

### Environment Variables (`.env`)

Sensitive values are loaded from `.env`:

```bash
DISCORD_BOT_TOKEN=your_token_here
MONGO_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
ENV=dev  # or prod, test
DEV_GUILD_ID=123456789  # Required only when ENV=dev
```

### Settings Loading

Settings are loaded via `dacite` from `config.toml` and merged with environment variables in `isekaitavern/config/settings.py`.

---

## Internationalization (i18n)

**Never hardcode user-facing strings.** All user-visible text must go through the i18n system.

### Usage

```python
from ..i18n import get_default

# Uses the default language from config.toml (bot.lang)
await interaction.response.send_message(
    get_default("ticket.commands.create.success", channel=channel.mention)
)
```

### Translation Files

- Located in `isekaitavern/i18n/`
- JSON format with dot-notation keys
- `zh-TW.json` and `en.json` are currently supported
- Default language is read from `config.toml` (`bot.lang`)

### Adding New Strings

1. Add the key to **all** language JSON files
2. Use dot notation: `"module.feature.action.status"`
3. Use named placeholders for dynamic values: `"Hello, {name}!"`

---

## Error Handling

### Custom Exceptions

Located in `isekaitavern/errno/`. Use them for domain-specific errors:

```python
from ..errno import ConfigException

raise ConfigException("Invalid database URL")
```

### General Principles

- Catch specific exceptions, not bare `except:`
- Log errors via `isekaitavern/utils/logging.py`
- In dev mode, send full tracebacks to Discord; in prod, send user-friendly messages
- Never suppress exceptions silently

### Logging

```python
from ..utils.logging import logger

logger.debug("Detailed debug info")
logger.info("Something happened")
logger.warning("Potential issue")
logger.error("Something failed")
```

---

## Database & Models

### Beanie ODM

Define models by inheriting from `beanie.Document`:

```python
import beanie
from pydantic import BaseModel

class Ticket(beanie.Document):
    guild_id: int
    channel_id: int
    creator_id: int
    status: str = "open"
```

### Repository Pattern

Keep all database queries in `repository.py`:

```python
class TicketRepository:
    async def create(self, ticket: Ticket) -> Ticket:
        return await ticket.insert()

    async def get_by_guild(self, guild_id: int) -> list[Ticket]:
        return await Ticket.find(Ticket.guild_id == guild_id).to_list()
```

---

## Discord-Specific Conventions

### Commands

- New cogs should use **`app_commands`** (slash commands) exclusively
- Legacy prefix commands exist but new features should be slash commands
- Use `discord.app_commands.checks` for permission validation

### Views & UI

- Define custom Views in `views.py`
- Use persistent views for components that must survive bot restarts
- Always set `custom_id` on buttons/selects for persistence

### Events

- Use `discord.ext.commands.Cog.listener()` for event handlers
- Keep event handlers thin; delegate to services

---

## Git Workflow

### Commit Messages

Use **Conventional Commits**:

| Prefix | Use Case |
|--------|----------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |

Example: `feat: add cooldown to anonymous messages`

### Before Submitting

1. Run `uv run ruff check .` — must pass with zero errors
2. Run `uv run ruff format .` — all files should be formatted
3. Verify your changes don't break existing cogs
4. Update documentation if you changed behavior

---

## Ruff Configuration

Key settings from `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "PTH", "PL", "RUF"]
ignore = ["E501", "PLR0402", "PLC0415", "PLR0913"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

Special per-file ignores exist for `__init__.py` and `tests/`. Check `pyproject.toml` for details.

---

## Quick Reference Checklist

Before submitting a PR, verify:

- [ ] Code passes `uv run ruff check .`
- [ ] Code is formatted with `uv run ruff format .`
- [ ] All functions have type hints
- [ ] No hardcoded user-facing strings (use i18n)
- [ ] Relative imports used for intra-package references
- [ ] `pathlib` used instead of `os.path`
- [ ] Proper error handling (no bare `except:`)
- [ ] Logging used instead of `print()`
- [ ] New settings added to `config.toml`, not new config files
- [ ] Conventional commit message format used

---

## Questions?

If you're unsure about a pattern or convention:

1. Check existing cogs (especially `ticket/` or `anonymous/`) for examples
2. Review `AGENTS.md` for additional operational guidelines
3. Ask in an issue or discussion before investing significant effort

---

*Last updated: After the comprehensive code review and cleanup cycle (all 9 short-term fixes applied).*
