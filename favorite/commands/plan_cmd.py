from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator, print_step_block
from ..ui.welcome import print_info


class PlanCommand(ICommand):
    name = "/plan"
    description = "Режим обсуждения и планирования"
    priority = 9

    def execute(self, args: str, ctx: CommandContext) -> None:
        print_separator()
        print_agent_message(
            "Режим /plan активирован. Я буду задавать вопросы и зафиксирую план в plan.txt.\n"
            "  Введи задачу, или нажми Enter для выхода.",
            "system"
        )
        print_separator()
