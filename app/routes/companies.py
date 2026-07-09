from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.database import get_db
from app.models.models import Company, Exchange, FinancialStatement, DailyPrice, ComputedMetric
from app.schemas.schemas import (
    CompanyResponse,
    CompanyListResponse,
    FinancialStatementResponse,
    DailyPriceResponse,
    ComputedMetricResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    exchange: Optional[str] = None,
    sector: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Company).join(Exchange)

    if search:
        query = query.filter(
            or_(
                Company.name.ilike(f"%{search}%"),
                Company.ticker.ilike(f"%{search}%"),
            )
        )
    if exchange:
        query = query.filter(Exchange.code == exchange.upper())
    if sector:
        query = query.filter(Company.sector.ilike(f"%{sector}%"))

    total = query.count()
    items = (
        query.order_by(Company.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CompanyListResponse(
        total=total, page=page, page_size=page_size, items=items
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/{company_id}/financials", response_model=List[FinancialStatementResponse])
def get_company_financials(
    company_id: int,
    years: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    statements = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_type == "FY",
        )
        .order_by(FinancialStatement.fiscal_year.desc())
        .limit(years)
        .all()
    )
    return statements


@router.get("/{company_id}/prices", response_model=List[DailyPriceResponse])
def get_company_prices(
    company_id: int,
    limit: int = Query(252, ge=1, le=1000),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.company_id == company_id)
        .order_by(DailyPrice.trade_date.desc())
        .limit(limit)
        .all()
    )
    # Return chronological order
    prices.reverse()
    return prices


@router.get("/{company_id}/metrics", response_model=Optional[ComputedMetricResponse])
def get_company_metrics(
    company_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    metric = (
        db.query(ComputedMetric)
        .filter(ComputedMetric.company_id == company_id)
        .order_by(ComputedMetric.computed_date.desc())
        .first()
    )
    return metric
