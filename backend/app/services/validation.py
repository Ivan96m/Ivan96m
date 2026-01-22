from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

REQUIRED_COLUMNS = {
    "open_time",
    "close_time",
    "symbol",
    "side",
    "volume",
    "entry_price",
    "exit_price",
}

OPTIONAL_COLUMNS = {"sl", "tp", "profit", "pips", "commission", "swap"}


COLUMN_ALIASES = {
    "open_time": ["open_time", "open", "entry_time", "open_date"],
    "close_time": ["close_time", "close", "exit_time", "close_date"],
    "symbol": ["symbol", "instrument", "pair"],
    "side": ["side", "type", "direction"],
    "volume": ["volume", "lot", "lots", "size"],
    "entry_price": ["entry_price", "open_price", "price_open"],
    "exit_price": ["exit_price", "close_price", "price_close"],
    "sl": ["sl", "stop_loss", "stop"],
    "tp": ["tp", "take_profit", "target"],
    "profit": ["profit", "pnl", "p&l", "net_profit"],
    "pips": ["pips", "pip"],
    "commission": ["commission", "fee"],
    "swap": ["swap", "swap_fee"],
}


class ValidationError(Exception):
    def __init__(self, message: str, extra: Dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.extra = extra or {}


def _find_column(mapping: Dict[str, List[str]], columns: List[str]) -> Dict[str, str]:
    column_map: Dict[str, str] = {}
    lower_columns = {col.lower(): col for col in columns}
    for canonical, aliases in mapping.items():
        for alias in aliases:
            if alias.lower() in lower_columns:
                column_map[canonical] = lower_columns[alias.lower()]
                break
    return column_map


def normalize_trades(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    warnings: List[str] = []
    column_map = _find_column(COLUMN_ALIASES, df.columns.tolist())

    missing = REQUIRED_COLUMNS - set(column_map.keys())
    if missing:
        raise ValidationError("Brak wymaganych kolumn.", {"missing": ", ".join(sorted(missing))})

    df = df.rename(columns={column_map[key]: key for key in column_map})

    if "profit" not in df.columns and "pips" in df.columns:
        df["profit"] = df["pips"]
        warnings.append("Brak kolumny profit. Użyto pips jako przybliżenia wyniku.")
    elif "profit" not in df.columns:
        raise ValidationError("Brak kolumny profit lub pips.")

    for col in ["open_time", "close_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    if df["open_time"].isna().any() or df["close_time"].isna().any():
        raise ValidationError("Niepoprawny format czasu w open_time lub close_time.")

    numeric_cols = [
        "volume",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "profit",
        "commission",
        "swap",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if df["volume"].isna().any() or df["entry_price"].isna().any() or df["exit_price"].isna().any():
        raise ValidationError("Niepoprawne wartości liczbowe w volume/entry_price/exit_price.")

    df["side"] = df["side"].astype(str).str.lower()
    if not df["side"].isin(["buy", "sell"]).all():
        raise ValidationError("Kolumna side musi zawierać wartości buy/sell.")

    df["symbol"] = df["symbol"].astype(str)

    return df, warnings
