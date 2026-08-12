from __future__ import annotations
import csv, os, re, time
from typing import Any, ClassVar
import requests
from collectors.base import BaseCollector
from models.metrics import MetricValue, Publication
from pulseai_utils.logger import get_logger
from pulseai_utils.validators import validate_year

logger = get_logger(__name__)

# AI-related OpenAlex concept IDs
AI_CONCEPT_IDS = [
    "C119857082",  # Machine learning
    "C15486532",  # Artificial intelligence
    "C54355291",  # Computer vision
    "C2013205381",  # Natural language processing
    "C13849689",  # Deep learning
    "C15744967",  # Reinforcement learning
    "C185763758",  # Pattern recognition
    "C68902304",  # Neural network
]

RUSSIAN_AFFILIATION_HINTS = (
    "россия", "russia", "russian federation", "moscow", "москва",
    "санкт-петербург", "saint petersburg", "st. petersburg", "spbu",
    "новосибирск", "novosibirsk", "казань", "kazan", "екатеринбург",
    "yekaterinburg", "нижний новгород", "nizhny novgorod", "сколтех",
    "skoltech", "мфти", "mipt", "мифи", "mephi", "вшэ", "hse", "итмо",
    "itmo", "мгу", "lomonosov moscow state", "innopolis", "иннополис",
    "yandex", "яндекс", "sber", "сбер", "tinkoff", "тинькофф",
    "vk", "вконтакте"
)

EXCLUDE_TITLE_KEYWORDS = (
    "competition", "workshop", "tutorial", "benchmark",
    "challenge", "dataset", "survey", "review",
)

TOP_VENUE_PATTERNS = {
    "NeurIPS": ["neurips", "neural information processing", "nips"],
    "ICML": ["icml", "international conference on machine learning"],
    "ICLR": ["iclr", "international conference on learning representations"],
    "CVPR": ["cvpr", "computer vision and pattern recognition"],
    "ICCV": ["iccv", "international conference on computer vision"],
    "ECCV": ["eccv", "european conference on computer vision"],
    "ACL": ["acl", "association for computational linguistics"],
    "EMNLP": ["emnlp", "empirical methods in natural language processing"],
    "AAAI": ["aaai", "aaai conference on artificial intelligence"],
    "IJCAI": ["ijcai", "international joint conference on artificial intelligence"],
    "Nature Machine Intelligence": ["nature machine intelligence"],
    "JMLR": ["journal of machine learning research", "jmlr"],
    "IEEE TPAMI": ["ieee transactions on pattern analysis", "tpami", "pami"],
}


def _is_false_positive_title(title: str | None) -> bool:
    if not title:
        return True
    low = title.lower()
    return any(kw in low for kw in EXCLUDE_TITLE_KEYWORDS)


def _pub_key(pub: dict):
    doi = (pub.get("doi") or "").strip().lower()
    if doi:
        return ("doi", doi)
    title = pub.get("title", "").strip().lower()
    authors = pub.get("authors", [])
    if isinstance(authors, list) and authors:
        return ("title_author", title, authors[0].strip().lower())
    return ("title_only", title)


def dedup_publications(pubs):
    seen = {}
    order = []
    for p in pubs:
        key = _pub_key(p)
        if key not in seen:
            seen[key] = dict(p)
            order.append(key)
        else:
            existing = seen[key]
            sources = set(s.strip() for s in existing.get("source", "").split("+") if s.strip())
            new_source = p.get("source", "").strip()
            if new_source and new_source not in sources:
                sources.add(new_source)
                existing["source"] = "+".join(sorted(sources))
            for field in ("doi", "url", "authors", "affiliations"):
                if not existing.get(field) and p.get(field):
                    existing[field] = p[field]
    return [seen[k] for k in order]


