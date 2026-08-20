from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request

from database import engine
import models
from routers import auth, cookies, orders, analytics

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("bakeflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield  # <-- Обязательно для lifespan!


app = FastAPI(title="BakeFlow API", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | "
        f"Time: {process_time:.2f}ms"
    )
    return response


# Подключаем роутеры ровно один раз
app.include_router(auth.router)
app.include_router(cookies.router)
app.include_router(orders.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {"status": "working", "project": "BakeFlow"}