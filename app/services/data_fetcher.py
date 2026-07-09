"""
Real-time data fetcher using Yahoo Finance (yfinance).
Pulls live stock prices and financial data.
Replaces old seed data with real data.
"""
import yfinance as yf
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import Company, Exchange, DailyPrice, FinancialStatement, ComputedMetric

logger = logging.getLogger(__name__)

# Yahoo Finance ticker suffixes per exchange
TICKER_SUFFIXES = {
    "SGX": ".SI",
    "NYSE": "",
    "NASDAQ": "",
    "HKEX": ".HK",
}

# Override mappings for non-standard tickers
TICKER_MAP = {
    "D05": "D05.SI",      # DBS
    "O39": "O39.SI",      # OCBC
    "U11": "U11.SI",      # UOB
    "AAPL": "AAPL",       # Apple
    "MSFT": "MSFT",       # Microsoft
    "GOOGL": "GOOGL",     # Google
    "TSM": "TSM",         # TSMC
    "TCEHY": "TCEHY",     # Tencent
    "BABA": "BABA",       # Alibaba
    "SSNLF": "SSNLF",     # Samsung
    "TM": "TM",           # Toyota
    "NSRGY": "NSRGY",     # Nestlé
    "SHEL": "SHEL",       # Shell
    "AMZN": "AMZN",       # Amazon
    "META": "META",       # Meta
}


def get_yahoo_ticker(company: Company) -> str:
    """Get the correct Yahoo Finance ticker for a company."""
    if company.ticker in TICKER_MAP:
        return TICKER_MAP[company.ticker]
    
    exchange_code = company.exchange.code if company.exchange else ""
    suffix = TICKER_SUFFIXES.get(exchange_code, "")
    return company.ticker + suffix


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
    """Fetch annual financial statements from Yahoo Finance (last 5 years)."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        
        if financials is None or financials.empty:
            logger.warning(f"No financial data for {ticker}")
            return None
        
        result = {}
        for year_col in financials.columns[:5]:
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
                    result[year]["total_assets"] = _safe_float(
                        balance_sheet.loc["Total Assets", year_col]
                    ) if "Total Assets" in balance_sheet.index else None
                    result[year]["total_liabilities"] = _safe_float(
                        balance_sheet.loc["Total Liabilities Net Minority Interest", year_col]
                    ) if "Total Liabilities Net Minority Interest" in balance_sheet.index else None
                    result[year]["shareholders_equity"] = _safe_float(
                        balance_sheet.loc["Stockholders Equity", year_col]
                    ) if "Stockholders Equity" in balance_sheet.index else None
                except:
                    pass
        
        return result
    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {e}")
        return None


def update_company_data(db: Session, company: Company):
    """
    Replace company data with real Yahoo Finance data.
    Deletes old seed data and inserts live data.
    """
    ticker = get_yahoo_ticker(company)
    logger.info(f"Fetching real data for {company.name} ({ticker})...")
    
    # Fetch price
    price_data = fetch_live_price(ticker)
    if price_data and price_data["close"]:
        # Delete old prices for this company
        db.query(DailyPrice).filter(DailyPrice.company_id == company.id).delete()
        db.flush()
        
        # Insert a few days of price history
        today = date.today()
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
        logger.info(f"  ✅ Price: ${price_data['close']} (market cap: ${price_data.get('market_cap', 'N/A')})")
    
    # Fetch financials and REPLACE old seed data
    fin_data = fetch_financials(ticker)
    if fin_data:
        # Delete old financials
        db.query(FinancialStatement).filter(
            FinancialStatement.company_id == company.id
        ).delete()
        db.flush()
        
        for year, data in fin_data.items():
            if data.get("revenue") is not None:
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
        
        fin_years = [y for y, d in fin_data.items() if d.get("revenue")]
        logger.info(f"  ✅ Financials: {len(fin_years)} years ({', '.join(str(y) for y in fin_years)})")
    else:
        logger.warning(f"  ⚠️ No financial data for {ticker}")
    
    # Delete old computed metrics so they get recalculated
    db.query(ComputedMetric).filter(
        ComputedMetric.company_id == company.id
    ).delete()
    
    db.commit()


def update_all_companies(db: Session):
    """Replace ALL company data with real data from Yahoo Finance."""
    companies = db.query(Company).all()
    success = 0
    for company in companies:
        try:
            update_company_data(db, company)
            success += 1
        except Exception as e:
            logger.error(f"❌ Failed to update {company.ticker}: {e}")
            db.rollback()
    
    # Recalculate metrics for all companies
    from app.services.metric_calculator import compute_all_metrics
    compute_all_metrics(db)
    
    logger.info(f"✅ Data update complete — {success}/{len(companies)} companies updated with real data")


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
