from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import ComputedMetric, Company, Exchange
from app.schemas.schemas import ScreeningCriteria
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def execute_screening(
    db: Session, criteria: ScreeningCriteria, max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Apply multi-criteria filters to all companies and return ranked results.
    Companies that match all non-null criteria are ranked by a composite score.
    """
    query = (
        db.query(ComputedMetric, Company, Exchange)
        .join(Company, ComputedMetric.company_id == Company.id)
        .join(Exchange, Company.exchange_id == Exchange.id)
    )

    # Apply criteria filters
    if criteria.revenue_growth_min is not None:
        query = query.filter(
            ComputedMetric.revenue_growth_1y >= criteria.revenue_growth_min
        )
    if criteria.revenue_growth_max is not None:
        query = query.filter(
            ComputedMetric.revenue_growth_1y <= criteria.revenue_growth_max
        )

    if criteria.pat_growth_min is not None:
        query = query.filter(
            ComputedMetric.pat_growth_1y >= criteria.pat_growth_min
        )
    if criteria.pat_growth_max is not None:
        query = query.filter(
            ComputedMetric.pat_growth_1y <= criteria.pat_growth_max
        )

    if criteria.pe_ratio_min is not None:
        query = query.filter(ComputedMetric.pe_ratio >= criteria.pe_ratio_min)
    if criteria.pe_ratio_max is not None:
        query = query.filter(ComputedMetric.pe_ratio <= criteria.pe_ratio_max)

    if criteria.dividend_yield_min is not None:
        query = query.filter(
            ComputedMetric.dividend_yield >= criteria.dividend_yield_min
        )
    if criteria.dividend_yield_max is not None:
        query = query.filter(
            ComputedMetric.dividend_yield <= criteria.dividend_yield_max
        )

    if criteria.market_cap_min is not None:
        query = query.filter(
            ComputedMetric.market_cap >= criteria.market_cap_min
        )
    if criteria.market_cap_max is not None:
        query = query.filter(
            ComputedMetric.market_cap <= criteria.market_cap_max
        )

    if criteria.exchanges:
        query = query.filter(Exchange.code.in_(criteria.exchanges))

    # Only include most recent metric per company
    subq = (
        db.query(ComputedMetric.company_id)
        .group_by(ComputedMetric.company_id)
        .subquery()
    )
    # Get latest metric for each company
    latest_metric_subq = (
        db.query(
            ComputedMetric.company_id,
            ComputedMetric.id,
        )
        .distinct(ComputedMetric.company_id)
        .order_by(
            ComputedMetric.company_id, ComputedMetric.computed_date.desc()
        )
        .subquery()
    )

    query = query.filter(
        ComputedMetric.id.in_(
            db.query(latest_metric_subq.c.id)
        )
    )

    results = query.all()

    # Compute composite score for ranking
    scored = []
    for metric, company, exchange in results:
        score = 0.0
        # PE ratio score (lower is better, target 5-20)
        if metric.pe_ratio and metric.pe_ratio > 0:
            pe_score = max(0, 100 - abs(metric.pe_ratio - 15) * 5)
            score += pe_score * 0.25

        # Revenue growth (higher is better)
        if metric.revenue_growth_1y is not None:
            rg_score = max(0, min(100, metric.revenue_growth_1y * 500))
            score += rg_score * 0.20

        # PAT growth (higher is better)
        if metric.pat_growth_1y is not None:
            pat_score = max(0, min(100, metric.pat_growth_1y * 400))
            score += pat_score * 0.20

        # ROE (higher is better)
        if metric.roe is not None:
            roe_score = max(0, min(100, metric.roe * 200))
            score += roe_score * 0.15

        # Dividend yield (higher is better, up to 8%)
        if metric.dividend_yield is not None:
            dy_score = max(0, min(100, metric.dividend_yield * 12.5))
            score += dy_score * 0.10

        # Debt-to-equity (lower is better)
        if metric.debt_to_equity is not None:
            dte_score = max(0, 100 - metric.debt_to_equity * 10)
            score += dte_score * 0.10

        scored.append(
            {
                "company_id": company.id,
                "company_name": company.name,
                "ticker": company.ticker,
                "exchange": exchange.code,
                "sector": company.sector,
                "industry": company.industry,
                "score": round(score, 2),
                "revenue_growth_1y": metric.revenue_growth_1y,
                "pat_growth_1y": metric.pat_growth_1y,
                "pe_ratio": metric.pe_ratio,
                "dividend_yield": metric.dividend_yield,
                "market_cap": metric.market_cap,
                "pb_ratio": metric.pb_ratio,
                "roe": metric.roe,
                "debt_to_equity": metric.debt_to_equity,
            }
        )

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Assign ranks
    for i, item in enumerate(scored):
        item["rank"] = i + 1

    return scored[:max_results]
