from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd


@dataclass
class SessionSummary:
    session: str
    trade_count: int
    winrate: float
    avg_profit: float


@dataclass
class CoreMetrics:
    trade_count: int
    winrate: float
    avg_profit: float
    avg_loss: float
    median_profit: float
    profit_factor: Optional[float]
    expectancy: float
    average_rr: Optional[float]
    max_drawdown: float


SESSION_WINDOWS = {
    "Asia": (0, 7),
    "London": (7, 13),
    "New York": (13, 21),
    "Off": (21, 24),
}


def compute_core_metrics(df: pd.DataFrame) -> CoreMetrics:
    profits = df["profit"].to_numpy()
    trade_count = len(profits)
    wins = profits[profits > 0]
    losses = profits[profits < 0]

    winrate = float(len(wins) / trade_count) if trade_count else 0.0
    avg_profit = float(np.mean(wins)) if len(wins) else 0.0
    avg_loss = float(np.mean(losses)) if len(losses) else 0.0
    median_profit = float(np.median(profits)) if trade_count else 0.0
    profit_factor = None
    if losses.size > 0:
        profit_factor = float(wins.sum() / abs(losses.sum())) if losses.sum() else None

    expectancy = winrate * avg_profit + (1 - winrate) * avg_loss
    average_rr = _average_rr(df)
    max_drawdown = float(_max_drawdown(profits))

    return CoreMetrics(
        trade_count=trade_count,
        winrate=winrate,
        avg_profit=avg_profit,
        avg_loss=avg_loss,
        median_profit=median_profit,
        profit_factor=profit_factor,
        expectancy=float(expectancy),
        average_rr=average_rr,
        max_drawdown=max_drawdown,
    )


def _average_rr(df: pd.DataFrame) -> Optional[float]:
    if "sl" not in df.columns:
        return None
    valid = df["sl"].notna()
    if not valid.any():
        return None

    sl = df.loc[valid, "sl"].to_numpy()
    entry = df.loc[valid, "entry_price"].to_numpy()
    tp = df.loc[valid, "tp"].to_numpy() if "tp" in df.columns else None
    profit = df.loc[valid, "profit"].to_numpy()

    risk = np.abs(entry - sl)
    risk[risk == 0] = np.nan

    if tp is not None and not np.isnan(tp).all():
        reward = np.abs(tp - entry)
    else:
        reward = np.abs(profit)

    rr = reward / risk
    rr = rr[~np.isnan(rr)]
    if rr.size == 0:
        return None
    return float(np.mean(rr))


def _max_drawdown(profits: np.ndarray) -> float:
    if profits.size == 0:
        return 0.0
    equity = np.cumsum(profits)
    peak = np.maximum.accumulate(equity)
    drawdown = equity - peak
    return float(drawdown.min())


def equity_curve(profits: np.ndarray) -> List[float]:
    return list(np.cumsum(profits).astype(float))


def daily_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = df["close_time"].dt.date
    daily_profit = df.groupby("date")["profit"].sum().reset_index()
    daily_profit["equity"] = daily_profit["profit"].cumsum()
    daily_profit["peak"] = daily_profit["equity"].cummax()
    daily_profit["daily_drawdown"] = daily_profit["equity"] - daily_profit["peak"]
    return daily_profit


def session_breakdown(df: pd.DataFrame) -> List[SessionSummary]:
    df = df.copy()
    df["hour"] = df["open_time"].dt.hour
    df["session"] = df["hour"].apply(_session_from_hour)
    summaries = []
    for session, group in df.groupby("session"):
        profits = group["profit"]
        wins = profits[profits > 0]
        winrate = float(len(wins) / len(group)) if len(group) else 0.0
        summaries.append(
            SessionSummary(
                session=session,
                trade_count=len(group),
                winrate=winrate,
                avg_profit=float(profits.mean()),
            )
        )
    return sorted(summaries, key=lambda item: item.trade_count, reverse=True)


def _session_from_hour(hour: int) -> str:
    for session, (start, end) in SESSION_WINDOWS.items():
        if start <= hour < end:
            return session
    return "Off"


def filter_period(df: pd.DataFrame, period_days: int) -> pd.DataFrame:
    latest = df["close_time"].max()
    cutoff = latest - pd.Timedelta(days=period_days)
    return df[df["close_time"] >= cutoff]
