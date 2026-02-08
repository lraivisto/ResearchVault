

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from portal.backend.app.routers import graph, missions, stream

import scripts.db as db


def _cors_origins_from_env() -> list[str]:
    raw = os.getenv(
        "RESEARCHVAULT_PORTAL_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB is migrated
    try:
        db.init_db()
        print("Database initialized and migrated.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    yield


app = FastAPI(title="ResearchVault Portal", lifespan=lifespan)

# Configurable CORS (dev default is Vite localhost).
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(missions.router, prefix="/api", tags=["missions"])


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
