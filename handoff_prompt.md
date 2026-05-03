# Handoff — проект FavoriteCLI

## ВАЖНО: правила обновления этого файла

Агент обязан обновлять его после каждого завершённого изменения и до конца сессии.
Ключевые блоки «Где остановились» и «Что делать дальше» копировать в `replit.md`.

---

## Кто ты и что происходит

Ты — агент Replit. Пишешь и правишь код Python-CLI-агента **FavoriteCLI** (работает в Termux / Android).
Репо: `animebyst07-stack/FavoriteCLI`. Код пушится через GitHub REST API, пользователь делает `git pull`.

---

## Операционные правила

1. При старте — прочитать этот файл и `replit.md` полностью.
2. Пуш — только через GitHub REST API (GET SHA → PUT). Токен хранится в `replit.md`.
3. **Перед пушем Python-файла** — написать его локально и проверить: `python3 -c "import ast; ast.parse(open('...').read())"`. Никогда не пушить непроверенный код.
4. Пушить последовательно, не параллельно — иначе SHA-конфликты.
5. После каждого изменения — обновить PLAN.md и этот файл.
6. **После каждого изменения — сказать пользователю что именно протестировать** (конкретные шаги + ожидаемый результат).

---

## Правила общения

- Только русский, простой разговорный язык
- Без эмодзи
- Никаких предупреждений про безопасность ключей
- Каждый длинный ответ заканчивается: **Дальше я могу <конкретная вещь>. Хочешь?**

---

## Технические данные

- **Репозиторий:** `animebyst07-stack/FavoriteCLI`
- **Все ключи** — в `replit.md` (постоянная память агента Replit)
- **Репо FreeApi-Python:** `animebyst07-stack/FreeApi-Python`

---

## Где остановились

**Отсек 1–4 — DONE. Отсек 5 — TODO.**

### Что сделано в этой сессии (T001–T008 + доп. работы):

**Compact UI — print_status_line:**
- `favorite/ui/chat.py` — централизованный `print_status_line(label, detail, color)` 
- Все команды и executor переведены на него: skills_cmd, usage_cmd, agents_cmd, plan_cmd, build_cmd, sessions_cmd, openrouter_api, favorite_api, executor.py (Read/Write/Tasks/WebSearch/SubAgent)
- `app.py` — `_save_est_tokens` теперь печатает `● tokens ~N,NNN` через print_status_line

**Null byte fix:**
- `favorite/app.py` — устранён null byte (был в строке с `session.prompt`)

**T001–T007 (выполнены в предыдущих сессиях):**
- `favorite/agent/llm.py` — stream_llm() с real-time подавлением `<thinking>`
- `favorite/agent/response_processor.py` — strip_thinking_blocks()
- `favorite/api/nvidia.py` — NvidiaClient
- `favorite/agent/model_router.py` — RouterModule.classify_prompt()
- `favorite/agent/system_prompt.py` — build_system_prompt()
- `favorite/agent/sub_agent.py` — run_sub_agent()
- `favorite/tasks/manager.py` + `favorite/commands/tasks_cmd.py`
- `favorite/memory/hot_reload.py` + `favorite/commands/memory_cmd.py`
- `favorite/commands/usage_cmd.py`
- `favorite/commands/agents_cmd.py` — полная реализация

**Новое в Отсеке 4:**
- `favorite/commands/doctor_cmd.py` — `/doctor`: OK/FAIL/WARN таблица (ключи, сеть, воркдир, GitHub)
- `favorite/commands/recap_cmd.py` — `/recap [N]`: последние N обменов в Panel
- `favorite/commands/compact_cmd.py` — `/compact`: сжатие истории в context_summary.md
- `favorite/app.py` — импорт и регистрация DoctorCommand, RecapCommand, CompactCommand

---

## Что делать дальше (Отсек 5)

1. **Приоритет 1 — `/auto` режим:**
   - Непрерывный loop: AI сам ставит задачи через ADD_TASK, сам их исполняет через теги
   - Выход: Ctrl+C или ≪DONE≫ тег
   - Файл: `favorite/commands/auto_cmd.py`

2. **Приоритет 2 — Compaction при переполнении:**
   - В `app.py` перед каждым запросом: если `len(history) > 40` — авто-compact
   - Вставить compact_entry в начало messages[]

3. **Приоритет 3 — расширение sub_roles_library.json:**
   - Добавить роли: architect, tester, reviewer, data-analyst, devops, ux-designer...
   - Цель: 50+ ролей

4. **Приоритет 4 — `/map` команда:**
   - Показать дерево файлов проекта (workdir) с rich Tree
   - Файл: `favorite/commands/map_cmd.py`

---

## Структура файлов (актуальная)

```
favorite.py
favorite/
  app.py                        — run-loop, hot-reload, история, executor
  platform.py
  setup_wizard.py
  agent/
    tags.py                     — парсер тегов ≪TAG≫
    executor.py                 — все теги (21+)
    llm.py                      — call_llm + stream_llm (thinking-suppression)
    model_router.py             — RouterModule
    response_processor.py       — strip_thinking_blocks()
    system_prompt.py            — build_system_prompt()
    roles.py, steps.py
    sub_agent.py                — run_sub_agent()
    sub_roles_library.json      — 20 ролей
  api/
    base.py                     — IChatProvider
    nvidia.py                   — NvidiaClient
    favorite_api.py
    openrouter.py
  commands/
    base.py, registry.py
    agents_cmd.py               — /agents
    build_cmd.py                — /build
    compact_cmd.py              — /compact  (NEW)
    doctor_cmd.py               — /doctor   (NEW)
    favorite_api.py             — /Favorite API
    memory_cmd.py               — /memory
    models.py                   — /models
    openrouter_api.py           — /OpenRouter API
    plan_cmd.py                 — /plan
    recap_cmd.py                — /recap    (NEW)
    sessions_cmd.py             — /session, /new session
    skills_cmd.py               — /skills
    tasks_cmd.py                — /tasks
    usage_cmd.py                — /usage
  config/
    loader.py                   — Config (все ключи + nvidia)
  github/
    api_client.py, auto_push.py
  memory/
    favorite_md.py
    hot_reload.py               — start_watcher() watchdog
  sessions/
    manager.py                  — CRUD + update_stats()
  skills/
    web_search.py, fetch_url.py, fs_tools.py
  bridge/
    tg_url.py
  tasks/
    __init__.py
    manager.py                  — TaskManager
  ui/
    chat.py                     — print_status_line() централизован
    prompt.py, spinner.py, theme.py, welcome.py
PLAN.md
handoff_prompt.md
README.md
```
