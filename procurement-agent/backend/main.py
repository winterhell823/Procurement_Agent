import sys
from pathlib import Path

# Make imports work reliably
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import auth
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

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Procurement Agent"}