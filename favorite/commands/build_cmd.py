from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


class BuildCommand(ICommand):
    name = "/build"
    description = "Режим исполнения"
    priority = 10

    def execute(self, args: str, ctx: CommandContext) -> None:
        print_separator()
        print_agent_message(
            "Режим /build активирован. Агент будет выполнять задачи:\n"
            "  читать/создавать файлы, запускать команды, коммитить в GitHub.",
            "system"
        )
        print_separator()
