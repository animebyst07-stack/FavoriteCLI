from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.history import InMemoryHistory

from .theme import STYLE


ALL_COMMANDS = [
    ("/Favorite API",    "Управление ключами FavoriteAPI"),
    ("/OpenRouter API",  "Управление ключами OpenRouter"),
    ("/models",          "Все модели всех провайдеров"),
    ("/agents",          "Управление роем агентов"),
    ("/auto",            "Режим глубокой автоматизации"),
    ("/new session",     "Начать новую сессию"),
    ("/session",         "Список сохранённых сессий"),
    ("/skills",          "Управление скиллами"),
    ("/plan",            "Режим обсуждения и планирования"),
    ("/build",           "Режим исполнения"),
    ("/silent",          "Включить/выключить режим тишины"),
    ("/export",          "Выгрузить сессию в zip/md"),
    ("/stop",            "Остановить /auto"),
    ("/resume",          "Продолжить остановленный /auto"),
    ("/architect",       "Режим архитектора (дорогая модель думает)"),
    ("/spec",            "Spec-Driven Development"),
    ("/usage",           "Статистика использования API"),
    ("/doctor",          "Диагностика системы"),
    ("/recap",           "Краткое резюме сессии"),
    ("/compact",         "Сжать контекст"),
    ("/effort",          "Уровень старания агента"),
    ("/map",             "Карта файлов проекта"),
    ("/branch",          "Форк диалога"),
    ("/image",           "Прикрепить изображение"),
    ("/voice",           "Голосовой ввод/вывод"),
    ("/soul",            "Soul-режим (непрерывная работа)"),
    ("/feedback",        "Журнал ошибок и мыслей агента"),
]


class SlashCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        partial = text.lower()
        starts, contains = [], []
        for cmd, desc in ALL_COMMANDS:
            low = cmd.lower()
            if low.startswith(partial):
                starts.append((cmd, desc))
            elif partial[1:] and partial[1:] in low:
                contains.append((cmd, desc))
        seen = set()
        for cmd, desc in starts + contains:
            if cmd in seen:
                continue
            seen.add(cmd)
            yield Completion(
                cmd,
                start_position=-len(text),
                display=_highlight(cmd, text),
                display_meta=desc,
            )


def _highlight(cmd: str, partial: str) -> HTML:
    """Подсвечивает совпадающую часть оранжевым."""
    low_cmd, low_partial = cmd.lower(), partial.lower()
    result, i = "", 0
    while i < len(cmd):
        if low_partial and low_cmd[i:i+len(low_partial)] == low_partial:
            result += f"<style fg='#ff8c00'><b>{cmd[i:i+len(low_partial)]}</b></style>"
            i += len(low_partial)
        else:
            result += cmd[i]
            i += 1
    return HTML(result)


def build_session() -> PromptSession:
    kb = KeyBindings()

    @kb.add("escape")
    def _noop(event):
        # Escape просто сбрасывает текущий ввод, не выходит
        event.app.current_buffer.reset()

    return PromptSession(
        completer=SlashCompleter(),
        style=STYLE,
        key_bindings=kb,
        history=InMemoryHistory(),
        complete_while_typing=True,
        mouse_support=False,
        # bottom_toolbar убран намеренно
    )


def get_prompt_tokens():
    return [("class:prompt-arrow", "\u276f ")]
