# skolkovo-pulsAI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

Готовое решение по результатам стажировки в Сколково для автоматического сбора, агрегации и хранения аналитических метрик в области ИИ-исследований, публикаций и образования

## 📋 Содержание

- [Описание](#описание)
- [Стек технологий](#стек-технологий)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [Сбор метрик](#сбор-метрик)
- [Запуск дашборда](#запуск-дашборда)
- [Структура ручных данных](#структура-ручных-данных)
- [Архитектура](#архитектура)
- [Безопасность](#безопасность)
- [Лицензия](#лицензия)

---

## Описание

`pulsAI` — Python-приложение для автоматического сбора, агрегации и хранения аналитических метрик в области ИИ-исследований, публикаций и образования

**Поддерживаемые метрики:**

| Метрика | Название | Источник |
|---------|----------|----------|
| Metric 1 | Топ-публикации по ИИ | OpenAlex API |
| Metric 2 | Квалифицированные ИИ-исследователи | Ручной ввод |
| Metric 3 | Студенты с ЕГЭ 81+ и олимпиадники | Ручной ввод |
| Metric 4 | Доля исследователей до 39 лет | Ручной ввод |
| Metric 5 | Студенты-исследователи в ИИ-центрах | Ручной ввод |

---

## Стек технологий

- Python 3.10+
- SQLite — локальное хранилище метрик
- OpenAlex API — сбор публикационных данных
- Streamlit — интерактивный дашборд

---

## Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
git clone https://github.com/stepkhop/skolkovo-pulsAI.git
cd skolkovo-pulsAI

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Настройка конфигурации

Создайте файлы конфигурации из шаблонов:

```bash
cp config.example.yaml config.yaml
cp manual_data.example.yaml manual_data.yaml
```

Отредактируйте `config.yaml` и укажите реальный API-ключ для OpenAlex:

```yaml
api_keys:
  openalex: "your_openalex_api_key_here"
```

Переменные окружения имеют приоритет над значениями в файле конфигурации. Для OpenAlex можно также использовать переменную `OPENALEX_API_KEY`

---

## Сбор метрик

Запуск сбора всех метрик за указанный год:

```bash
python main.py --year 2026
```

Сбор только одной метрики:

```bash
python main.py --year 2026 --metric 1
```

---

## Запуск дашборда

```bash
streamlit run ui/pages/dashboard.py
```

Убедитесь, что база данных `data/pulse_ai.db` создана перед запуском дашборда

---

## Конфигурация

Основные параметры задаются в `config.yaml`.

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `app.db_path` | `string` | `data/pulse_ai.db` | Путь к файлу SQLite |
| `api_keys.openalex` | `string` | `""` | API-ключ OpenAlex (env: `OPENALEX_API_KEY`) |
| `metric_1.enabled` | `boolean` | `true` | Включить сбор Metric 1 |
| `metric_1.openalex.email` | `string` | `""` | Email для OpenAlex API (рекомендуется) |
| `collection.default_year` | `integer` | Текущий год | Год для сбора по умолчанию |

---

## Структура ручных данных

Файл `manual_data.yaml` используется для метрик 2–5. Пример заполнения:

```yaml
metric_2_researchers:
  2023:
    value: 45
    source: "Минобрнауки"
    notes: "Квалифицированные исследователи в области ИИ"

metric_3_ege:
  2023:
    value: 120
    source: "Рособрнадзор"
    notes: "Студенты с ЕГЭ 81+ и победители олимпиад"

metric_4_age:
  2023:
    value: 62.5
    source: "Внутренняя аналитика"
    notes: "Доля исследователей до 39 лет, %"

metric_5_students:
  2023:
    value: 89
    source: "Университеты-партнёры"
    notes: "Студенты-исследователи в ИИ-центрах"
```

---

## Архитектура

```text
skolkovo-pulsAI/
├── collectors/                 # Коллекторы метрик
│   ├── __init__.py
│   ├── base.py                 # Базовый класс BaseCollector
│   ├── metric1_publications.py # OpenAlex API
│   ├── metric2_researchers.py  # Ручные данные
│   ├── metric3_ege.py          # Ручные данные
│   ├── metric4_age.py          # Ручные данные
│   └── metric5_students.py     # Ручные данные
├── config/                     # Конфигурация приложения
│   ├── __init__.py
│   └── settings.py
├── core/                       # Оркестратор и агрегатор
│   ├── __init__.py
│   ├── aggregator.py
│   └── orchestrator.py
├── data/                       # Данные и локальная БД
│   ├── publications_2022.csv
│   ├── publications_2023.csv
│   ├── publications_2024.csv
│   ├── publications_2025.csv
│   ├── publications_2026.csv
│   └── pulse_ai.db
├── logs/                       # Логи работы
├── models/                     # Модели данных
│   ├── __init__.py
│   └── metrics.py
├── pulseai_utils/              # Утилиты, валидаторы, исключения
│   ├── __init__.py
│   ├── exceptions.py
│   ├── logger.py
│   └── validators.py
├── reports/                    # Сгенерированные отчёты
├── storage/                    # Слой работы с БД
│   ├── __init__.py
│   ├── base.py
│   └── sqlite.py
├── streamlit/                  # Конфигурация Streamlit
│   └── config.toml
├── ui/                         # Интерфейс дашборда
│   ├── __init__.py
│   ├── components.py
│   ├── theme.py
│   └── pages/
│       ├── __init__.py
│       └── dashboard.py
├── config.yaml                 # Файл конфигурации
├── main.py                     # Точка входа (CLI)
├── manual_data.yaml            # Ручные данные для метрик 2–5
├── requirements.txt            # Зависимости
└── setup.py                    # Установка пакета
```

---

## Безопасность

API-ключ не хранится в репозитории. Используйте переменную окружения `OPENALEX_API_KEY` или задавайте его через `.env` файл

Файлы `config.yaml` и `manual_data.yaml` обязательно добавьте в `.gitignore`

База данных `data/pulse_ai.db` и папка `data/` также должны быть исключены из Git

Все SQL-запросы в `storage/sqlite.py` параметризованы (`?`), что исключает риск SQL-инъекций

Пример `.gitignore` (создайте его в корне проекта):

```gitignore
# Конфигурационные файлы с секретами
config.yaml
manual_data.yaml

# База данных и сгенерированные данные
data/
*.db

# Виртуальное окружение
venv/
env/
__pycache__/

# Файлы IDE
.vscode/
.idea/

# Файлы окружения
.env
```

---

## Лицензия

Проект распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](LICENSE)
