from __future__ import annotations

from collectors.base import BaseCollector
from collectors.metric1_publications import Metric1Collector
from collectors.metric2_researchers import Metric2Collector
from collectors.metric3_ege import Metric3Collector
from collectors.metric4_age import Metric4Collector
from collectors.metric5_students import Metric5Collector

__all__ = [
    "BaseCollector",
    "Metric1Collector",
    "Metric2Collector",
    "Metric3Collector",
    "Metric4Collector",
    "Metric5Collector",
]