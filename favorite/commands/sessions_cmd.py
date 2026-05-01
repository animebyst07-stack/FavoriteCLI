from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info
from ..sessions.manager import SessionManager


class NewSessionCommand(ICommand):
    name = "/new session"
    description = "Начать новую сессию"
    priority = 6

    def execute(self, args: str, ctx: CommandContext) -> None:
        mgr = SessionManager()
        print_agent_message("Создаю новую сессию...", "system")
        sid = mgr.create_session(workdir=ctx.workdir)
        print_info(f"  Сессия создана: {sid}")


class SessionCommand(ICommand):
    name = "/session"
    description = "Список сохранённых сессий"
    priority = 7

    def execute(self, args: str, ctx: CommandContext) -> None:
        mgr = SessionManager()
        sessions = mgr.list_sessions()
        print_separator()
        print_agent_message("Сохранённые сессии", "system")
        if not sessions:
            print_info("  Сессий нет.")
        for i, s in enumerate(sessions, 1):
            print_info(f"  [{i}] {s['session_id'][:8]}...  |  {s.get('title','без названия')}  |  {s.get('created_at','?')}")
        print_separator()
