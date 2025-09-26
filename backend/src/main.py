"""
PartsHub - Electronic Parts Inventory Management System
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from .api.components import router as components_router
from .api.storage import router as storage_router
from .api.integrations import router as integrations_router
from .api.tags import router as tags_router

app = FastAPI(
    title="PartsHub API",
    description="Electronic parts inventory management system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(components_router)
app.include_router(storage_router)
app.include_router(integrations_router)
app.include_router(tags_router)


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "PartsHub API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)