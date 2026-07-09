"""
Real-time data fetcher using Yahoo Finance (yfinance).
Pulls live stock prices and financial data.
"""
import yfinance as yf
import logging
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import Company, Exchange, DailyPrice, FinancialStatement, ComputedMetric

logger = logging.getLogger(__name__)


def fetch_live_price(ticker: str) -> Optional[dict]:
    """Fetch current price and market data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get latest price
        hist = stock.history(period="5d")
        if hist.empty:
            logger.warning(f"No price data for {ticker}")
            return None
        
        latest = hist.iloc[-1]
        
        return {
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "eps": info.get("trailingEps"),
            "book_value": info.get("bookValue"),
            "shares_outstanding": info.get("sharesOutstanding"),
        }
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None


def fetch_financials(ticker: str) -> Optional[dict]:
    """Fetch annual financial statements from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        
        if financials is None or financials.empty:
            logger.warning(f"No financial data for {ticker}")
            return None
        
        result = {}
        for year_col in financials.columns[:5]:  # Last 5 years
            year = year_col.year
            try:
                result[year] = {
                    "revenue": _safe_float(financials.loc["Total Revenue", year_col]) if "Total Revenue" in financials.index else None,
                    "gross_profit": _safe_float(financials.loc["Gross Profit", year_col]) if "Gross Profit" in financials.index else None,
                    "operating_profit": _safe_float(financials.loc["Operating Income", year_col]) if "Operating Income" in financials.index else None,
                    "ebitda": _safe_float(financials.loc["EBITDA", year_col]) if "EBITDA" in financials.index else None,
                    "profit_after_tax": _safe_float(financials.loc["Net Income", year_col]) if "Net Income" in financials.index else None,
                    "eps": _safe_float(financials.loc["Diluted EPS", year_col]) if "Diluted EPS" in financials.index else None,
                }
            except (KeyError, TypeError):
                result[year] = {"revenue": None, "profit_after_tax": None}
        
        # Add balance sheet data
        if balance_sheet is not None and not balance_sheet.empty:
            for year_col in balance_sheet.columns[:5]:
                year = year_col.year
                if year not in result:
                    result[year] = {}
                try:
                    result[year]["total_assets"] = _safe_float(balance_sheet.loc["Total Assets", year_col]) if "Total Assets" in balance_sheet.index else None
                    result[year]["total_liabilities"] = _safe_float(balance_sheet.loc["Total Liabilities Net Minority Interest", year_col]) if "Total Liabilities Net Minority Interest" in balance_sheet.index else None
                    result[year]["shareholders_equity"] = _safe_float(balance_sheet.loc["Stockholders Equity", year_col]) if "Stockholders Equity" in balance_sheet.index else None
                except:
                    pass
        
        return result
    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {e}")
        return None


def update_company_data(db: Session, company: Company, ticker_yahoo: str = None):
    """
    Update a company's daily price and financial data from Yahoo Finance.
    """
    ticker = ticker_yahoo or company.ticker
    if company.exchange and company.exchange.code == "SGX":
        ticker = f"{ticker}.SI"  # Singapore suffix for Yahoo Finance
    
    # Fetch price
    price_data = fetch_live_price(ticker)
    if price_data:
        # Save daily price
        today = date.today()
        existing = db.query(DailyPrice).filter(
            DailyPrice.company_id == company.id,
            DailyPrice.trade_date == today
        ).first()
        
        if not existing:
            dp = DailyPrice(
                company_id=company.id,
                trade_date=today,
                open=price_data["open"],
                high=price_data["high"],
                low=price_data["low"],
                close=price_data["close"],
                volume=price_data["volume"],
                market_cap=price_data["market_cap"],
            )
            db.add(dp)
            db.commit()
            logger.info(f"Updated price for {ticker}: ${price_data['close']}")
    
    # Fetch financials (only if no data yet)
    existing_fin = db.query(FinancialStatement).filter(
        FinancialStatement.company_id == company.id
    ).first()
    
    if not existing_fin:
        fin_data = fetch_financials(ticker)
        if fin_data:
            for year, data in fin_data.items():
                fs = FinancialStatement(
                    company_id=company.id,
                    period_type="FY",
                    fiscal_year=year,
                    revenue=data.get("revenue"),
                    gross_profit=data.get("gross_profit"),
                    operating_profit=data.get("operating_profit"),
                    ebitda=data.get("ebitda"),
                    profit_after_tax=data.get("profit_after_tax"),
                    earnings_per_share=data.get("eps"),
                    total_assets=data.get("total_assets"),
                    total_liabilities=data.get("total_liabilities"),
                    shareholders_equity=data.get("shareholders_equity"),
                )
                db.add(fs)
            db.commit()
            logger.info(f"Updated financials for {ticker}")


def update_all_companies(db: Session):
    """Update data for all companies from Yahoo Finance."""
    companies = db.query(Company).all()
    for company in companies:
        try:
            update_company_data(db, company)
        except Exception as e:
            logger.error(f"Failed to update {company.ticker}: {e}")
    logger.info(f"Data update complete for {len(companies)} companies")


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        result = float(val)
        if result != result:  # NaN check
            return None
        return result
    except (ValueError, TypeError):
        return None
