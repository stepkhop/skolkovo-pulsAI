from __future__ import annotations
from typing import Any
from collectors.base import BaseCollector
from config.settings import load_manual_data
from models.metrics import MetricSeries, MetricType, MetricValue
from pulseai_utils.logger import get_logger
from pulseai_utils.validators import validate_year

logger = get_logger(__name__)

class Metric4Collector(BaseCollector):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.manual_data = load_manual_data()

    @property
    def metric_id(self) -> str:
        return "metric_4"

    def collect(self, year: int) -> MetricSeries:
        year = validate_year(year)
        series = MetricSeries(
            metric_type=MetricType.EDUCATION,
            name=self.config["metric_4"]["name"],
            description=self.config["metric_4"]["description"],
            unit=self.config["metric_4"].get("unit", "%"),
        )

        data = self.manual_data.get("metric_4_age", {})
        year_data = data.get(year)
        if year_data:
            value = year_data.get("value")
            series.add_value(MetricValue(
                year=year,
                value=float(value) if value is not None else None,
                source=year_data.get("source", "Ручной ввод"),
                notes=year_data.get("notes", ""),
            ))
            logger.info(f"Метрика 4 ({year}): {value}%")
        else:
            logger.warning(f"Метрика 4: нет данных за {year}")
            series.add_value(MetricValue(year=year, value=None, source="", notes="Нет данных"))

        return series