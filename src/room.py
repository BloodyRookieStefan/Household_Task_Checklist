from dataclasses import dataclass
from .task import Task

@dataclass
class Room:
    name: str
    tasks: list[Task]

