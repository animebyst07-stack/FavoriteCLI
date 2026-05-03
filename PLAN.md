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
- [x] `favorite/ui/chat.py` — рендер сообщений + print_status_line()
- [x] `favorite/ui/prompt.py` — slash-меню с автодополнением
- [x] `favorite/commands/` — ICommand + registry + все базовые команды
- [x] `favorite/agent/tags.py` — парсер тегов ≪TAG≫
- [x] `favorite/agent/sub_roles_library.json` — 20 встроенных ролей
- [x] `favorite/sessions/manager.py` — CRUD сессий + stats tracking
- [x] `favorite/github/api_client.py` — GitHub REST API
- [x] `favorite/github/auto_push.py` — авто-пуш
- [x] `favorite/api/` — IChatProvider, FavoriteApiClient, OpenRouterClient, NvidiaClient
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

## ОТСЕК 2 — Ядро агента: история + теги + скиллы [DONE]

- [x] Многоходовая история messages[] — AI помнит разговор (последние 20 сообщений)
- [x] Системный промпт из Favorite.md передаётся при каждом запросе
- [x] `favorite/agent/executor.py` — все теги: STEP, SHELL_RAW, SHELL_BG, SLEEP, WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL, CONTINUE, POLL, WRITE_PLAN, READ_FILE, WRITE_FILE, ASK_USER, THINK, SUB_AGENT, ADD_TASK, UPDATE_TASK, COMPLETE_TASK, LIST_TASKS
- [x] `favorite/skills/web_search.py` — VoidAI perplexity/sonar + DuckDuckGo fallback
- [x] `favorite/skills/fetch_url.py` — загрузка URL + очистка HTML
- [x] `favorite/skills/fs_tools.py` — read/write/append/list файлов в WORKDIR
- [x] Стриминг SSE от OpenRouter с подавлением `<thinking>` блоков в реальном времени
- [x] Режим /plan: диалог → POLL → WRITE_PLAN → sessions/<id>/plan.txt
- [x] Режим /build: чтение plan.txt + исполнение тегов + GIT_PUSH
- [x] `favorite/agent/response_processor.py` — strip_thinking_blocks() для не-стримингового пути
- [x] `favorite/agent/system_prompt.py` — централизованный build_system_prompt()
- [x] `favorite/agent/model_router.py` — RouterModule: classify_prompt() + select_model()
- [x] `favorite/api/nvidia.py` — NvidiaClient(IChatProvider) — NVIDIA NIM endpoint
- [x] `favorite/config/loader.py` — nvidia_key поле

---

## ОТСЕК 3 — Многоагентность + hot-reload памяти [DONE]

- [x] `/agents list` — таблица активных агентов + доступные роли из библиотеки
- [x] `/agents spawn <role> <task>` — запускает суб-агент с ролью, возвращает результат
- [x] `favorite/agent/sub_agent.py` — run_sub_agent(role, task, cfg) — in-process суб-агент
- [x] `≪SUB_AGENT:role=...≫` тег — вызов суб-агента из main agent loop
- [x] Hot-reload Favorite.md через watchdog Observer — уведомление при изменении файла
- [x] `/memory` — показать содержимое Favorite.md в rich Panel
- [x] `/memory edit` — открыть $EDITOR или показать путь
- [x] `favorite/memory/hot_reload.py` — start_watcher() с дебаунсингом
- [x] `favorite/commands/memory_cmd.py` — MemoryCommand

---

## ОТСЕК 4 — Утилиты + диагностика [DONE]

- [x] `/usage` — запросы, токены (est), длительность, модель, размер Favorite.md
- [x] `favorite/commands/usage_cmd.py` — UsageCommand
- [x] `favorite/tasks/manager.py` — TaskManager: CRUD задач в sessions/<id>/tasks.json
- [x] `favorite/commands/tasks_cmd.py` — /tasks list/add/done/todo/progress/del с rich Table
- [x] `/doctor` — диагностика: API ключи, сеть, воркдир, Favorite.md, GitHub конфиг
- [x] `favorite/commands/doctor_cmd.py` — DoctorCommand (OK/FAIL/WARN таблица)
- [x] `/recap [N]` — компактный дайджест последних N обменов в rich Panel
- [x] `favorite/commands/recap_cmd.py` — RecapCommand
- [x] `/compact` — сжать историю в context_summary.md, заменить history.jsonl
- [x] `favorite/commands/compact_cmd.py` — CompactCommand
- [x] Централизованный print_status_line() — все статус-строки через одну функцию
- [x] Null byte в app.py устранён

---

## ОТСЕК 5 — Продвинутые фичи [TODO]

- [ ] `/auto` — непрерывный loop без user input
- [ ] `/silent` режим — тихая работа
- [ ] Compaction: WRITE_CTX при переполнении контекста (>16K токенов)
- [ ] Библиотека ролей: расширение до 100+ ролей
- [ ] Telegram-уведомления (три режима роутинга + дайджест)
- [ ] `/effort` — оценка сложности задачи
- [ ] `/map` — карта файлов проекта
- [ ] `/voice` (STT+TTS)
- [ ] `/architect` (дорогая модель думает → дешёвая делает)
- [ ] MCP поддержка
- [ ] Web Panel
