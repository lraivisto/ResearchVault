

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from portal.backend.app.routers import stream, graph, missions
import scripts.db as db

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

# Configure CORS for local development (React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(missions.router, prefix="/api", tags=["missions"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

