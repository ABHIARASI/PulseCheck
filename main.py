from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from models import MonitorResult, Monitor
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time

from database import SessionLocal

scheduler = BackgroundScheduler()


def run_scheduled_checks():
    db = SessionLocal()

    try:
        monitors = (
            db.query(Monitor)
            .filter(Monitor.is_active == True)
            .all()
        )

        for monitor in monitors:
            try:
                response = httpx.get(
                    monitor.url,
                    timeout=5.0,
                    follow_redirects=True
                )

                result = MonitorResult(
                    url=monitor.url,
                    status_code=response.status_code,
                    response_time_ms=round(
                        response.elapsed.total_seconds() * 1000, 2
                    ),
                    is_healthy=200 <= response.status_code < 400
                )

            except httpx.RequestError:
                result = MonitorResult(
                    url=monitor.url,
                    status_code=None,
                    response_time_ms=None,
                    is_healthy=False
                )

            db.add(result)

        db.commit()

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        run_scheduled_checks,
        "interval",
        minutes=1,
        id="monitor_checks",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="PulseCheck API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MonitorRequest(BaseModel):
    url: HttpUrl


class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "PulseCheck API is running!"}


@app.post("/check")
def check_api(request: MonitorRequest, db: Session = Depends(get_db)):
    start_time = time.perf_counter()

    try:
        response = httpx.get(
            str(request.url),
            timeout=5.0,
            follow_redirects=True
        )

        response_time = round(
            (time.perf_counter() - start_time) * 1000, 2
        )

        is_healthy = 200 <= response.status_code < 400

        result = MonitorResult(
            url=str(request.url),
            status_code=response.status_code,
            response_time_ms=response_time,
            is_healthy=is_healthy
        )

    except httpx.TimeoutException:
        result = MonitorResult(
            url=str(request.url),
            status_code=None,
            response_time_ms=5000.0,
            is_healthy=False
        )

    except httpx.RequestError:
        result = MonitorResult(
            url=str(request.url),
            status_code=None,
            response_time_ms=None,
            is_healthy=False
        )

    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "id": result.id,
        "url": result.url,
        "status_code": result.status_code,
        "response_time_ms": result.response_time_ms,
        "is_healthy": result.is_healthy,
        "checked_at": result.checked_at
    }


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    results = (
        db.query(MonitorResult)
        .order_by(MonitorResult.id.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": result.id,
            "url": result.url,
            "status_code": result.status_code,
            "response_time_ms": result.response_time_ms,
            "is_healthy": result.is_healthy,
            "checked_at": result.checked_at
        }
        for result in results
    ]


@app.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total = db.query(MonitorResult).count()

    successful = (
        db.query(MonitorResult)
        .filter(MonitorResult.is_healthy == True)
        .count()
    )

    failed = total - successful

    uptime = round((successful / total) * 100, 2) if total else 0

    return {
        "total_checks": total,
        "successful_checks": successful,
        "failed_checks": failed,
        "uptime_percentage": uptime
    }


@app.post("/monitors")
def create_monitor(
    request: MonitorCreate,
    db: Session = Depends(get_db)
):
    monitor = Monitor(
        name=request.name,
        url=str(request.url)
    )

    db.add(monitor)

    try:
        db.commit()
        db.refresh(monitor)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not register monitor; URL may already exist"
        )

    return {
        "id": monitor.id,
        "name": monitor.name,
        "url": monitor.url,
        "is_active": monitor.is_active
    }


@app.get("/monitors")
def list_monitors(db: Session = Depends(get_db)):
    monitors = db.query(Monitor).order_by(Monitor.id.desc()).all()

    return [
        {
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "is_active": monitor.is_active
        }
        for monitor in monitors
    ]

@app.get("/monitors/{monitor_id}/latest")
def get_latest_check(
    monitor_id: int,
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id
    ).first()

    if not monitor:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found"
        )

    result = (
        db.query(MonitorResult)
        .filter(MonitorResult.url == monitor.url)
        .order_by(MonitorResult.id.desc())
        .first()
    )

    if not result:
        return {
            "monitor_id": monitor.id,
            "url": monitor.url,
            "status": "Pending",
            "response_time_ms": None,
            "checked_at": None
        }

    return {
        "monitor_id": monitor.id,
        "url": monitor.url,
        "status": "Healthy" if result.is_healthy else "Unhealthy",
        "status_code": result.status_code,
        "response_time_ms": result.response_time_ms,
        "checked_at": result.checked_at
    }
