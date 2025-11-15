"""
FastAPI application entry point.
Starts backend API server on port 8000.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api.routes import router
from .database import init_db

app = FastAPI(
    title="Trading Bot API",
    version="1.0.0",
    description="Paper trading bot backend for Swing Trend strategy"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await init_db()
    print("✓ Database initialized")
    print("✓ API server ready")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Trading Bot API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
