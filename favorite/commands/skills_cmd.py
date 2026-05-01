from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


BUILTIN_SKILLS = [
    ("WebSearch",     "Поиск в интернете через VoidAI / DuckDuckGo", True),
    ("Fetch URL",     "Скачать и распарсить страницу (clean text)", True),
    ("FS Tools",      "Чтение/запись файлов в WORKDIR", True),
    ("Termux Shell",  "Запуск команд в терминале", True),
    ("Sleep",         "Отложенное чтение результатов tmux-сессии", True),
    ("web_panel",     "Веб-панель (FastAPI+WebSocket)", False),
    ("device_control","Управление вторым Android через ADB", False),
]


class SkillsCommand(ICommand):
    name = "/skills"
    description = "Управление скиллами"
    priority = 8

    def execute(self, args: str, ctx: CommandContext) -> None:
        print_separator()
        print_agent_message("Скиллы", "system")
        for name, desc, enabled in BUILTIN_SKILLS:
            status = "[ON]" if enabled else "[OFF]"
            print_info(f"  {status:6} {name:<18} — {desc}")
        print_separator()
        print_info("  Для вкл/выкл: /skills <имя> on|off")
