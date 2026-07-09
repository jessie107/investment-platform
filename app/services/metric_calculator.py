from sqlalchemy.orm import Session
from app.models.models import FinancialStatement, ComputedMetric, DailyPrice, Company
from datetime import date
import logging

logger = logging.getLogger(__name__)


def compute_metrics_for_company(db: Session, company_id: int, target_date: date = None) -> ComputedMetric:
    """Compute key financial metrics for a given company."""
    if target_date is None:
        target_date = date.today()

    # Get the two most recent fiscal years
    statements = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_type == "FY",
        )
        .order_by(FinancialStatement.fiscal_year.desc())
        .limit(2)
        .all()
    )

    if len(statements) < 2:
        logger.warning(f"Not enough financial data for company {company_id}")
        # Can still compute partial metrics
        current = statements[0] if statements else None
        previous = None
    else:
        current = statements[0]
        previous = statements[1]

    # Get latest price data
    latest_price = (
        db.query(DailyPrice)
        .filter(DailyPrice.company_id == company_id)
        .order_by(DailyPrice.trade_date.desc())
        .first()
    )

    company = db.query(Company).filter(Company.id == company_id).first()

    # --- Compute growth ---
    revenue_growth = None
    pat_growth = None
    if current and previous:
        if previous.revenue and previous.revenue > 0:
            revenue_growth = (
                (current.revenue - previous.revenue) / previous.revenue
            )
        if previous.profit_after_tax and previous.profit_after_tax > 0:
            pat_growth = (
                (current.profit_after_tax - previous.profit_after_tax)
                / previous.profit_after_tax
            )

    # --- Compute ratios ---
    pe_ratio = None
    if current and current.earnings_per_share and current.earnings_per_share > 0:
        if latest_price and latest_price.close:
            pe_ratio = latest_price.close / current.earnings_per_share

    dividend_yield = None
    if latest_price and latest_price.close and latest_price.close > 0:
        dummy_dividend = 0.0
        if current and current.profit_after_tax:
            dummy_dividend = current.profit_after_tax * 0.3 / (current.revenue or 1)
        if dummy_dividend > 0:
            dividend_yield = (dummy_dividend / latest_price.close) * 100

    market_cap = latest_price.market_cap if latest_price else None

    pb_ratio = None
    if current and current.shareholders_equity and current.shareholders_equity > 0:
        if latest_price and latest_price.market_cap:
            pb_ratio = latest_price.market_cap / current.shareholders_equity

    roe = None
    if current and current.shareholders_equity and current.shareholders_equity > 0:
        if current.profit_after_tax:
            roe = current.profit_after_tax / current.shareholders_equity

    debt_to_equity = None
    if current and current.shareholders_equity and current.shareholders_equity > 0:
        if current.total_liabilities:
            debt_to_equity = current.total_liabilities / current.shareholders_equity

    # Store in DB
    metric = ComputedMetric(
        company_id=company_id,
        computed_date=target_date,
        revenue_growth_1y=round(revenue_growth, 4) if revenue_growth else None,
        pat_growth_1y=round(pat_growth, 4) if pat_growth else None,
        pe_ratio=round(pe_ratio, 2) if pe_ratio else None,
        dividend_yield=round(dividend_yield, 4) if dividend_yield else None,
        market_cap=market_cap,
        pb_ratio=round(pb_ratio, 2) if pb_ratio else None,
        roe=round(roe, 4) if roe else None,
        debt_to_equity=round(debt_to_equity, 2) if debt_to_equity else None,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def compute_all_metrics(db: Session):
    """Compute metrics for all companies."""
    companies = db.query(Company).all()
    for c in companies:
        compute_metrics_for_company(db, c.id)
    logger.info(f"Computed metrics for {len(companies)} companies")
