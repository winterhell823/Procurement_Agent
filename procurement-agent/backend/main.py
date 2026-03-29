import sys
from pathlib import Path

# Make imports work reliably
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import auth, procurement, quotes, suppliers, orders, export, analytics
from config import settings
from models.base import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title = "AI Procurement Agent",
    version = "1.0.0",
    lifespan = lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(auth.router,     prefix="/auth", tags=["auth"])
app.include_router(procurement.router, prefix="/procurement", tags=["procurement"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])   

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Procurement Agent"}