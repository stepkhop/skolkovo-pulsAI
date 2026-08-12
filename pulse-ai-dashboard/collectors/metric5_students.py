from __future__ import annotations
from typing import Any
from collectors.base import BaseCollector
from config.settings import load_manual_data
from models.metrics import MetricSeries, MetricType, MetricValue
from pulseai_utils.logger import get_logger
from pulseai_utils.validators import validate_year

logger = get_logger(__name__)

class Metric5Collector(BaseCollector):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.manual_data = load_manual_data()

    @property
    def metric_id(self) -> str:
        return "metric_5"

    def collect(self, year: int) -> MetricSeries:
        year = validate_year(year)
        series = MetricSeries(
            metric_type=MetricType.STUDENTS,
            name=self.config["metric_5"]["name"],
            description=self.config["metric_5"]["description"],
            unit=self.config["metric_5"].get("unit", "чел."),
        )

        data = self.manual_data.get("metric_5_students", {})
        year_data = data.get(year)
        if year_data:
            value = year_data.get("value")
            series.add_value(MetricValue(
                year=year,
                value=float(value) if value is not None else None,
                source=year_data.get("source", "Ручной ввод"),
                notes=year_data.get("notes", ""),
            ))
            logger.info(f"Метрика 5 ({year}): {value} студентов")
        else:
            logger.warning(f"Метрика 5: нет данных за {year}")
            series.add_value(MetricValue(year=year, value=None, source="", notes="Нет данных"))

        return series