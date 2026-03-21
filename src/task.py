from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    name: str
    repeat: int
    description: str
    
    doneBy: Optional[str] = None
    doneWhen: Optional[datetime] = None
