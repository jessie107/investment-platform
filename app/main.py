import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routes import auth, companies, screening, dashboard

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investment Research & Screening Platform",
    description="A comprehensive tool for screening and analyzing investments",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(screening.router)
app.include_router(dashboard.router)

# Serve frontend static files
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}
