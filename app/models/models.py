import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst")
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    screening_sessions = relationship("ScreeningSession", back_populates="user")


class Exchange(Base):
    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    timezone = Column(String(100))
    currency = Column(String(10))

    companies = relationship("Company", back_populates="exchange")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    ticker = Column(String(20), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    sector = Column(String(255))
    description = Column(Text)

    exchange = relationship("Exchange", back_populates="companies")
    financial_statements = relationship("FinancialStatement", back_populates="company")
    daily_prices = relationship("DailyPrice", back_populates="company")
    computed_metrics = relationship("ComputedMetric", back_populates="company")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_type = Column(String(20), default="FY")  # FY, Q1-Q4
    fiscal_year = Column(Integer, nullable=False)
    revenue = Column(Float)
    gross_profit = Column(Float)
    operating_profit = Column(Float)
    ebitda = Column(Float)
    profit_after_tax = Column(Float)
    earnings_per_share = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    shareholders_equity = Column(Float)

    company = relationship("Company", back_populates="financial_statements")


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    market_cap = Column(Float)

    company = relationship("Company", back_populates="daily_prices")


class ComputedMetric(Base):
    __tablename__ = "computed_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    computed_date = Column(Date, nullable=False)
    revenue_growth_1y = Column(Float)
    pat_growth_1y = Column(Float)
    pe_ratio = Column(Float)
    dividend_yield = Column(Float)
    market_cap = Column(Float)
    pb_ratio = Column(Float)
    roe = Column(Float)
    debt_to_equity = Column(Float)

    company = relationship("Company", back_populates="computed_metrics")


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255))
    criteria = Column(JSON)
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="screening_sessions")
    results = relationship("ScreeningResult", back_populates="session")


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("screening_sessions.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    metrics_snapshot = Column(JSON)
    rank = Column(Integer)

    session = relationship("ScreeningSession", back_populates="results")
    company = relationship("Company")
