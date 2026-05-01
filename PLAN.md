# FavoriteCLI — План разработки по отсекам

Правило: каждый отсек завершается пушем в GitHub и отчётом.
GitHub: https://github.com/animebyst07-stack/FavoriteCLI

---

## ОТСЕК 1 — Фундамент [DONE]

- [x] Структура файлов проекта (по SOLID, §10)
- [x] `config/api_keys.json` — все ключи (FavoriteAPI, OpenRouter, VoidAI)
- [x] `config/github.json` — токен и репо
- [x] `favorite/platform.py` — IPlatform / TermuxPlatform / LinuxFakePlatform
- [x] `favorite/ui/theme.py` — цветовая схема оранжевый + белый
- [x] `favorite/ui/welcome.py` — welcome-блок (рамка, лого, модель, путь)
- [x] `favorite/ui/spinner.py` — анимация Thinking/Shimmying
- [x] `favorite/ui/chat.py` — рендер сообщений (●, ❯, ⎿)
- [x] `favorite/ui/prompt.py` — slash-меню с автодополнением (28 команд)
- [x] `favorite/commands/` — ICommand + registry + все базовые команды
- [x] `favorite/agent/tags.py` — парсер тегов ≪TAG≫/≪TAG:args≫/≪TAG≫...≪/TAG≫
- [x] `favorite/agent/sub_roles_library.json` — 20 встроенных ролей суб-агентов
- [x] `favorite/sessions/manager.py` — CRUD сессий (meta.json, history.jsonl)
- [x] `favorite/github/api_client.py` — GitHub REST API (без git CLI)
- [x] `favorite/github/auto_push.py` — авто-пуш после фич
- [x] `favorite/api/` — IChatProvider, FavoriteApiClient, OpenRouterClient
- [x] `favorite/memory/favorite_md.py` — чтение/запись Favorite.md
- [x] `favorite/app.py` — DI-контейнер, главный run-loop
- [x] `favorite.py` — точка входа
- [x] `Favorite.md` — системный промпт AI (постоянная память)
- [x] `README.md`, `requirements.txt`

---

## ОТСЕК 2 — Ядро агента: теги + скиллы + чат-цикл [TODO]

- [ ] Полный обработчик тегов в run-loop (STEP, SHELL_RAW, SHELL_BG, SLEEP, SKILL, GIT_PUSH, PLAN, POLL)
- [ ] Скилл WebSearch (VoidAI `perplexity/sonar` + DuckDuckGo fallback)
- [ ] Скилл Fetch URL (httpx + clean text)
- [ ] Скилл FS Tools (read/write файлов в WORKDIR)
- [ ] Скилл Termux Shell (запуск SHELL_RAW, SHELL_BG, SLEEP)
- [ ] Поддержка стриминга ответа (SSE) от OpenRouter
- [ ] Многоходовая история (messages[] для контекста)
- [ ] Режим /plan: диалог → POLL → WRITE_PLAN → sessions/<id>/plan.txt
- [ ] Режим /build: чтение plan.txt + исполнение + GIT_PUSH

---

## ОТСЕК 3 — Многоагентность + /auto + hot-reload памяти [TODO]

- [ ] MainAgent / SubAgent с очередью запросов
- [ ] Библиотека ролей: 100+ ролей в sub_roles_library.json
- [ ] /agents команда: вкл/выкл, назначить роль, авто-дефолт топ-N
- [ ] /auto режим: глубокая автоматизация с лимитами и журналом
- [ ] /silent режим
- [ ] Hot-reload Favorite.md (watchdog)
- [ ] Compaction (WRITE_CTX при переполнении контекста)

---

## ОТСЕК 4 — Telegram-уведомления + /usage + FavoriteChrome [TODO]

- [ ] Telegram-уведомления (три режима роутинга + дайджест)
- [ ] /usage дашборд (токены, деньги, context_kb)
- [ ] /doctor, /recap, /compact, /effort, /map
- [ ] FavoriteChrome — FastAPI+Playwright браузерный сервис
- [ ] Endpoints: /pdf, /content, /scrape, /url-metadata, /screenshot, /youtube-transcript

---

## ОТСЕК 5 — Продвинутые фичи [TODO]

- [ ] /voice (SaluteSpeech Bot, STT+TTS)
- [ ] /architect (дорогая модель думает → architect_plan.md → дешёвая делает)
- [ ] /spec + Spec-Driven Development (requirements/design/tasks.md)
- [ ] MCP поддержка (mcp_servers.json)
- [ ] Soul режим (/soul on/off/bg/fg)
- [ ] Vault (§33) — хранилище привязок
- [ ] Web Panel (FastAPI+WebSocket + D3.js граф)
