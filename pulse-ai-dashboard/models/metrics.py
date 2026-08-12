from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetricType(str, Enum):
    PUBLICATIONS = "publications"
    RESEARCHERS = "researchers"
    ECONOMY = "economy"
    EDUCATION = "education"
    STUDENTS = "students"


class Publication(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1)
    authors: list[str] = Field(default_factory=list)
    doi: str = Field(default="")
    url: str = Field(default="")
    venue: str = Field(...)
    source: str = Field(...)
    year: int = Field(..., ge=2000, le=2100)
    is_russian_affiliated: bool = Field(default=False)
    affiliations: list[str] = Field(default_factory=list)

    @field_validator("authors", mode="before")
    @classmethod
    def _norm_authors(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [a.strip() for a in v.split(",") if a.strip()]
        if isinstance(v, list):
            return [str(a).strip() for a in v if a]
        return []

    @field_validator("affiliations", mode="before")
    @classmethod
    def _norm_affils(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [a.strip() for a in v.split(",") if a.strip()]
        if isinstance(v, list):
            return [str(a).strip() for a in v if a]
        return []

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        return v.strip()


class PublicationCollection(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    total_count: int = Field(default=0, ge=0)
    source_counts: dict[str, int] = Field(default_factory=dict)
    publications: list[Publication] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    def add_publication(self, pub: Publication) -> None:
        self.publications.append(pub)
        self.total_count = len(self.publications)


class MetricValue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    year: int = Field(..., ge=2000, le=2100)
    value: float | None = Field(default=None)
    source: str = Field(default="")
    notes: str = Field(default="")
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("value")
    @classmethod
    def _validate_positive(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("Значение метрики не может быть отрицательным")
        return v


class MetricSeries(BaseModel):
    metric_type: MetricType = Field(...)
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    unit: str = Field(default="")
    values: list[MetricValue] = Field(default_factory=list)

    def get_value_for_year(self, year: int) -> MetricValue | None:
        for v in self.values:
            if v.year == year:
                return v
        return None

    def add_value(self, value: MetricValue) -> None:
        existing = self.get_value_for_year(value.year)
        if existing:
            self.values.remove(existing)
        self.values.append(value)
        self.values.sort(key=lambda x: x.year)


class DashboardData(BaseModel):
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    publications: PublicationCollection = Field(
        default_factory=lambda: PublicationCollection(year=2024)
    )
    metrics: dict[MetricType, MetricSeries] = Field(default_factory=dict)

    def get_metric(self, metric_type: MetricType) -> MetricSeries | None:
        return self.metrics.get(metric_type)

    def set_metric(self, metric: MetricSeries) -> None:
        self.metrics[metric.metric_type] = metric