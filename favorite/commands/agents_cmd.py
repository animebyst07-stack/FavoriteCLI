from typing import Optional
import json
from pathlib import Path
from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from rich.table import Table
from rich.console import Console

_ROLES_FILE = Path(__file__).resolve().parent.parent / "agent" / "sub_roles_library.json"
console = Console()

def print_info(text: str) -> None:
    console.print(text)

def load_roles() -> list[dict]:
    if not _ROLES_FILE.exists():
        return []
    try:
        return json.loads(_ROLES_FILE.read_text(encoding="utf-8"))
    except:
        return []

class AgentsCommand(ICommand):
    name = "/agents"
    description = "Управление роем агентов"
    priority = 4

    def execute(self, args: str, ctx: CommandContext) -> None:
        parts = args.split()
        cmd = parts[0].lower() if parts else "list"

        if cmd == "list":
            self._list_agents(ctx)
        elif cmd == "spawn":
            role_id = parts[1] if len(parts) > 1 else None
            task = " ".join(parts[2:]) if len(parts) > 2 else ""
            self._spawn_agent(role_id, task, ctx)
        elif cmd == "kill":
            print_info("  [dim]Функция kill пока не реализована (агенты завершаются сами)[/dim]")
        else:
            print_info(f"  [red]Неизвестная подкоманда: {cmd}[/red]")
            print_info("  Использование: /agents [list|spawn <role> <task>|kill <id>]")

    def _list_agents(self, ctx: CommandContext) -> None:
        print_separator()
        print_agent_message("Активные агенты", "system")
        
        table = Table(box=None, padding=(0, 2))
        table.add_column("ID", style="cyan")
        table.add_column("ROLE", style="green")
        table.add_column("STATUS", style="dim")
        
        table.add_row("main-1", "orchestrator", "active")
        
        console.print(table)
        
        print_separator()
        print_agent_message("Доступные роли (библиотека)", "system")
        roles = load_roles()
        
        role_table = Table(box=None, padding=(0, 2))
        role_table.add_column("ID", style="cyan")
        role_table.add_column("NAME", style="white")
        role_table.add_column("DESCRIPTION", style="dim")
        
        for r in roles:
            role_table.add_row(r.get("id", ""), r.get("name", ""), r.get("description", ""))
            
        console.print(role_table)

    def _spawn_agent(self, role_id: Optional[str], task: str, ctx: CommandContext) -> None:
        if not role_id:
            print_info("  [red]Ошибка: не указана роль. Пример: /agents spawn debugger 'check this code'[/red]")
            return
        
        if not task:
            print_info(f"  [red]Ошибка: не указана задача для {role_id}[/red]")
            return

        print_info(f"  [bold #ff8c00]●[/bold #ff8c00] Spawning [cyan]{role_id}[/cyan]...")
        from ..agent.sub_agent import run_sub_agent
        result = run_sub_agent(role_id, task, ctx.config)
        
        print_separator()
        print_agent_message(f"Ответ от {role_id}", "agent")
        console.print(result)
        print_separator()
