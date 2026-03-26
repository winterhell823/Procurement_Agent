import sys
from pathlib import Path

# Make imports work reliably
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
<<<<<<< HEAD
from routes import auth, procurement, quotes, suppliers, orders, export, analytics
=======
from routes import auth
>>>>>>> 8972cb8903ce977fd6064489ffb17c4acdff5c6b
from config import settings
from models.base import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    #await init_db()
    yield

app = FastAPI(
    title = "AI Procurement Agent",
    version = "1.0.0",
    lifespan = lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

<<<<<<< HEAD
app.include_router(auth.router,     prefix="/auth", tags=["auth"])
app.include_router(procurement.router, prefix="/procurement", tags=["procurement"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])   
=======
app.include_router(auth.router, prefix="/auth", tags=["auth"])
>>>>>>> 8972cb8903ce977fd6064489ffb17c4acdff5c6b

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Procurement Agent"}