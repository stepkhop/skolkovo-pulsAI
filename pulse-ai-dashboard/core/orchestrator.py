from __future__ import annotations
from typing import Any
from collectors.metric1_publications import Metric1Collector
from collectors.metric2_researchers import Metric2Collector
from collectors.metric3_ege import Metric3Collector
from collectors.metric4_age import Metric4Collector
from collectors.metric5_students import Metric5Collector
from config.settings import load_config
from models.metrics import DashboardData, MetricType, PublicationCollection, MetricSeries, MetricValue
from pulseai_utils.logger import get_logger
from storage.sqlite import SQLiteStorage

logger = get_logger(__name__)

class Orchestrator:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        self.storage = SQLiteStorage(self.config["app"]["db_path"])
        self.collectors = {
            1: Metric1Collector(self.config),
            2: Metric2Collector(self.config),
            3: Metric3Collector(self.config),
            4: Metric4Collector(self.config),
            5: Metric5Collector(self.config),
        }

    def run(self, year: int | None = None) -> DashboardData:
        year = year or self.config["collection"]["default_year"]
        logger.info("=== Запуск сбора метрик за %d ===", year)
        data = DashboardData()
        self._collect_metric_1(year, data)
        for num, mtype in [
            (2, MetricType.RESEARCHERS),
            (3, MetricType.ECONOMY),
            (4, MetricType.EDUCATION),
            (5, MetricType.STUDENTS),
        ]:
            self._collect_metric_n(num, mtype, year, data)
        logger.info("=== Сбор метрик завершён ===")
        return data

    def run_single_metric(self, metric_num: int, year: int | None = None) -> DashboardData:
        year = year or self.config["collection"]["default_year"]
        logger.info("=== Сбор метрики %d за %d ===", metric_num, year)
        data = DashboardData()
        if metric_num == 1:
            self._collect_metric_1(year, data)
        elif metric_num in (2, 3, 4, 5):
            mtype = {
                2: MetricType.RESEARCHERS,
                3: MetricType.ECONOMY,
                4: MetricType.EDUCATION,
                5: MetricType.STUDENTS,
            }[metric_num]
            self._collect_metric_n(metric_num, mtype, year, data)
        else:
            logger.error("Неизвестная метрика: %d", metric_num)
        return data

    def _collect_metric_1(self, year: int, data: DashboardData) -> None:
        if not self.config.get("metric_1", {}).get("enabled", False):
            return
        try:
            metric_value, publications = self.collectors[1].collect(year)
            collection = PublicationCollection(year=year)
            for p in publications:
                collection.add_publication(p)
            self.storage.save_publications(collection)
            series = MetricSeries(
                metric_type=MetricType.PUBLICATIONS,
                name="Топ-публикации",
                description="",
                unit="шт."
            )
            series.add_value(metric_value)
            self.storage.save_metric(series)
            data.publications = collection
            logger.info("Метрика 1 сохранена: %s публикаций", metric_value.value)
        except Exception:
            logger.exception("Метрика 1: ошибка сбора")

    def _collect_metric_n(self, num: int, mtype: MetricType, year: int, data: DashboardData) -> None:
        if not self.config.get(f"metric_{num}", {}).get("enabled", False):
            return
        try:
            series = self.collectors[num].collect(year)
            self.storage.save_metric(series)
            data.set_metric(series)
            val = series.get_value_for_year(year)
            if val and val.value is not None:
                logger.info("Метрика %d сохранена: %s", num, val.value)
        except Exception:
            logger.exception("Метрика %d: ошибка сбора", num)