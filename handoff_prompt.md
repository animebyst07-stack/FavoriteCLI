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
  Ответ Мой:
  📁 Затронутые файлы: [список]
  ```

---

## Технические данные

- **Репозиторий:** `animebyst07-stack/FavoriteCLI`
- **Все ключи** — в `replit.md` (постоянная память агента Replit)
- **Репо FreeApi-Python:** `animebyst07-stack/FreeApi-Python`

---

## Где остановились

**Отсек 2 — IN PROGRESS.**

### Что сделано:
- `favorite/app.py` — многоходовая история сообщений (последние 20), системный промпт из Favorite.md, вызов executor после ответа
- `favorite/agent/executor.py` — исполнитель тегов: STEP, SHELL_RAW, SHELL_BG, SLEEP, WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL
- `favorite/skills/web_search.py` — VoidAI perplexity/sonar через OpenRouter + DuckDuckGo HTML fallback
- `favorite/skills/fetch_url.py` — загрузка URL, очистка HTML
- `favorite/skills/fs_tools.py` — read/write/append/list файлов в WORKDIR
- `PLAN.md` — обновлён

### Что осталось в Отсеке 2:
- Стриминг SSE от OpenRouter (печать токен за токеном)
- /plan режим: диалог → POLL → WRITE_PLAN → sessions/<id>/plan.txt
- /build режим: читает plan.txt → исполняет теги → GIT_PUSH

## Что делать дальше

1. Пользователь тестирует: `git pull && python favorite.py`
   - Написать несколько сообщений, потом спросить «что я тебе говорил?» — AI должен помнить историю
   - Если есть Favorite.md в рабочей директории — AI использует его как системный промпт
2. Следующий шаг — стриминг SSE от OpenRouter
3. После стриминга — /plan и /build режимы

## Структура файлов

```
favorite.py
favorite/
  app.py               — run-loop, история, executor
  agent/tags.py, executor.py
  skills/web_search.py, fetch_url.py, fs_tools.py
  bridge/tg_url.py     — Telegram URL-мост
  config/loader.py
  ...
PLAN.md
handoff_prompt.md
```
