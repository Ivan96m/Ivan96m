from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd


def detect_overtrading(df: pd.DataFrame, window_minutes: int = 60, trade_threshold: int = 5) -> List[str]:
    df = df.sort_values("open_time")
    times = df["open_time"]
    flags = []
    for idx, time in times.items():
        start = time - pd.Timedelta(minutes=window_minutes)
        window_count = times[(times >= start) & (times <= time)].count()
        if window_count > trade_threshold:
            flags.append(
                f"{time.date()} {time.time()} - {window_count} transakcji w {window_minutes} min"
            )
    return flags


def detect_revenge_trading(df: pd.DataFrame) -> List[str]:
    df = df.sort_values("open_time").reset_index(drop=True)
    flags = []
    losses = df["profit"] < 0
    for i in range(2, len(df)):
        if losses.iloc[i - 2] and losses.iloc[i - 1]:
            prev_volume = df.loc[i - 1, "volume"]
            current_volume = df.loc[i, "volume"]
            median_gap = _median_gap_minutes(df)
            gap = (df.loc[i, "open_time"] - df.loc[i - 1, "open_time"]).total_seconds() / 60
            if current_volume > prev_volume * 1.5 or gap < median_gap / 2:
                flags.append(
                    f"{df.loc[i, 'open_time'].date()} - możliwy revenge trading po 2 stratach"
                )
    return flags


def detect_early_tp_closes(df: pd.DataFrame, ratio_threshold: float = 0.8) -> List[str]:
    if "tp" not in df.columns or "sl" not in df.columns:
        return ["Brak danych TP/SL do oceny early TP closes."]

    df = df.copy()
    df = df[df["tp"].notna() & df["sl"].notna()]
    if df.empty:
        return ["Brak danych TP/SL do oceny early TP closes."]

    reward_planned = (df["tp"] - df["entry_price"]).abs()
    risk = (df["entry_price"] - df["sl"]).abs()
    risk = risk.replace(0, np.nan)
    planned_rr = reward_planned / risk
    realized_rr = (df["exit_price"] - df["entry_price"]).abs() / risk

    flags = []
    for idx, row in df.iterrows():
        if row["profit"] > 0 and planned_rr.loc[idx] > 0:
            if realized_rr.loc[idx] < planned_rr.loc[idx] * ratio_threshold:
                flags.append(f"{row['close_time'].date()} - zamknięcie TP przed planowanym RR")
    return flags


def sl_moved_against_data_available(df: pd.DataFrame) -> str:
    return "Brak danych o zmianach SL w historii transakcji."


def _median_gap_minutes(df: pd.DataFrame) -> float:
    if len(df) < 2:
        return 0.0
    gaps = df["open_time"].diff().dropna().dt.total_seconds() / 60
    return float(gaps.median()) if not gaps.empty else 0.0
