from contextlib import asynccontextmanager
import logging
import time
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (ai, admin, alerts, analytics, auth, dashboard, health, im,
                  orders, products, refresh, reviews, settings as settings_api)
from .config import settings
from .database import init_db
from .services.refresh import refresh_data

# ---- 结构化日志（可观测性基础） ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("meituan_saas")

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # 启动定时刷新数据任务
    scheduler.add_job(refresh_data, "interval", minutes=settings.refresh_interval_minutes,
                      id="refresh_data", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS：骨架阶段放宽；生产应改为具体前端域名（如 https://admin.example.com）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志 + trace_id：便于排障与链路追踪。"""
    trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1fms) trace=%s",
                request.method, request.url.path, response.status_code, elapsed_ms, trace_id)
    response.headers["X-Trace-Id"] = trace_id
    return response


# ---- 统一错误响应体（替代 FastAPI 默认 HTML/零散 JSON） ----
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": "请求参数校验失败", "detail": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "服务器内部错误"}},
    )


app.include_router(health.router, tags=["health"])
app.include_router(dashboard.router, prefix=settings.api_prefix, tags=["dashboard"])
app.include_router(orders.router, prefix=settings.api_prefix, tags=["orders"])
app.include_router(products.router, prefix=settings.api_prefix, tags=["products"])
app.include_router(reviews.router, prefix=settings.api_prefix, tags=["reviews"])
app.include_router(alerts.router, prefix=settings.api_prefix, tags=["alerts"])
app.include_router(ai.router, prefix=settings.api_prefix, tags=["ai"])
app.include_router(im.router, prefix=settings.api_prefix, tags=["im"])
app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
app.include_router(admin.router, prefix=settings.api_prefix, tags=["admin"])
app.include_router(analytics.router, prefix=settings.api_prefix, tags=["analytics"])
app.include_router(settings_api.router, prefix=settings.api_prefix, tags=["settings"])
app.include_router(refresh.router, prefix=settings.api_prefix, tags=["refresh"])
