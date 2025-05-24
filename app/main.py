import asyncio
import os
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
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
    secret_key=settings.SECRET_KEY,  # 使用配置中的密钥
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
    
    # Admin user authentication is handled via configuration (.env) when AUTH_STORAGE is 'memory'.

@app.on_event("shutdown")
async def shutdown():
    # Close any resources
    pass

# 检查用户是否已登录
def is_user_logged_in(request: Request) -> bool:
    """检查用户是否已登录"""
    user_session = request.session.get("user")
    return user_session is not None and "username" in user_session

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 如果用户未登录，重定向到登录页面；否则重定向到控制台"""
    if is_user_logged_in(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    if is_user_logged_in(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """控制台页面 - 需要用户登录"""
    if not is_user_logged_in(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    user = request.session.get("user", {})
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/books", response_class=HTMLResponse)
async def books_page(request: Request):
    """书籍管理页面 - 需要用户登录"""
    if not is_user_logged_in(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    user = request.session.get("user", {})
    return templates.TemplateResponse("books.html", {"request": request, "user": user})

@app.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request):
    """设备管理页面 - 需要用户登录"""
    if not is_user_logged_in(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    user = request.session.get("user", {})
    return templates.TemplateResponse("devices.html", {"request": request, "user": user})

@app.get("/healthcheck")
async def healthcheck():
    """健康检查"""
    return {"status": "ok"} 