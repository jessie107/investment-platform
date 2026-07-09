from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# Auth
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


# Exchange
class ExchangeResponse(BaseModel):
    id: int
    code: str
    name: str
    country: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


# Company
class CompanyResponse(BaseModel):
    id: int
    ticker: str
    name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    exchange_id: int
    exchange: Optional[ExchangeResponse] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CompanyResponse]


# Financial Statement
class FinancialStatementResponse(BaseModel):
    id: int
    period_type: str
    fiscal_year: int
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_profit: Optional[float] = None
    ebitda: Optional[float] = None
    profit_after_tax: Optional[float] = None
    earnings_per_share: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None

    class Config:
        from_attributes = True


# Daily Price
class DailyPriceResponse(BaseModel):
    id: int
    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None

    class Config:
        from_attributes = True


# Computed Metric
class ComputedMetricResponse(BaseModel):
    id: int
    computed_date: date
    revenue_growth_1y: Optional[float] = None
    pat_growth_1y: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None

    class Config:
        from_attributes = True


# Screening
class ScreeningCriteria(BaseModel):
    revenue_growth_min: Optional[float] = None
    revenue_growth_max: Optional[float] = None
    pat_growth_min: Optional[float] = None
    pat_growth_max: Optional[float] = None
    pe_ratio_min: Optional[float] = None
    pe_ratio_max: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    dividend_yield_max: Optional[float] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    exchanges: Optional[List[str]] = None


class ScreeningRequest(BaseModel):
    name: Optional[str] = "Screening Results"
    criteria: ScreeningCriteria


class ScreeningResultResponse(BaseModel):
    rank: int
    company_id: int
    company: Optional[CompanyResponse] = None
    metrics_snapshot: Optional[dict] = None

    class Config:
        from_attributes = True


class ScreeningSessionResponse(BaseModel):
    id: int
    name: str
    criteria: Optional[dict] = None
    result_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScreeningSessionDetailResponse(BaseModel):
    id: int
    name: str
    criteria: Optional[dict] = None
    result_count: int
    created_at: datetime
    results: List[ScreeningResultResponse]

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_companies: int
    total_exchanges: int
    latest_screen_results: int
