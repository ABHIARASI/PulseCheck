
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class MonitorResult(Base):
    __tablename__ = "monitor_results"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    is_healthy = Column(Boolean, nullable=False)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
