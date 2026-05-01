# FavoriteCLI — План разработки по отсекам

Правило: каждый отсек завершается пушем в GitHub и отчётом.
GitHub: https://github.com/animebyst07-stack/FavoriteCLI

---

## ОТСЕК 1 — Фундамент [DONE]

- [x] Структура файлов проекта (по SOLID, §10)
- [x] `config/api_keys.json` — пустой шаблон (ключи вводятся в CLI)
- [x] `config/github.json` — пустой шаблон (настраивается в CLI)
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
- [x] `favorite/setup_wizard.py` — мастер первого запуска (ключи вводятся интерактивно)
- [x] `favorite/app.py` — DI-контейнер, главный run-loop
- [x] `favorite.py` — точка входа
- [x] `Favorite.md` — системный промпт AI (постоянная память)
- [x] `README.md`, `requirements.txt`
- [x] Все API-ключи убраны из кода — вводятся только через CLI
- [x] CLI запускается сразу без принудительного мастера настройки
- [x] Выбор модели — двухуровневое меню: провайдер → модели (сортировка от дешёвых к дорогим, :free видно в ID)
- [x] fix: Ctrl+C в мастере настройки больше не сохраняет пустой ключ

---

## ОТСЕК 2 — Ядро агента: тег-обработчик + скиллы + стриминг [TODO]

- [ ] Полный обработчик тегов в run-loop:
      STEP, SHELL_RAW, SHELL_BG, SLEEP, SKILL, GIT_PUSH, PLAN, POLL, WRITE_PLAN, WRITE_FAV, WRITE_CTX
- [ ] Скилл WebSearch — VoidAI `perplexity/sonar` + DuckDuckGo HTML fallback
- [ ] Скилл Fetch URL — httpx + clean text extraction
- [ ] Скилл FS Tools — read/write/list файлов в WORKDIR
- [ ] Скилл Termux Shell — SHELL_RAW, SHELL_BG, SLEEP
- [ ] Стриминг ответа SSE от OpenRouter (печать по токену)
- [ ] Многоходовая история messages[] для контекста сессии
- [ ] Режим /plan: диалог → POLL → WRITE_PLAN → sessions/<id>/plan.txt
- [ ] Режим /build: чтение plan.txt + исполнение + GIT_PUSH

---

## ОТСЕК 3 — Многоагентность + /auto + hot-reload памяти [TODO]

- [ ] MainAgent / SubAgent с очередью запросов (один запрос за раз на ключ)
- [ ] Библиотека ролей: 100+ ролей в sub_roles_library.json
- [ ] /agents: вкл/выкл, назначить роль, авто-дефолт топ-N
- [ ] /auto: глубокая автоматизация с лимитами и журналом
- [ ] /silent режим
- [ ] Hot-reload Favorite.md через watchdog
- [ ] Compaction: WRITE_CTX при переполнении контекста (context_kb)

---

## ОТСЕК 4 — Telegram-уведомления + /usage + FavoriteChrome [TODO]

- [ ] Telegram-уведомления (три режима роутинга + дайджест)
- [ ] /usage дашборд (токены, деньги, context_kb по ключам)
- [ ] /doctor, /recap, /compact, /effort, /map
- [ ] FavoriteChrome — FastAPI+Playwright браузерный сервис
- [ ] Endpoints: /pdf, /content, /scrape, /url-metadata, /screenshot, /youtube-transcript
- [ ] Сессии браузера, блокировка ресурсов, stealth-режим

---

## ОТСЕК 5 — Продвинутые фичи [TODO]

- [ ] /voice (SaluteSpeech Bot, STT+TTS)
- [ ] /architect (дорогая модель думает → architect_plan.md → дешёвая делает)
- [ ] /spec + Spec-Driven Development (requirements/design/tasks.md)
- [ ] MCP поддержка (mcp_servers.json)
- [ ] Soul режим (/soul on/off/bg/fg)
- [ ] Vault (§33) — хранилище привязок
- [ ] Web Panel (FastAPI+WebSocket + D3.js граф)
