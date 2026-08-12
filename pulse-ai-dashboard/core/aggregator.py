from __future__ import annotations

from models.metrics import DashboardData, MetricType
from pulseai_utils.logger import get_logger
from storage.sqlite import SQLiteStorage

logger = get_logger(__name__)


class Aggregator:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def get_dashboard_data(self, year: int) -> DashboardData:
        data = DashboardData()

        try:
            pubs = self.storage.load_publications(year)
            data.publications = pubs
        except Exception as e:
            logger.error("Ошибка загрузки публикаций: %s", e)

        for metric_type in [
            MetricType.PUBLICATIONS,
            MetricType.RESEARCHERS,
            MetricType.ECONOMY,
            MetricType.EDUCATION,
            MetricType.STUDENTS,
        ]:
            try:
                series = self.storage.load_metric(metric_type)
                if series:
                    data.set_metric(series)
            except Exception as e:
                logger.error("Ошибка загрузки метрики %s: %s", metric_type.value, e)

        return data

    def get_metric_history(self, metric_type: MetricType) -> list[tuple[int, float | None]]:
        series = self.storage.load_metric(metric_type)
        if not series:
            return []
        return [(v.year, v.value) for v in series.values]