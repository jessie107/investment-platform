from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.data_fetcher import update_all_companies

router = APIRouter(tags=["data"])


@router.post("/refresh-all-data")
def refresh_all_data(db: Session = Depends(get_db)):
    """Public endpoint to refresh all company data from Yahoo Finance."""
    update_all_companies(db)
    return {"message": "Market data refresh completed", "status": "ok"}
