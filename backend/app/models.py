from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Text

from .db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    summary = Column(Text, nullable=True)
    report_markdown = Column(Text, nullable=False)
