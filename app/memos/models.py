from dataclasses import dataclass
from typing import Literal
from datetime import datetime


@dataclass
class Memo:
    id: str
    content: str
    create_time: datetime
    state: Literal["NORMAL", "ARCHIVED"]

    @classmethod
    def from_payload(cls, data: dict) -> "Memo":
        return cls(
            id=data["name"],
            content=data["content"],
            create_time=datetime.fromisoformat(
                data["createTime"].replace("Z", "+00:00")
            ),
            state=data["state"],
        )
