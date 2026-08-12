from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @property
    @abstractmethod
    def metric_id(self) -> str:
        pass

    @abstractmethod
    def collect(self, year: int) -> Any:
        pass