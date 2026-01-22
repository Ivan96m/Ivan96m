from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Limits(BaseModel):
    max_daily_dd: Optional[float] = Field(default=None, ge=0)
    max_total_dd: Optional[float] = Field(default=None, ge=0)
    account_size: Optional[float] = Field(default=None, gt=0)


class MetricsRequest(BaseModel):
    period_days: int = Field(default=30, ge=1, le=365)
    limits: Optional[Limits] = None


class TradeRecord(BaseModel):
    open_time: datetime
    close_time: datetime
    symbol: str
    side: str
    volume: float
    entry_price: float
    exit_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    profit: float
    commission: Optional[float] = None
    swap: Optional[float] = None


class CoreMetrics(BaseModel):
    trade_count: int
    winrate: float
    avg_profit: float
    avg_loss: float
    median_profit: float
    profit_factor: Optional[float]
    expectancy: float
    average_rr: Optional[float]
    max_drawdown: float


class SessionStats(BaseModel):
    session: str
    trade_count: int
    winrate: float
    avg_profit: float


class BehaviorFlags(BaseModel):
    overtrading: List[str]
    revenge_trading: List[str]
    early_tp_closes: List[str]
    sl_moved_against: str


class Violation(BaseModel):
    date: str
    daily_drawdown: float
    limit: float
    breached: bool


class MetricsResponse(BaseModel):
    core: CoreMetrics
    sessions: List[SessionStats]
    behaviors: BehaviorFlags
    equity_curve: List[float]
    daily_violations: List[Violation]
    warnings: List[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    report_markdown: str
    report_id: Optional[int] = None
    created_at: Optional[datetime] = None


class ReportRecord(BaseModel):
    id: int
    created_at: datetime
    report_markdown: str
    summary: Optional[str]


class ReportsList(BaseModel):
    reports: List[ReportRecord]


class ErrorResponse(BaseModel):
    detail: str
    extra: Optional[Any] = None
