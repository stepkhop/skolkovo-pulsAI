from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from config.settings import load_config
from pulseai_utils.logger import get_logger

logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pulse AI Dashboard — сбор метрик",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py --collect --year 2025           # собрать все метрики за 2025
  python main.py --collect --year 2025 --metric 1  # только метрика 1
  python main.py --collect --all-years             # собрать за все годы
  python main.py --dashboard                       # запустить Streamlit дашборд
        """,
    )
    parser.add_argument("--collect", action="store_true", help="Запустить сбор метрик")
    parser.add_argument("--year", type=int, default=None, help="Год для сбора (по умолчанию из конфига)")
    parser.add_argument("--metric", type=int, choices=[1, 2, 3, 4, 5], default=None, help="Собрать только одну метрику (1-5)")
    parser.add_argument("--all-years", action="store_true", help="Собрать за все годы из конфига")
    parser.add_argument("--dashboard", action="store_true", help="Запустить Streamlit дашборд")
    parser.add_argument("--config", type=str, default="config.yaml", help="Путь к конфигу (по умолчанию config.yaml)")
    return parser.parse_args()

def run_collection(config: dict[str, Any], year: int | None, metric: int | None) -> None:
    from core.orchestrator import Orchestrator
    orchestrator = Orchestrator(config)
    if metric:
        logger.info("=== Сбор только метрики %d за %s ===", metric, year or "default")
        orchestrator.run_single_metric(metric, year)
    else:
        logger.info("=== Сбор всех метрик за %s ===", year or "default")
        orchestrator.run(year)
    logger.info("=== Сбор завершён ===")

def run_dashboard() -> None:
    project_root = Path(__file__).resolve().parent
    dashboard_path = project_root / "ui" / "pages" / "dashboard.py"
    if not dashboard_path.exists():
        logger.error("Dashboard файл не найден: %s", dashboard_path)
        sys.exit(1)
    logger.info("Запуск Streamlit дашборда: %s", dashboard_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
        check=True,
        env=env,
        cwd=str(project_root),
    )

def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.dashboard:
        run_dashboard()
        return 0
    if not args.collect:
        logger.error("Укажите --collect или --dashboard. Используйте --help для справки.")
        return 1
    if args.all_years:
        years = config.get("collection", {}).get("years_to_collect", [2025])
        for y in years:
            run_collection(config, y, args.metric)
    else:
        year = args.year or config.get("collection", {}).get("default_year", 2025)
        run_collection(config, year, args.metric)
    return 0

if __name__ == "__main__":
    sys.exit(main())