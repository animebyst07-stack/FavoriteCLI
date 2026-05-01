# FavoriteCLI

Python CLI AI-agent for Termux/Android. Inspired by Claude Code.

**Color scheme:** white + orange  
**Entry point:** `python favorite.py`  
**Architecture:** SOLID — each module has one job

## Quick Start (Termux)

```bash
pkg install python tmux git
pip install -r requirements.txt
python favorite.py
```

## Quick Start (Linux/Replit)

```bash
pip install -r requirements.txt
python favorite.py
```

## Project Structure

```
favorite.py              # entry point
favorite/
  app.py                 # DI container + run loop
  platform.py            # IPlatform (TermuxPlatform / LinuxFakePlatform)
  ui/                    # welcome, chat, prompt, theme, spinner
  commands/              # ICommand implementations
  api/                   # IChatProvider (FavoriteAPI, OpenRouter)
  agent/                 # tags parser, sub_roles_library.json
  skills/                # ISkill implementations
  sessions/              # session CRUD
  github/                # GitHub REST API push
  config/                # loader.py
  memory/                # Favorite.md hot-reload
config/
  api_keys.json          # API keys
  github.json            # GitHub token + repo
Favorite.md              # permanent AI memory (system prompt)
sessions/                # per-session data
```

## API Providers

- **OpenRouter** — default (`qwen/qwen3-coder:free`)
- **FavoriteAPI** — local Telegram-bridge to Gemini (`http://127.0.0.1:5005`)
- **VoidAI** — WebSearch skill (`perplexity/sonar`)

## Key Commands

| Command | Description |
|---|---|
| `/plan` | Discuss task, run polls, write plan.txt |
| `/build` | Execute: create files, run commands, push |
| `/agents` | Manage main + sub-agents |
| `/skills` | Toggle and configure skills |
| `/session` | List and switch sessions |
| `/auto` | Deep automation mode |

## Platform Detection

Set `FAVORITE_PLATFORM=termux` or `FAVORITE_PLATFORM=linux` to override auto-detection.  
Auto-detect checks for Termux `$PREFIX` path.

## GitHub Push

The agent pushes via GitHub REST API (no git CLI needed).  
Config: `config/github.json`
