# FavoriteCLI — План разработки по отсекам

Правило: каждый отсек завершается пушем в GitHub и отчётом.
GitHub: https://github.com/animebyst07-stack/FavoriteCLI

---

## ОТСЕК 1 — Фундамент [DONE]

- [x] Структура файлов проекта (по SOLID, §10)
- [x] `config/api_keys.json` — пустой шаблон
- [x] `config/github.json` — пустой шаблон
- [x] `favorite/platform.py` — IPlatform / TermuxPlatform / LinuxFakePlatform
- [x] `favorite/ui/theme.py` — цветовая схема оранжевый + белый
- [x] `favorite/ui/welcome.py` — welcome-блок
- [x] `favorite/ui/spinner.py` — анимация ● серый/белый
- [x] `favorite/ui/chat.py` — рендер сообщений
- [x] `favorite/ui/prompt.py` — slash-меню с автодополнением
- [x] `favorite/commands/` — ICommand + registry + все базовые команды
- [x] `favorite/agent/tags.py` — парсер тегов ≪TAG≫
- [x] `favorite/agent/sub_roles_library.json` — 20 встроенных ролей
- [x] `favorite/sessions/manager.py` — CRUD сессий
- [x] `favorite/github/api_client.py` — GitHub REST API
- [x] `favorite/github/auto_push.py` — авто-пуш
- [x] `favorite/api/` — IChatProvider, FavoriteApiClient, OpenRouterClient
- [x] `favorite/memory/favorite_md.py` — чтение/запись Favorite.md
- [x] `favorite/setup_wizard.py` — мастер первого запуска
- [x] `favorite/app.py` — DI-контейнер, главный run-loop
- [x] `favorite.py` — точка входа
- [x] UX фиксы: clear экрана, спиннер ●, убрано дублирование ввода
- [x] Статус в шапке всегда актуален (reload_config при каждом показе)

## planMOST — Telegram URL-мост [DONE]

- [x] `freeapi/tg_notify.py` — пинит красивое уведомление с URL
- [x] `favorite/bridge/tg_url.py` — читает URL из pinned_message, -100 префикс для каналов
- [x] `favorite/config/loader.py` — поля tg_bridge_token/chat_id
- [x] `favorite/app.py` — авторетрай через TG при ConnectionError
- [x] `/Favorite API` → [4] — настройка моста

---

## ОТСЕК 2 — Ядро агента: история + теги + скиллы [IN PROGRESS]

- [x] Многоходовая история messages[] — AI помнит разговор (последние 20 сообщений)
- [x] Системный промпт из Favorite.md передаётся при каждом запросе
- [x] `favorite/agent/executor.py` — обработчик тегов: STEP, SHELL_RAW, SHELL_BG, SLEEP, WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL
- [x] `favorite/skills/web_search.py` — VoidAI perplexity/sonar + DuckDuckGo fallback
- [x] `favorite/skills/fetch_url.py` — загрузка URL + очистка HTML
- [x] `favorite/skills/fs_tools.py` — read/write/append/list файлов в WORKDIR
- [ ] Стриминг SSE от OpenRouter (печать по токену)
- [ ] Режим /plan: диалог → POLL → WRITE_PLAN → sessions/<id>/plan.txt
- [ ] Режим /build: чтение plan.txt + исполнение тегов + GIT_PUSH

---

## ОТСЕК 3 — Многоагентность + /auto + hot-reload памяти [TODO]

- [ ] MainAgent / SubAgent с очередью запросов
- [ ] Библиотека ролей: 100+ ролей в sub_roles_library.json
- [ ] /agents: вкл/выкл, назначить роль
- [ ] /auto: глубокая автоматизация
- [ ] /silent режим
- [ ] Hot-reload Favorite.md через watchdog
- [ ] Compaction: WRITE_CTX при переполнении контекста

---

## ОТСЕК 4 — Telegram-уведомления + /usage [TODO]

- [ ] Telegram-уведомления (три режима роутинга + дайджест)
- [ ] /usage дашборд (токены, деньги, context_kb)
- [ ] /doctor, /recap, /compact, /effort, /map

---

## ОТСЕК 5 — Продвинутые фичи [TODO]

- [ ] /voice (STT+TTS)
- [ ] /architect (дорогая модель думает → дешёвая делает)
- [ ] MCP поддержка
- [ ] Soul режим
- [ ] Web Panel
