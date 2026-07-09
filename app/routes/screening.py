import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import ScreeningSession, ScreeningResult, User, Company
from app.schemas.schemas import (
    ScreeningRequest,
    ScreeningResultResponse,
    ScreeningSessionResponse,
    ScreeningSessionDetailResponse,
)
from app.services.screen_engine import execute_screening
from app.auth import get_current_user

router = APIRouter(prefix="/screen", tags=["screening"])


@router.post("")
def run_screening(
    request: ScreeningRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Execute screening with criteria and store results."""
    results_data = execute_screening(db, request.criteria)

    # Create session
    session = ScreeningSession(
        user_id=user.id,
        name=request.name or "Screening Results",
        criteria=request.criteria.model_dump(),
        result_count=len(results_data),
    )
    db.add(session)
    db.flush()

    # Store individual results
    for item in results_data:
        result = ScreeningResult(
            session_id=session.id,
            company_id=item["company_id"],
            metrics_snapshot={
                k: v
                for k, v in item.items()
                if k not in ("company_id", "rank")
            },
            rank=item["rank"],
        )
        db.add(result)

    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "result_count": len(results_data),
        "results": results_data,
    }


@router.get("/sessions", response_model=List[ScreeningSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ScreeningSession)
        .filter(ScreeningSession.user_id == user.id)
        .order_by(ScreeningSession.created_at.desc())
        .limit(20)
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=ScreeningSessionDetailResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.id == session_id,
            ScreeningSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load results with company data
    results = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.session_id == session_id)
        .order_by(ScreeningResult.rank)
        .all()
    )

    return ScreeningSessionDetailResponse(
        id=session.id,
        name=session.name,
        criteria=session.criteria,
        result_count=session.result_count,
        created_at=session.created_at,
        results=[
            ScreeningResultResponse(
                rank=r.rank,
                company_id=r.company_id,
                company=r.company,
                metrics_snapshot=r.metrics_snapshot,
            )
            for r in results
        ],
    )


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id: int,
    format: str = Query("csv"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.id == session_id,
            ScreeningSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    results = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.session_id == session_id)
        .order_by(ScreeningResult.rank)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    # Header
    writer.writerow(
        [
            "Rank",
            "Company",
            "Ticker",
            "Exchange",
            "Sector",
            "Revenue Growth",
            "PAT Growth",
            "P/E Ratio",
            "Dividend Yield",
            "Market Cap",
            "P/B Ratio",
            "ROE",
            "Debt/Equity",
        ]
    )

    for r in results:
        m = r.metrics_snapshot or {}
        company = r.company
        exchange_code = company.exchange.code if company and company.exchange else ""
        writer.writerow(
            [
                r.rank,
                m.get("company_name", ""),
                m.get("ticker", ""),
                exchange_code,
                m.get("sector", ""),
                m.get("revenue_growth_1y", ""),
                m.get("pat_growth_1y", ""),
                m.get("pe_ratio", ""),
                m.get("dividend_yield", ""),
                m.get("market_cap", ""),
                m.get("pb_ratio", ""),
                m.get("roe", ""),
                m.get("debt_to_equity", ""),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=screening_{session_id}.csv"
        },
    )
