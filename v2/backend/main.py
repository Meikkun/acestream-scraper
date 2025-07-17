from fastapi import Request, Response, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.config.database import get_db
from app.services.playlist_service import PlaylistService
"""
Main application entry point for Acestream Scraper v2 backend
"""
import os
import uvicorn
from fastapi import FastAPI, Request, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.api import api_router
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.services.task_service import task_service
from app.tasks.epg_refresh_task import run_epg_refresh_task
from app.tasks.url_scraping_task import run_url_scraping_task
from app.tasks.channel_cleanup_task import run_channel_cleanup_task
from app.tasks.channel_status_task import run_channel_status_task

# Setup logging before anything else
setup_logging()
import logging
logging.getLogger().warning("[MAIN] Root logger active at startup")

# Initialize database on startup
def initialize_database():
    """Initialize database with migration check"""
    try:
        from migrate_database import DatabaseMigrator
        migrator = DatabaseMigrator()

        # Only run migration if acestream.db exists and hasn't been migrated yet
        if migrator.should_migrate():
            print("Found v1 database, running migration...")
            migrated = migrator.run_migration()
            if migrated:
                print("Migration completed successfully!")
            return

        # Check if v2 database exists, create if not
        if not os.path.exists(migrator.v2_db_path):
            print("Creating fresh v2 database...")
            from app.config.database import engine, Base
            Base.metadata.create_all(bind=engine)
            print("Fresh v2 database created!")
        else:
            print("V2 database ready")

    except Exception as e:
        print(f"Database initialization error: {e}")
        # Create empty database if everything fails
        try:
            from app.config.database import engine, Base
            print("Creating emergency fresh database...")
            Base.metadata.create_all(bind=engine)
        except Exception as e2:
            print(f"Emergency database creation failed: {e2}")

# Initialize database
initialize_database()

app = FastAPI(
    title="Acestream Scraper API",
    description="API for scraping and managing Acestream channels",
    version="2.0.0",
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes with versioning
app.include_router(api_router, prefix="/api/v1")

# Status router for background tasks
status_router = APIRouter()

@status_router.get("/api/v1/background-tasks/status")
def get_background_tasks_status():
    jobs = task_service.get_jobs()
    return [{
        "id": job.id,
        "next_run_time": str(job.next_run_time),
        "trigger": str(job.trigger)
    } for job in jobs]

app.include_router(status_router)

# Static files serving
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.FRONTEND_BUILD_PATH)
os.makedirs(frontend_dir, exist_ok=True)  # Ensure directory exists

# Check what static directories exist in the frontend build
static_dirs = []
for dirname in ["static", "assets"]:
    if os.path.isdir(os.path.join(frontend_dir, dirname)):
        static_dirs.append(dirname)

# Mount static files directories that exist
for dirname in static_dirs:
    app.mount(f"/{dirname}", StaticFiles(directory=os.path.join(frontend_dir, dirname)), name=dirname)

# Public playlist route for user-friendly URLs (no /api prefix)
@app.get("/playlists/m3u", response_class=PlainTextResponse)
async def public_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Public route for M3U playlist (no /api prefix)
    """
    playlist_service = PlaylistService(db)
    try:
        include_groups_list = include_groups.split(",") if include_groups else None
        exclude_groups_list = exclude_groups.split(",") if exclude_groups else None
        m3u_content = await playlist_service.generate_playlist(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups_list,
            exclude_groups=exclude_groups_list,
            base_url=base_url,
            format=format
        )
        headers = {"Content-Disposition": "attachment; filename=playlist.m3u"}
        return PlainTextResponse(m3u_content, headers=headers)
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n#EXTINF:-1,Error: {str(e)}\n", status_code=500)

# Serve React app - handle all other routes to support client-side routing
@app.exception_handler(StarletteHTTPException)
async def spa_server(request: Request, exc: StarletteHTTPException):
    """Serve SPA for all non-API routes."""
    # Only handle 404s for non-API routes (client-side routing)
    if exc.status_code == 404 and not request.url.path.startswith("/api"):
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    # For API routes or other status codes, return the exception as an HTTP response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the React frontend index page."""
    try:
        with open(os.path.join(frontend_dir, "index.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # If frontend build doesn't exist yet, return a placeholder
        return HTMLResponse(content="<html><body><h1>Acestream Scraper</h1><p>Frontend not built yet. Please run 'npm run build' in the frontend directory.</p></body></html>")

@app.on_event("startup")
def start_background_tasks():
    # Start the background scheduler
    task_service.start()
    # Schedule periodic tasks (intervals in seconds)
    task_service.add_interval_task(run_epg_refresh_task, seconds=3600, job_id="epg_refresh")  # every hour
    task_service.add_interval_task(run_url_scraping_task, seconds=900, job_id="url_scraping")  # every 15 min
    task_service.add_interval_task(run_channel_cleanup_task, seconds=86400, job_id="channel_cleanup")  # daily
    task_service.add_interval_task(run_channel_status_task, seconds=600, job_id="channel_status")  # every 10 min

@app.on_event("shutdown")
def shutdown_background_tasks():
    task_service.shutdown()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
