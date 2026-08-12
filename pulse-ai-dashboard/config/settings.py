from __future__ import annotations
import os
import yaml
from pathlib import Path
from pulseai_utils.logger import get_logger

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_yaml(path):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_config(config_path=None):
    path = Path(config_path).resolve() if config_path else PROJECT_ROOT / "config.yaml"
    cfg = load_yaml(path)
    logger.info(f"Конфиг загружен: {path}")
    return cfg

_manual_cache = None

def load_manual_data(path=None):
    global _manual_cache
    if _manual_cache is not None:
        return _manual_cache
    path = Path(path).resolve() if path else PROJECT_ROOT / "manual_data.yaml"
    if not path.exists():
        logger.warning(f"manual_data.yaml не найден в {path}. Метрики M2-M5 будут Н/Д.")
        _manual_cache = {}
        return {}
    _manual_cache = load_yaml(path)
    logger.info(f"Ручные данные загружены: {path}")
    return _manual_cache