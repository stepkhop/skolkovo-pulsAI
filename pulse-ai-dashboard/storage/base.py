from __future__ import annotations
from abc import ABC, abstractmethod
from models.metrics import MetricSeries, MetricType, PublicationCollection

class BaseStorage(ABC):
    @abstractmethod
    def save_publications(self, collection: PublicationCollection) -> None:
        pass

    @abstractmethod
    def load_publications(self, year: int) -> PublicationCollection:
        pass

    @abstractmethod
    def save_metric(self, series: MetricSeries) -> None:
        pass

    @abstractmethod
    def load_metric(self, metric_type: MetricType) -> MetricSeries | None:
        pass