from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import auth, prcurement, quotes, suppliers
from config import settings
from models.base import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title = "AI Procurement Agent",
    version = "1.0.0";
    lifespan = lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(auth.router,     prefix="/auth", tags=["auth"])
app.include_router(prcurement.router, prefix="/procurement", tags=["procurement"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Procurement Agent"}