# InvestScreen - Investment Research & Screening Platform

A comprehensive MVP for screening and analyzing investments across multiple exchanges (SGX, NYSE, HKEX).

## Quick Start

### Option 1: Local Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev
```

### Option 2: Docker
```bash
docker-compose up --build
```

## Access

- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Demo Credentials
- Email: `demo@invest.com`
- Password: `demo123`

## Features

- **Authentication** - JWT-based login system
- **Dashboard** - Stats overview and recent sessions
- **Stock Screening** - Multi-criteria filtering with composite scoring
- **Company Details** - Financial history, price charts, key metrics
- **CSV Export** - Download screening results

## Tech Stack

- **Backend:** Python FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 18, TypeScript, Tailwind CSS, Recharts
- **Auth:** JWT (python-jose + passlib)
