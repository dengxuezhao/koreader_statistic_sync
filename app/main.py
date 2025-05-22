import asyncio
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings, get_settings
from app.database import Base, engine
from app.dependencies import (
    get_auth_service, 
    get_book_shelf, 
    get_progress_sync,
    get_reading_stats
)
from app.api.v1 import api_router
from app.api.webdav import router as webdav_router
from app.api.opds import router as opds_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
)

# Add session middleware for authentication
app.add_middleware(
    SessionMiddleware, 
    secret_key="kompanion_secret_key",  # In production, use a proper secret key
    max_age=86400  # 1 day
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join("app", "web", "static")), name="static")

# Initialize template engine
templates = Jinja2Templates(directory=os.path.join("app", "web", "templates"))

# Include API routes
app.include_router(api_router)
app.include_router(webdav_router)
app.include_router(opds_router)

@app.on_event("startup")
async def startup():
    # Create database tables if they don't exist
    async with engine.begin() as conn:
        # This would be handled by Alembic in production
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize auth service with admin user will be done later

@app.on_event("shutdown")
async def shutdown():
    # Close any resources
    pass

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/healthcheck")
async def healthcheck():
    """健康检查"""
    return {"status": "ok"} 