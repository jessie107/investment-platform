"""
Seed script to populate the database with realistic sample data.
Run: python seed.py
"""
import random
import datetime
from app.database import engine, SessionLocal, Base
from app.models.models import (
    User,
    Exchange,
    Company,
    FinancialStatement,
    DailyPrice,
    ComputedMetric,
    ScreeningSession,
    ScreeningResult,
)
from app.auth import hash_password
from app.services.metric_calculator import compute_metrics_for_company

random.seed(42)

# Create tables
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()

    # Clear existing data
    for table in [
        ScreeningResult,
        ScreeningSession,
        ComputedMetric,
        DailyPrice,
        FinancialStatement,
        Company,
        Exchange,
        User,
    ]:
        db.query(table).delete()
    db.commit()

    # ── Exchanges ──
    exchanges_data = [
        {"code": "SGX", "name": "Singapore Exchange", "country": "Singapore", "timezone": "Asia/Singapore", "currency": "SGD"},
        {"code": "NYSE", "name": "New York Stock Exchange", "country": "USA", "timezone": "America/New_York", "currency": "USD"},
        {"code": "HKEX", "name": "Hong Kong Stock Exchange", "country": "Hong Kong", "timezone": "Asia/Hong_Kong", "currency": "HKD"},
    ]
    exchanges = {}
    for e in exchanges_data:
        exchange = Exchange(**e)
        db.add(exchange)
        db.flush()
        exchanges[e["code"]] = exchange
    db.commit()

    # ── Companies ──
    companies_data = [
        # SGX
        {"ticker": "D05", "name": "DBS Group Holdings Ltd", "industry": "Banking", "sector": "Financials", "exchange": "SGX",
         "description": "DBS is a leading financial services group in Asia, with a growing presence in Greater China, Southeast Asia and South Asia."},
        {"ticker": "O39", "name": "Oversea-Chinese Banking Corp Ltd", "industry": "Banking", "sector": "Financials", "exchange": "SGX",
         "description": "OCBC is the second largest financial services group in Southeast Asia by assets."},
        {"ticker": "U11", "name": "United Overseas Bank Ltd", "industry": "Banking", "sector": "Financials", "exchange": "SGX",
         "description": "UOB is a leading bank in Asia with a global network of more than 500 offices."},
        {"ticker": "C38U", "name": "CapitaLand Integrated Commercial Trust", "industry": "REIT", "sector": "Real Estate", "exchange": "SGX",
         "description": "CICT is Singapore's largest listed REIT with a diversified portfolio of retail and office properties."},
        {"ticker": "C07", "name": "Jardine Cycle & Carriage Ltd", "industry": "Automotive", "sector": "Industrials", "exchange": "SGX",
         "description": "Jardine C&C is a Singapore-based conglomerate focused on automotive and industrial operations."},
        # NYSE
        {"ticker": "AAPL", "name": "Apple Inc.", "industry": "Consumer Electronics", "sector": "Technology", "exchange": "NYSE",
         "description": "Apple designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories."},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "industry": "Software", "sector": "Technology", "exchange": "NYSE",
         "description": "Microsoft develops and licenses software, services, devices, and solutions worldwide."},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "industry": "Internet Services", "sector": "Technology", "exchange": "NYSE",
         "description": "Alphabet is a holding company that provides web-based search, advertising, cloud, and hardware products."},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "industry": "Banking", "sector": "Financials", "exchange": "NYSE",
         "description": "JPMorgan Chase is a leading global financial services firm with assets of $3.9 trillion."},
        {"ticker": "KO", "name": "The Coca-Cola Company", "industry": "Beverages", "sector": "Consumer Staples", "exchange": "NYSE",
         "description": "Coca-Cola is a total beverage company with over 500 brands in more than 200 countries."},
        # HKEX
        {"ticker": "0700", "name": "Tencent Holdings Ltd", "industry": "Internet Services", "sector": "Technology", "exchange": "HKEX",
         "description": "Tencent is a world-leading internet and technology company with businesses in social media, gaming, fintech and cloud."},
        {"ticker": "9988", "name": "Alibaba Group Holding Ltd", "industry": "E-commerce", "sector": "Technology", "exchange": "HKEX",
         "description": "Alibaba operates e-commerce, cloud computing, digital media and innovation initiatives."},
        {"ticker": "0005", "name": "HSBC Holdings plc", "industry": "Banking", "sector": "Financials", "exchange": "HKEX",
         "description": "HSBC is one of the largest banking and financial services organizations in the world."},
        {"ticker": "1299", "name": "AIA Group Ltd", "industry": "Insurance", "sector": "Financials", "exchange": "HKEX",
         "description": "AIA is the largest independent publicly listed pan-Asian life insurance group."},
        {"ticker": "0001", "name": "CK Hutchison Holdings Ltd", "industry": "Conglomerate", "sector": "Industrials", "exchange": "HKEX",
         "description": "CK Hutchison is a multinational conglomerate with businesses in ports, retail, infrastructure, energy and telecom."},
    ]

    base_prices = {
        "D05": 35.0, "O39": 13.0, "U11": 28.0, "C38U": 2.0, "C07": 30.0,
        "AAPL": 180.0, "MSFT": 370.0, "GOOGL": 140.0, "JPM": 170.0, "KO": 60.0,
        "0700": 380.0, "9988": 180.0, "0005": 65.0, "1299": 70.0, "0001": 45.0,
    }

    # Base financials (realistic revenue in millions of base currency)
    base_financials = {
        "D05": {"revenue": 16500, "gp_margin": 0.85, "op_margin": 0.42, "pat_margin": 0.35, "eps": 3.50, "assets": 650000, "liabilities": 590000, "equity": 60000},
        "O39": {"revenue": 9500, "gp_margin": 0.82, "op_margin": 0.40, "pat_margin": 0.33, "eps": 1.80, "assets": 420000, "liabilities": 380000, "equity": 40000},
        "U11": {"revenue": 11000, "gp_margin": 0.84, "op_margin": 0.41, "pat_margin": 0.34, "eps": 2.80, "assets": 520000, "liabilities": 470000, "equity": 50000},
        "C38U": {"revenue": 1400, "gp_margin": 0.70, "op_margin": 0.55, "pat_margin": 0.45, "eps": 0.10, "assets": 21000, "liabilities": 13000, "equity": 8000},
        "C07": {"revenue": 18000, "gp_margin": 0.25, "op_margin": 0.08, "pat_margin": 0.05, "eps": 1.50, "assets": 35000, "liabilities": 20000, "equity": 15000},
        "AAPL": {"revenue": 394000, "gp_margin": 0.43, "op_margin": 0.30, "pat_margin": 0.25, "eps": 6.40, "assets": 350000, "liabilities": 280000, "equity": 70000},
        "MSFT": {"revenue": 211000, "gp_margin": 0.70, "op_margin": 0.42, "pat_margin": 0.35, "eps": 11.00, "assets": 411000, "liabilities": 190000, "equity": 221000},
        "GOOGL": {"revenue": 307000, "gp_margin": 0.56, "op_margin": 0.27, "pat_margin": 0.22, "eps": 5.80, "assets": 395000, "liabilities": 115000, "equity": 280000},
        "JPM": {"revenue": 158000, "gp_margin": 0.65, "op_margin": 0.35, "pat_margin": 0.28, "eps": 14.50, "assets": 3900000, "liabilities": 3500000, "equity": 320000},
        "KO": {"revenue": 46000, "gp_margin": 0.60, "op_margin": 0.27, "pat_margin": 0.22, "eps": 2.50, "assets": 98000, "liabilities": 74000, "equity": 24000},
        "0700": {"revenue": 600000, "gp_margin": 0.47, "op_margin": 0.28, "pat_margin": 0.22, "eps": 17.50, "assets": 1800000, "liabilities": 780000, "equity": 1020000},
        "9988": {"revenue": 870000, "gp_margin": 0.38, "op_margin": 0.10, "pat_margin": 0.08, "eps": 7.50, "assets": 1800000, "liabilities": 750000, "equity": 1050000},
        "0005": {"revenue": 50000, "gp_margin": 0.60, "op_margin": 0.30, "pat_margin": 0.24, "eps": 1.20, "assets": 3000000, "liabilities": 2750000, "equity": 250000},
        "1299": {"revenue": 19000, "gp_margin": 0.55, "op_margin": 0.25, "pat_margin": 0.20, "eps": 0.70, "assets": 320000, "liabilities": 270000, "equity": 50000},
        "0001": {"revenue": 280000, "gp_margin": 0.35, "op_margin": 0.12, "pat_margin": 0.08, "eps": 4.50, "assets": 1200000, "liabilities": 800000, "equity": 400000},
    }

    companies = {}
    for c in companies_data:
        company = Company(
            exchange_id=exchanges[c["exchange"]].id,
            ticker=c["ticker"],
            name=c["name"],
            industry=c["industry"],
            sector=c["sector"],
            description=c["description"],
        )
        db.add(company)
        db.flush()
        companies[c["ticker"]] = company
    db.commit()

    # ── Financial Statements (5 years) ──
    current_year = datetime.date.today().year
    for ticker, fin_data in base_financials.items():
        company = companies[ticker]
        for year_offset in range(5):
            fy = current_year - year_offset
            # Add growth/decline trend: recent years better
            year_factor = 1.0 + (2 - year_offset) * 0.05  # growth trend
            random_factor = 1.0 + random.uniform(-0.05, 0.05)
            rf = year_factor * random_factor

            revenue = round(fin_data["revenue"] * rf, 2)
            gross_profit = round(revenue * fin_data["gp_margin"] * (1 + random.uniform(-0.03, 0.03)), 2)
            operating_profit = round(revenue * fin_data["op_margin"] * (1 + random.uniform(-0.04, 0.04)), 2)
            ebitda = round(operating_profit * (1 + random.uniform(0.1, 0.2)), 2)
            profit_after_tax = round(revenue * fin_data["pat_margin"] * (1 + random.uniform(-0.05, 0.05)), 2)
            eps = round(fin_data["eps"] * rf * (1 + random.uniform(-0.03, 0.03)), 2)
            assets = round(fin_data["assets"] * (1 + year_offset * 0.02) * (1 + random.uniform(-0.01, 0.01)), 2)
            liabilities = round(fin_data["liabilities"] * (1 + year_offset * 0.02) * (1 + random.uniform(-0.01, 0.01)), 2)
            equity = round(fin_data["equity"] * (1 + year_offset * 0.03) * (1 + random.uniform(-0.01, 0.01)), 2)

            statement = FinancialStatement(
                company_id=company.id,
                period_type="FY",
                fiscal_year=fy,
                revenue=revenue,
                gross_profit=gross_profit,
                operating_profit=operating_profit,
                ebitda=ebitda,
                profit_after_tax=profit_after_tax,
                earnings_per_share=eps,
                total_assets=assets,
                total_liabilities=liabilities,
                shareholders_equity=equity,
            )
            db.add(statement)
    db.commit()

    # ── Daily Prices (~252 trading days per year, 3 years) ──
    for ticker, base_price in base_prices.items():
        company = companies[ticker]
        price = base_price
        for year_offset in range(3):
            fy = current_year - year_offset
            num_days = 252 if year_offset == 0 else 252
            for day in range(num_days, 0, -1):
                trade_date = datetime.date(fy, 1, 1) + datetime.timedelta(days=250 - day)
                if trade_date > datetime.date.today():
                    continue

                # Simulate price movement
                daily_change = random.gauss(0.0003, 0.015)
                price = price * (1 + daily_change)

                vol_mult = random.uniform(0.3, 0.8) if ticker in ["D05", "O39", "U11", "C38U", "C07"] else random.uniform(0.5, 1.5)
                volume = int(base_price * 100000 * vol_mult * (1 + random.uniform(-0.3, 0.3)))

                close = round(price, 2)
                open_price = round(close * (1 + random.gauss(0, 0.005)), 2)
                high = round(max(open_price, close) * (1 + random.uniform(0, 0.02)), 2)
                low = round(min(open_price, close) * (1 - random.uniform(0, 0.02)), 2)

                # Market cap
                if ticker == "D05":
                    shares_outstanding_m = 2800
                elif ticker == "O39":
                    shares_outstanding_m = 4400
                elif ticker == "U11":
                    shares_outstanding_m = 1700
                elif ticker == "C38U":
                    shares_outstanding_m = 7500
                elif ticker == "C07":
                    shares_outstanding_m = 400
                elif ticker == "AAPL":
                    shares_outstanding_m = 15500
                elif ticker == "MSFT":
                    shares_outstanding_m = 7500
                elif ticker == "GOOGL":
                    shares_outstanding_m = 12600
                elif ticker == "JPM":
                    shares_outstanding_m = 2900
                elif ticker == "KO":
                    shares_outstanding_m = 4300
                elif ticker == "0700":
                    shares_outstanding_m = 9600
                elif ticker == "9988":
                    shares_outstanding_m = 20000
                elif ticker == "0005":
                    shares_outstanding_m = 19500
                elif ticker == "1299":
                    shares_outstanding_m = 12000
                elif ticker == "0001":
                    shares_outstanding_m = 3800
                else:
                    shares_outstanding_m = 1000

                market_cap = round(close * shares_outstanding_m * 1000000, 2)

                daily_price = DailyPrice(
                    company_id=company.id,
                    trade_date=trade_date,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    market_cap=market_cap,
                )
                db.add(daily_price)
        db.commit()
    print("✅ Prices seeded")

    # ── Computed Metrics ──
    for ticker, company in companies.items():
        metric = compute_metrics_for_company(db, company.id)
        print(f"  Metrics computed for {ticker}: PE={metric.pe_ratio}, RevGr={metric.revenue_growth_1y}")
    print("✅ Metrics computed")

    # ── User (demo) ──
    demo_user = User(
        email="demo@invest.com",
        full_name="Demo Analyst",
        role="analyst",
        password_hash=hash_password("demo123"),
    )
    db.add(demo_user)
    db.commit()

    # ── Sample Screening Session ──
    sample_session = ScreeningSession(
        user_id=demo_user.id,
        name="Top Tech Growth Stocks",
        criteria={
            "revenue_growth_min": 0.05,
            "pat_growth_min": 0.05,
            "pe_ratio_max": 35,
            "exchanges": ["SGX", "NYSE", "HKEX"],
        },
        result_count=5,
    )
    db.add(sample_session)
    db.commit()

    print("\n🎉 Seed completed!")
    print(f"   Exchanges: {len(exchanges_data)}")
    print(f"   Companies: {len(companies_data)}")
    print(f"   User: demo@invest.com / demo123")

    db.close()


if __name__ == "__main__":
    seed()