class OpenAlexAdapter:
    def __init__(self, config):
        cfg = config.get("metric_1", {}).get("openalex", {})
        self.base_url = cfg.get("base_url", "https://api.openalex.org").rstrip("/")
        self.per_page = min(max(int(cfg.get("per_page", 200)), 1), 200)
        self.email = cfg.get("email", "pulse-ai@example.com")
        self.api_key = config.get("api_keys", {}).get("openalex", "")
        self.headers = {"User-Agent": "PulseAI/1.0", "Accept": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _request(self, endpoint, params):
        for attempt in range(3):
            try:
                resp = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self.headers, timeout=30)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning(f"OpenAlex retry {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
        return None

    def fetch_ai_publications(self, year):
        logger.info(f"OpenAlex: сбор AI-публикаций за {year}")
        results = []
        seen = set()
        cursor = "*"
        while cursor:
            params = {
                "filter": f"publication_year:{year},authorships.institutions.country_code:ru,concepts.id:{'|'.join(AI_CONCEPT_IDS)}",
                "per-page": self.per_page,
                "cursor": cursor,
                "mailto": self.email,
            }
            data = self._request("/works", params)
            if not data:
                break
            for w in data.get("results", []):
                if w.get("id") in seen:
                    continue
                seen.add(w.get("id"))
                title = w.get("title", "")
                if _is_false_positive_title(title):
                    continue
                authors = []
                is_ru = False
                for auth in w.get("authorships", []):
                    if auth.get("author", {}).get("display_name"):
                        authors.append(auth["author"]["display_name"])
                    for inst in auth.get("institutions", []):
                        if inst.get("country_code") == "RU":
                            is_ru = True
                if not is_ru:
                    continue

                # Защита от NoneType в primary_location
                primary_location = w.get("primary_location")
                if primary_location and isinstance(primary_location, dict):
                    source = primary_location.get("source")
                    venue_name = source.get("display_name", "N/A") if source else "N/A"
                else:
                    venue_name = "N/A"

                classified = venue_name
                is_top = False
                for top_venue, patterns in TOP_VENUE_PATTERNS.items():
                    if any(p in title.lower() or p in venue_name.lower() for p in patterns):
                        classified = top_venue
                        is_top = True
                        break
                results.append({
                    "title": title,
                    "authors": authors,
                    "doi": w.get("doi", ""),
                    "venue": classified,
                    "source": "OpenAlex",
                    "year": year,
                    "is_top_venue": is_top,
                })
            cursor = data.get("meta", {}).get("next_cursor")
        logger.info(f"OpenAlex: собрано {len(results)} шт.")
        return results


class Metric1Collector(BaseCollector):
    @property
    def metric_id(self):
        return "metric_1"

    def __init__(self, config):
        super().__init__(config)
        self.openalex = OpenAlexAdapter(config)

    def collect(self, year):
        validate_year(year)
        oa = self.openalex.fetch_ai_publications(year)
        deduped = dedup_publications(oa)
        # Общее количество всех AI-публикаций
        total_ai = len(deduped)
        # Топ-публикации
        top = [p for p in deduped if p.get("is_top_venue")]
        top_count = len(top)

        # Экспортируем все публикации в CSV
        csv_path = f"data/publications_{year}.csv"
        os.makedirs("data", exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["title", "authors", "doi", "venue", "source", "year", "is_top_venue"])
            for p in deduped:
                writer.writerow(
                    [p.get(k, "") for k in ["title", "authors", "doi", "venue", "source", "year", "is_top_venue"]])
        logger.info(f"CSV сохранён: {csv_path}, {total_ai} записей")

        # В заметках храним оба числа
        notes = f"Всего AI-публикаций (OpenAlex): {total_ai}; Топ-публикаций (A*/Q1): {top_count}"
        logger.info(f"Metric 1: всего AI = {total_ai}, топ = {top_count}")

        pubs = []
        for p in top:
            pubs.append(Publication(
                title=p["title"],
                authors=p["authors"],
                doi=p.get("doi", ""),
                venue=p["venue"],
                source=p["source"],
                year=year,
                is_russian_affiliated=True,
            ))
        metric_value = MetricValue(year=year, value=float(top_count), source="OpenAlex", notes=notes)
        return metric_value, pubs