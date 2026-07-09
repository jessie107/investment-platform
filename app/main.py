import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routes import auth, companies, screening, dashboard

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investment Research & Screening Platform",
    description="A comprehensive tool for screening and analyzing investments",
    version="0.1.0",
)

# CORS - allow everything for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers FIRST (so they take priority)
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(screening.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend SPA - catch all remaining routes
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")
index_html = os.path.join(frontend_dist, "index.html")

if os.path.exists(frontend_dist):
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve SPA for any route not handled by API."""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(index_html)
