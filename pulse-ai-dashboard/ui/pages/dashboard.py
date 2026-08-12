from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st
import re

st.set_page_config(
    page_title="Пульс ИИ — Российская экосистема ИИ",
    page_icon="🧠",
    layout="wide",
)

from config.settings import load_config
from core.aggregator import Aggregator
from models.metrics import MetricType
from storage.sqlite import SQLiteStorage

def render_sidebar() -> int:
    with st.sidebar:
        st.title("🧠 Пульс ИИ")
        st.caption("Российская экосистема ИИ")
        st.divider()
        config = load_config()
        years = config["collection"]["years_to_collect"]
        year = st.selectbox("📅 Отчётный год", years, index=len(years)-1)
        st.markdown("**Метрики**")
        st.markdown("1. Число топ-публикаций РФ по ИИ")
        st.markdown("2. Квалифицированные ИИ-исследователи")
        st.markdown("3. ЕГЭ 81+ и олимпиадники")
        st.markdown("4. Доля исследователей до 39 лет")
        st.markdown("5. Student researchers в ИИ-центрах")
        st.divider()
        if st.button("🔄 Обновить данные", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        return year

@st.cache_data(ttl=3600)
def load_data(year):
    cfg = load_config()
    storage = SQLiteStorage(cfg["app"]["db_path"])
    aggregator = Aggregator(storage)
    return aggregator.get_dashboard_data(year)

def render_publications(data, year):
    config = load_config()
    m1_cfg = config.get("metric_1", {})
    st.subheader(m1_cfg.get("name", "Метрика 1"))
    st.caption(m1_cfg.get("description", ""))

    pubs = data.publications.publications if data and data.publications else []
    top_count = len(pubs)

    total_ai = 0
    metric = data.get_metric(MetricType.PUBLICATIONS) if data else None
    if metric:
        val = metric.get_value_for_year(year)
        if val and val.notes:
            match = re.search(r"Всего AI-публикаций \(OpenAlex\): (\d+)", val.notes)
            if match:
                total_ai = int(match.group(1))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Топ-публикаций (A*/Q1)", f"{top_count} шт.")
    c2.metric("Всего AI-публикаций (OpenAlex)", f"{total_ai} шт." if total_ai else "—")
    c3.metric("Уникальных топ-площадок", f"{len({p.venue for p in pubs})} шт.")
    c4.metric("Год", year)

    if pubs:
        with st.expander(f"📋 Показать {top_count} топ-публикаций"):
            df_data = []
            for p in pubs:
                authors_short = ", ".join(p.authors[:3])
                if len(p.authors) > 3:
                    authors_short += "..."
                df_data.append({
                    "Название": p.title,
                    "Авторы": authors_short,
                    "Площадка": p.venue,
                    "DOI": p.doi,
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
    else:
        st.info("Данных нет. Запустите сбор.")

def render_metrics(data, year):
    config = load_config()
    metrics_config = [
        (MetricType.RESEARCHERS, "metric_2"),
        (MetricType.ECONOMY, "metric_3"),
        (MetricType.EDUCATION, "metric_4"),
        (MetricType.STUDENTS, "metric_5"),
    ]
    for mt, cfg_key in metrics_config:
        st.divider()
        cfg = config.get(cfg_key, {})
        title = cfg.get("name", mt.value)
        description = cfg.get("description", "")
        unit = cfg.get("unit", "")
        st.subheader(title)
        if description:
            st.caption(description)

        series = data.get_metric(mt) if data else None
        if not series or not series.values:
            st.info("Нет данных. Проверьте manual_data.yaml")
            continue

        history = [(v.year, v.value) for v in series.values if v.value is not None]
        cur = series.get_value_for_year(year)

        col1, col2 = st.columns([1, 3])
        with col1:
            if cur and cur.value is not None:
                st.metric("Значение", f"{cur.value} {unit}")
            else:
                st.warning("Н/Д (данные за этот год ещё не собраны)")

        with col2:
            if len(history) > 1:
                df = pd.DataFrame(history, columns=["Год", "Значение"])
                fig = px.bar(
                    df,
                    x="Год",
                    y="Значение",
                    text="Значение",
                    labels={"Значение": f"Значение ({unit})" if unit else "Значение"}
                )
                fig.update_traces(texttemplate=f"%{{y}}{unit}", textposition="outside")
                fig.update_layout(
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#1e1e2e",
                    font_color="#fafafa",
                    yaxis_title=f"Значение ({unit})" if unit else "Значение"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нужно минимум 2 года для графика")

def main():
    year = render_sidebar()
    st.title(f"🧠 Пульс ИИ — Российская экосистема ИИ ({year} г.)")
    try:
        data = load_data(year)
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return
    render_publications(data, year)
    render_metrics(data, year)
    st.caption("Pulse AI v1.0 | OpenAlex + manual_data.yaml")

if __name__ == "__main__":
    main()