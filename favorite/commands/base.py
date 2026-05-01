from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandContext:
    workdir: str
    session_id: str
    platform: Any
    config: Any


class ICommand(ABC):
    name: str
    description: str
    priority: int = 99

    @abstractmethod
    def execute(self, args: str, ctx: CommandContext) -> None:
        pass
