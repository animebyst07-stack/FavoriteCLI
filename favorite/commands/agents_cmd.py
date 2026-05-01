import json
from pathlib import Path
from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info

_ROLES_FILE = Path(__file__).resolve().parent.parent / "agent" / "sub_roles_library.json"


def load_roles() -> list[dict]:
    if not _ROLES_FILE.exists():
        return []
    return json.loads(_ROLES_FILE.read_text(encoding="utf-8"))


class AgentsCommand(ICommand):
    name = "/agents"
    description = "Управление роем агентов"
    priority = 4

    def execute(self, args: str, ctx: CommandContext) -> None:
        print_separator()
        print_agent_message("Управление агентами", "system")
        roles = load_roles()
        print_info(f"  Библиотека ролей: {len(roles)} ролей")
        print_info("  Главные агенты: 1 (main-1)")
        print_info("  Суб-агенты: 0 активных")
        print_separator()
        print_info("  [1] Добавить главного агента")
        print_info("  [2] Назначить суб-агента")
        print_info("  [3] Просмотреть библиотеку ролей")
        print_info("  [0] Назад")
        choice = input("  Выбери: ").strip()
        if choice == "3":
            for r in roles[:10]:
                print_info(f"  [{r.get('priority','-')}] {r.get('name')} — {r.get('description','')}")
            if len(roles) > 10:
                print_info(f"  ... и ещё {len(roles)-10} ролей")
