from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import init_db
from routes import farmers, collections, production, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # runs once on startup
    yield


app = FastAPI(title="Farmer Carbon Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(farmers.router,     prefix="/api/farmers",     tags=["Farmers"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections"])
app.include_router(production.router,  prefix="/api/production",  tags=["Production"])
app.include_router(dashboard.router,   prefix="/api/dashboard",   tags=["Dashboard"])

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")