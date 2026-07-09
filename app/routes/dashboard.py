from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Company, Exchange, ScreeningSession
from app.schemas.schemas import DashboardStats
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    total_companies = db.query(Company).count()
    total_exchanges = db.query(Exchange).count()
    latest_count = (
        db.query(ScreeningSession)
        .filter(ScreeningSession.user_id == user.id)
        .order_by(ScreeningSession.created_at.desc())
        .first()
    )
    return DashboardStats(
        total_companies=total_companies,
        total_exchanges=total_exchanges,
        latest_screen_results=latest_count.result_count if latest_count else 0,
    )
