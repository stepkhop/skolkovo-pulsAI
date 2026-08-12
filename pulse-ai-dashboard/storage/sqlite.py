from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager

from models.metrics import MetricSeries, MetricType, MetricValue, PublicationCollection
from pulseai_utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT,
    doi TEXT,
    url TEXT,
    venue TEXT NOT NULL,
    source TEXT NOT NULL,
    year INTEGER NOT NULL,
    is_russian_affiliated INTEGER DEFAULT 0,
    affiliations TEXT,
    collected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pub_year ON publications(year);
CREATE INDEX IF NOT EXISTS idx_pub_venue ON publications(venue);
CREATE INDEX IF NOT EXISTS idx_pub_doi ON publications(doi);

CREATE TABLE IF NOT EXISTS metric_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL,
    year INTEGER NOT NULL,
    value REAL,
    source TEXT,
    notes TEXT,
    collected_at TEXT NOT NULL,
    UNIQUE(metric_type, year)
);

CREATE INDEX IF NOT EXISTS idx_mv_type_year ON metric_values(metric_type, year);
"""


class SQLiteStorage:
    def __init__(self, db_path: str = "data/pulse_ai.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(SCHEMA_SQL)
                logger.info("SQLite схема инициализирована: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("Ошибка инициализации схемы БД: %s", e)
            raise

    def save_publications(self, collection: PublicationCollection) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM publications WHERE year = ?", (collection.year,))
            for pub in collection.publications:
                conn.execute(
                    """
                    INSERT INTO publications
                    (title, authors, doi, url, venue, source, year, is_russian_affiliated, affiliations, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pub.title,
                        json.dumps(pub.authors, ensure_ascii=False),
                        pub.doi,
                        pub.url,
                        pub.venue,
                        pub.source,
                        pub.year,
                        1 if pub.is_russian_affiliated else 0,
                        json.dumps(pub.affiliations, ensure_ascii=False),
                        collection.collected_at.isoformat(),
                    ),
                )
            logger.info("Сохранено %d публикаций за %d", len(collection.publications), collection.year)

    def load_publications(self, year: int) -> PublicationCollection:
        from models.metrics import Publication
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM publications WHERE year = ? ORDER BY venue, title",
                (year,),
            ).fetchall()

        result = PublicationCollection(year=year)
        for row in rows:
            authors = json.loads(row["authors"] or "[]")
            affiliations = json.loads(row["affiliations"] or "[]")
            pub = Publication(
                title=row["title"],
                authors=authors,
                doi=row["doi"] or "",
                url=row["url"] or "",
                venue=row["venue"],
                source=row["source"],
                year=row["year"],
                is_russian_affiliated=bool(row["is_russian_affiliated"]),
                affiliations=affiliations,
            )
            result.add_publication(pub)
        return result

    def save_metric(self, series: MetricSeries) -> None:
        with self._connect() as conn:
            for val in series.values:
                conn.execute(
                    """
                    INSERT INTO metric_values (metric_type, year, value, source, notes, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(metric_type, year) DO UPDATE SET
                        value = excluded.value,
                        source = excluded.source,
                        notes = excluded.notes,
                        collected_at = excluded.collected_at
                    """,
                    (
                        series.metric_type.value,
                        val.year,
                        val.value,
                        val.source,
                        val.notes,
                        val.collected_at.isoformat(),
                    ),
                )
            logger.info("Сохранена метрика %s", series.metric_type.value)

    def load_metric(self, metric_type: MetricType) -> MetricSeries | None:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM metric_values WHERE metric_type = ? ORDER BY year",
                (metric_type.value,),
            ).fetchall()

        if not rows:
            return None

        series = MetricSeries(
            metric_type=metric_type,
            name=metric_type.value,
            description="",
            unit="",
        )
        for row in rows:
            series.add_value(MetricValue(
                year=row["year"],
                value=row["value"],
                source=row["source"] or "",
                notes=row["notes"] or "",
            ))
        return series