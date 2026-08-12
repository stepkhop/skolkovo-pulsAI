from __future__ import annotations

import streamlit as st

def metric_card(label: str, value: str | float | None, unit: str = "", delta: str = "") -> None:
    if value is None:
        value_str = "Н/Д"
    else:
        value_str = f"{value:,.0f}" if isinstance(value, float) and value == int(value) else f"{value}"
        if unit:
            value_str += f" {unit}"
    st.metric(label=label, value=value_str, delta=delta or None)


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)