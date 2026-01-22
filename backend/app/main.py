from __future__ import annotations

from datetime import datetime
from typing import List

import json
import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .models import Report
from .schemas import (
    BehaviorFlags,
    CoreMetrics,
    ErrorResponse,
    Limits,
    MetricsResponse,
    ReportResponse,
    ReportsList,
    SessionStats,
    Violation,
)
from .services.behaviors import (
    detect_early_tp_closes,
    detect_overtrading,
    detect_revenge_trading,
    sl_moved_against_data_available,
)
from .services.llm import LLMClient
from .services.metrics import (
    compute_core_metrics,
    daily_drawdown,
    equity_curve,
    filter_period,
    session_breakdown,
)
from .services.report import build_report_payload
from .services.validation import ValidationError, normalize_trades

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prop Trader MVP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


def _parse_limits(limits_json: str | None) -> Limits | None:
    if not limits_json:
        return None
    data = json.loads(limits_json)
    return Limits(**data)


@app.post("/metrics", response_model=MetricsResponse, responses={400: {"model": ErrorResponse}})
async def metrics(
    period_days: int = Form(30),
    limits: str | None = Form(None),
    file: UploadFile = File(...),
) -> MetricsResponse:
    try:
        df = pd.read_csv(file.file)
        df, warnings = normalize_trades(df)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0]) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        limit_data = _parse_limits(limits)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Niepoprawny format limitów.") from exc
    df = filter_period(df, period_days)
    core = compute_core_metrics(df)
    sessions = session_breakdown(df)
    behaviors = BehaviorFlags(
        overtrading=detect_overtrading(df),
        revenge_trading=detect_revenge_trading(df),
        early_tp_closes=detect_early_tp_closes(df),
        sl_moved_against=sl_moved_against_data_available(df),
    )

    daily_df = daily_drawdown(df)
    violations: List[Violation] = []
    if limit_data and limit_data.max_daily_dd is not None:
        limit = limit_data.max_daily_dd
        for _, row in daily_df.iterrows():
            dd = float(row["daily_drawdown"])
            violations.append(
                Violation(
                    date=str(row["date"]),
                    daily_drawdown=dd,
                    limit=limit,
                    breached=dd <= -abs(limit),
                )
            )

    return MetricsResponse(
        core=CoreMetrics(**core.__dict__),
        sessions=[SessionStats(**session.__dict__) for session in sessions],
        behaviors=behaviors,
        equity_curve=equity_curve(df["profit"].to_numpy()),
        daily_violations=violations,
        warnings=warnings,
    )


@app.post("/report", response_model=ReportResponse, responses={400: {"model": ErrorResponse}})
async def report(
    period_days: int = Form(30),
    limits: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReportResponse:
    try:
        df = pd.read_csv(file.file)
        df, warnings = normalize_trades(df)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0]) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        limit_data = _parse_limits(limits)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Niepoprawny format limitów.") from exc
    df = filter_period(df, period_days)
    core = compute_core_metrics(df)
    sessions = session_breakdown(df)
    behaviors = BehaviorFlags(
        overtrading=detect_overtrading(df),
        revenge_trading=detect_revenge_trading(df),
        early_tp_closes=detect_early_tp_closes(df),
        sl_moved_against=sl_moved_against_data_available(df),
    )
    daily_df = daily_drawdown(df)
    violations = daily_df[["date", "daily_drawdown"]].to_dict(orient="records")

    payload_data = build_report_payload(
        metrics={
            "core": core.__dict__,
            "sessions": [session.__dict__ for session in sessions],
        },
        behaviors=behaviors.dict(),
        violations={"daily": violations, "warnings": warnings},
        limits=limit_data.dict() if limit_data else None,
    )

    llm = LLMClient()
    report_text = llm.generate_report(payload_data)
    report_record = Report(report_markdown=report_text, summary=None)
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return ReportResponse(
        report_markdown=report_text,
        report_id=report_record.id,
        created_at=report_record.created_at,
    )


@app.get("/reports", response_model=ReportsList)
async def list_reports(db: Session = Depends(get_db)) -> ReportsList:
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return ReportsList(
        reports=[
            {
                "id": report.id,
                "created_at": report.created_at,
                "report_markdown": report.report_markdown,
                "summary": report.summary,
            }
            for report in reports
        ]
    )
