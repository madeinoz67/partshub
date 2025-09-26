"""
PartsHub - Electronic Parts Inventory Management System
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import for startup events
from .database import get_db
from .auth.admin import ensure_admin_exists

# Import all models to ensure SQLAlchemy relationships are configured
from . import models

# Import API routers
from .api.components import router as components_router
from .api.storage import router as storage_router
from .api.integrations import router as integrations_router
from .api.tags import router as tags_router
from .api.auth import router as auth_router
from .api.attachments import router as attachments_router
from .api.kicad import router as kicad_router
from .api.projects import router as projects_router
from .api.reports import router as reports_router
from .api.bom import router as bom_router

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
        "http://localhost:9000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:9000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(components_router)
app.include_router(storage_router)
app.include_router(integrations_router)
app.include_router(tags_router)
app.include_router(attachments_router)
app.include_router(kicad_router)
app.include_router(projects_router)
app.include_router(reports_router)
app.include_router(bom_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Configure SQLAlchemy registry to ensure all relationships are properly initialized
    from sqlalchemy.orm import configure_mappers
    try:
        configure_mappers()
    except Exception as e:
        print(f"Warning: SQLAlchemy mapper configuration issue: {e}")

    # Ensure default admin user exists
    db = next(get_db())
    try:
        result = ensure_admin_exists(db)
        if result:
            user, password = result
            print(f"\n🔑 DEFAULT ADMIN CREATED:")
            print(f"   Username: {user.username}")
            print(f"   Password: {password}")
            print(f"   ⚠️  Please change this password after first login!\n")
    except Exception as e:
        print(f"Error creating default admin user: {e}")
    finally:
        db.close()


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