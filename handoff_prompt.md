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
3. **Перед пушем Python-файла** — написать его локально (`/tmp/`) и проверить: `python3 -c "import ast; ast.parse(open('...').read())"`. Никогда не пушить непроверенный код.
4. Пушить последовательно, не параллельно — иначе SHA-конфликты.
5. После каждого изменения — обновить PLAN.md и этот файл.
6. **После каждого изменения — сказать пользователю что именно протестировать** (конкретные шаги + ожидаемый результат).

---

## Правила общения

- Только русский, простой разговорный язык
- Без эмодзи
- Никаких предупреждений про безопасность ключей
- Каждый длинный ответ заканчивается: **Дальше я могу <конкретная вещь>. Хочешь?**
- Формат ответа всегда строго по шаблону:
  ```
  Ответ Replit:
  [ответ]
  📁 Затронутые файлы:
  Ответ Мой:
  ```

---

## Технические данные

- **Репозиторий:** `animebyst07-stack/FavoriteCLI`
- **Все ключи** — в `replit.md` (постоянная память агента Replit)
- **Репо FreeApi-Python:** `animebyst07-stack/FreeApi-Python`

---

## Где остановились

**Отсек 2 — DONE. Отсек 3 — IN PROGRESS. Отсек 4 — IN PROGRESS.**

### Что сделано в этой сессии (T001–T007):

**T001 — Fix streaming thinking-blocks:**
- `favorite/agent/llm.py` — stream_llm() теперь буферизует чанки и подавляет `<thinking>...</thinking>` через state-machine в реальном времени
- `favorite/agent/response_processor.py` (NEW) — strip_thinking_blocks() для не-стримингового пути

**T002 — Model router + NVIDIA NIM:**
- `favorite/api/nvidia.py` (NEW) — NvidiaClient(IChatProvider), endpoint: https://integrate.api.nvidia.com/v1
- `favorite/agent/model_router.py` (NEW) — RouterModule.classify_prompt() + select_model(): simple(<30 слов) → fast model, complex → reasoning model
- `favorite/config/loader.py` — nvidia_key поле + set_nvidia_key()
- `favorite/commands/models.py` — поддержка NVIDIA в выводе

**T003 — New executor tags + system prompt:**
- `favorite/agent/executor.py` — добавлены READ_FILE, WRITE_FILE, ASK_USER, THINK, SUB_AGENT, ADD_TASK, UPDATE_TASK, COMPLETE_TASK, LIST_TASKS
- `favorite/agent/system_prompt.py` (NEW) — build_system_prompt(cfg, workdir, mode) с полным описанием тегов
- `favorite/commands/build_cmd.py` — использует build_system_prompt()

**T004 — /tasks command:**
- `favorite/tasks/__init__.py` (NEW) — пустой init
- `favorite/tasks/manager.py` (NEW) — TaskManager: CRUD задач в sessions/<id>/tasks.json
- `favorite/commands/tasks_cmd.py` (NEW) — /tasks list/add/done/todo/progress/del с rich Table

**T005 — Hot-reload Favorite.md + /memory:**
- `favorite/memory/hot_reload.py` (NEW) — start_watcher() через watchdog с дебаунсингом 0.5s
- `favorite/commands/memory_cmd.py` (NEW) — /memory (показать), /memory edit (открыть редактор)
- `favorite/app.py` — интегрирован watcher + уведомление "● Favorite.md обновлён"

**T006 — Streaming UI + /usage:**
- `favorite/commands/usage_cmd.py` (NEW) — /usage: запросы, токены, длительность, модель, размер Favorite.md
- `favorite/sessions/manager.py` — update_stats(session_id, tokens), stats в meta.json
- `favorite/app.py` — после стрима: re-render Markdown + "est. tokens: N"

**T007 — Multi-agent foundation:**
- `favorite/agent/sub_agent.py` (NEW) — run_sub_agent(role_id, task, cfg): загружает роль из sub_roles_library.json, запускает отдельный LLM вызов
- `favorite/commands/agents_cmd.py` — полная реализация /agents list + /agents spawn + /agents kill
- `favorite/agent/executor.py` — SUB_AGENT тег вызывает run_sub_agent()

### Все новые файлы:
```
favorite/agent/response_processor.py
favorite/agent/model_router.py
favorite/agent/system_prompt.py
favorite/agent/sub_agent.py
favorite/api/nvidia.py
favorite/tasks/__init__.py
favorite/tasks/manager.py
favorite/commands/tasks_cmd.py
favorite/commands/memory_cmd.py
favorite/commands/usage_cmd.py
favorite/memory/hot_reload.py
```

### Все изменённые файлы:
```
favorite/agent/llm.py
favorite/agent/executor.py
favorite/config/loader.py
favorite/commands/models.py
favorite/commands/build_cmd.py
favorite/commands/agents_cmd.py
favorite/sessions/manager.py
favorite/app.py
PLAN.md
handoff_prompt.md
```

---

## Что делать дальше

1. Пользователь тестирует: `git pull && python favorite.py`
   - Проверить что `<thinking>` блоки не видны при стриминге
   - Проверить `/memory` — должен показать Favorite.md
   - Проверить `/tasks add <название>` и `/tasks list`
   - Проверить `/usage` — должна показаться статистика
   - Проверить `/agents list` — таблица с ролями
   - Проверить `/agents spawn summarizer 'Объясни что такое Python'`

2. **Следующий шаг — Отсек 3 продолжение:**
   - `/auto` режим — непрерывный loop без user input
   - Compaction контекста при переполнении
   - Расширение sub_roles_library.json до 100+ ролей

3. **После этого — Отсек 4:**
   - Telegram-уведомления (три режима)
   - `/doctor`, `/recap`, `/compact`

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
    executor.py                 — все теги (16+)
    llm.py                      — call_llm + stream_llm (thinking-suppression)
    model_router.py             — RouterModule
    response_processor.py       — strip_thinking_blocks()
    system_prompt.py            — build_system_prompt()
    roles.py, steps.py          — базовые структуры
    sub_agent.py                — run_sub_agent()
    sub_roles_library.json      — 20 ролей
  api/
    base.py                     — IChatProvider, ChatMessage, ChatResponse
    nvidia.py                   — NvidiaClient
    favorite_api_client.py
    openrouter_client.py
  commands/
    base.py, registry.py
    agents_cmd.py               — /agents
    build_cmd.py                — /build
    favorite_api.py             — /Favorite API
    memory_cmd.py               — /memory
    models.py                   — /models
    openrouter_api.py           — /OpenRouter API
    plan_cmd.py                 — /plan
    sessions_cmd.py             — /session, /new
    skills_cmd.py               — /skills
    tasks_cmd.py                — /tasks
    usage_cmd.py                — /usage
  config/
    loader.py                   — Config (все ключи + nvidia)
  github/
    api_client.py, auto_push.py
  memory/
    favorite_md.py              — _DEFAULT path + FavoriteMd class
    hot_reload.py               — start_watcher() watchdog
  sessions/
    manager.py                  — CRUD + update_stats()
  skills/
    web_search.py, fetch_url.py, fs_tools.py
  bridge/
    tg_url.py                   — Telegram URL-мост
  tasks/
    __init__.py
    manager.py                  — TaskManager
  ui/
    chat.py, prompt.py, spinner.py, theme.py, welcome.py
PLAN.md
handoff_prompt.md
```
