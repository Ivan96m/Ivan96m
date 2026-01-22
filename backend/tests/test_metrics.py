from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.services.metrics import compute_core_metrics


def _sample_df() -> pd.DataFrame:
    now = datetime(2024, 1, 1)
    return pd.DataFrame(
        {
            "open_time": [now + timedelta(hours=i) for i in range(4)],
            "close_time": [now + timedelta(hours=i, minutes=10) for i in range(4)],
            "symbol": ["EURUSD"] * 4,
            "side": ["buy", "sell", "buy", "sell"],
            "volume": [1, 1, 1, 1],
            "entry_price": [1.1, 1.2, 1.15, 1.18],
            "exit_price": [1.12, 1.18, 1.1, 1.2],
            "sl": [1.09, 1.25, 1.14, 1.17],
            "tp": [1.14, 1.15, 1.18, 1.21],
            "profit": [20, -10, -15, 25],
        }
    )


def test_compute_core_metrics_winrate() -> None:
    df = _sample_df()
    metrics = compute_core_metrics(df)
    assert metrics.trade_count == 4
    assert metrics.winrate == 0.5


def test_compute_core_metrics_profit_factor() -> None:
    df = _sample_df()
    metrics = compute_core_metrics(df)
    assert metrics.profit_factor == (45 / 25)


def test_compute_core_metrics_expectancy() -> None:
    df = _sample_df()
    metrics = compute_core_metrics(df)
    expected = 0.5 * 22.5 + 0.5 * (-12.5)
    assert metrics.expectancy == expected


def test_compute_core_metrics_max_drawdown() -> None:
    df = _sample_df()
    metrics = compute_core_metrics(df)
    assert metrics.max_drawdown == -25


def test_compute_core_metrics_average_rr() -> None:
    df = _sample_df()
    metrics = compute_core_metrics(df)
    assert metrics.average_rr is not None
    assert metrics.average_rr > 0
