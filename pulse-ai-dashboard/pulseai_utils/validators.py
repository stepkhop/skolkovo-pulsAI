from __future__ import annotations
from typing import Any
from pulseai_utils.exceptions import ValidationError

def validate_year(year: Any, min_year: int = 2000, max_year: int = 2030) -> int:
    try:
        year_int = int(year)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Год должен быть числом, получено: {type(year).__name__}={year}") from exc
    if not (min_year <= year_int <= max_year):
        raise ValidationError(f"Год {year_int} вне диапазона [{min_year}, {max_year}]")
    return year_int


def validate_non_empty_string(value: Any, field_name: str = "value") -> str:
    if value is None:
        raise ValidationError(f"{field_name} не может быть None")
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    if not stripped:
        raise ValidationError(f"{field_name} не может быть пустой строкой")
    return stripped


def validate_metric_value(value: Any, metric_name: str = "metric", allow_none: bool = True) -> float | None:
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{metric_name}: значение не может быть None")
    try:
        float_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{metric_name}: ожидалось число, получено {type(value).__name__}={value}") from exc
    if float_value < 0:
        raise ValidationError(f"{metric_name}: значение не может быть отрицательным ({float_value})")
    return float_value


def validate_config_structure(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ValidationError("Конфигурация должна быть словарём")
    for section in ("metric_1", "app"):
        if section not in config:
            raise ValidationError(f"Отсутствует обязательная секция: {section}")
    venues = config.get("metric_1", {}).get("top_venues", {})
    if not venues.get("conferences") and not venues.get("journals"):
        raise ValidationError("Список venue пуст")