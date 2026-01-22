from __future__ import annotations

import io
import json
import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Prop Trader MVP", layout="wide")

st.title("Prop Trader MVP")

with st.sidebar:
    st.header("Ustawienia")
    period = st.selectbox("Okres analizy", options=[7, 30, 90], index=1)
    max_daily_dd = st.number_input("Max daily DD", min_value=0.0, step=100.0, value=0.0)
    max_total_dd = st.number_input("Max total DD", min_value=0.0, step=100.0, value=0.0)
    account_size = st.number_input("Account size", min_value=0.0, step=1000.0, value=0.0)

    limits = {
        "max_daily_dd": max_daily_dd or None,
        "max_total_dd": max_total_dd or None,
        "account_size": account_size or None,
    }
    limits_json = json.dumps(limits)

uploaded_file = st.file_uploader("Wgraj CSV z transakcjami", type=["csv"])

if uploaded_file:
    st.success("Plik załadowany.")
    params = {"period_days": period}
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    if st.button("Policz metryki"):
        response = requests.post(
            f"{BACKEND_URL}/metrics",
            params=params,
            data={"limits": limits_json},
            files=files,
            timeout=30,
        )
        if response.status_code != 200:
            st.error(f"Błąd: {response.text}")
        else:
            payload = response.json()
            core = payload["core"]
            st.subheader("Metryki")
            col1, col2, col3 = st.columns(3)
            col1.metric("Winrate", f"{core['winrate'] * 100:.1f}%")
            col2.metric("Trade count", core["trade_count"])
            col3.metric("Profit factor", core["profit_factor"])

            st.write(pd.DataFrame([core]))

            st.subheader("Equity curve")
            st.line_chart(payload["equity_curve"])

            st.subheader("Sesje")
            st.dataframe(pd.DataFrame(payload["sessions"]))

            st.subheader("Zachowania")
            st.json(payload["behaviors"])

            if payload["daily_violations"]:
                st.subheader("Naruszenia DD")
                st.dataframe(pd.DataFrame(payload["daily_violations"]))

            if payload["warnings"]:
                st.warning("\n".join(payload["warnings"]))

    if st.button("Generuj raport AI"):
        response = requests.post(
            f"{BACKEND_URL}/report",
            params=params,
            data={"limits": limits_json},
            files=files,
            timeout=60,
        )
        if response.status_code != 200:
            st.error(f"Błąd: {response.text}")
        else:
            payload = response.json()
            report_md = payload["report_markdown"]
            st.subheader("Raport")
            st.markdown(report_md)

            buffer = io.BytesIO(report_md.encode("utf-8"))
            st.download_button(
                label="Pobierz raport .md",
                data=buffer,
                file_name="raport.md",
                mime="text/markdown",
            )
else:
    st.info("Wgraj plik CSV, aby rozpocząć analizę.")
