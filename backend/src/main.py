"""
PartsHub - Electronic Parts Inventory Management System
Main FastAPI application entry point
"""

import os
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import all models to ensure SQLAlchemy relationships are configured
from .api.attachments import router as attachments_router
from .api.auth import router as auth_router
from .api.bom import router as bom_router
from .api.bulk_operations import router as bulk_operations_router
from .api.categories import router as categories_router

# Import API routers
from .api.components import router as components_router
from .api.integrations import router as integrations_router
from .api.kicad import router as kicad_router
from .api.location_layout import router as location_layout_router
from .api.projects import router as projects_router
from .api.providers import router as providers_router
from .api.reports import router as reports_router
from .api.resources import router as resources_router
from .api.stock_history import router as stock_history_router
from .api.stock_operations import router as stock_operations_router
from .api.storage import router as storage_router
from .api.tags import router as tags_router
from .api.wizard import router as wizard_router
from .auth.admin import ensure_admin_exists

# Import for startup events
from .database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup
    # Note: Database migrations must be run separately before starting the app
    # Run: cd backend && uv run --project .. alembic upgrade head
    #
    # Automatic migrations during app startup were removed due to SQLite connection
    # conflicts that cause migrations to hang (60+ seconds vs <1 second when run separately)

    # Configure SQLAlchemy registry to ensure all relationships are properly initialized
    from sqlalchemy.orm import configure_mappers

    try:
        configure_mappers()
    except Exception as e:
        print(f"Warning: SQLAlchemy mapper configuration issue: {e}")

    # Ensure default admin user exists (skip during tests)
    if not os.getenv("TESTING"):
        db = next(get_db())
        try:
            result = ensure_admin_exists(db)
            if result:
                user, password = result
                print("\n🔑 DEFAULT ADMIN CREATED:")
                print(f"   Username: {user.username}")
                print(f"   Password: {password}")
                print("   ⚠️  Please change this password after first login!\n")
        except Exception as e:
            print(f"Error creating default admin user: {e}")
        finally:
            db.close()

    # Optimize database with search indexes
    db = next(get_db())
    try:
        from .database.indexes import optimize_database_for_search

        results = optimize_database_for_search(db)
        if results.get("indexes_created"):
            print("📊 Database search indexes optimized for performance")
            optimized_count = sum(
                1
                for q in results.get("performance_analysis", {}).values()
                if q.get("optimized", False)
            )
            total_count = len(results.get("performance_analysis", {}))
            print(f"   {optimized_count}/{total_count} search queries optimized")
        if results.get("errors"):
            for error in results["errors"]:
                print(f"   ⚠️  {error}")
    except Exception as e:
        print(f"Warning: Database optimization failed: {e}")
    finally:
        db.close()

    yield

    # Shutdown (if needed)
    # Add any cleanup code here


# Get version from pyproject.toml
try:
    __version__ = version("partshub")
    # Ensure version is not empty
    if not __version__:
        __version__ = "0.2.1"
except Exception:
    __version__ = "0.2.1"  # Fallback version

app = FastAPI(
    title="PartsHub API",
    description="Electronic parts inventory management system",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Custom exception handler for JSON decode errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors to return 400 for JSON decode errors.

    FastAPI returns 422 by default for all validation errors, but malformed JSON
    should return 400 Bad Request per HTTP standards.
    """
    # Check if the error is due to JSON decode failure
    errors = exc.errors()
    if errors and any(
        error.get("type") == "json_invalid" or "JSON" in str(error.get("msg", ""))
        for error in errors
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid JSON in request body"},
        )

    # For other validation errors, return 422 as usual
    # Convert error objects to serializable format
    serializable_errors = []
    for error in errors:
        serializable_errors.append(
            {
                "type": error.get("type"),
                "loc": error.get("loc"),
                "msg": str(error.get("msg", "")),
                "input": str(error.get("input", "")) if "input" in error else None,
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": serializable_errors},
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
        "http://127.0.0.1:9000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(components_router)
app.include_router(storage_router)
app.include_router(location_layout_router)
app.include_router(integrations_router)
app.include_router(tags_router)
app.include_router(attachments_router)
app.include_router(kicad_router)
app.include_router(projects_router)
app.include_router(reports_router)
app.include_router(bom_router)
app.include_router(categories_router)
app.include_router(bulk_operations_router)
app.include_router(stock_operations_router)
app.include_router(stock_history_router)
app.include_router(providers_router)
app.include_router(wizard_router)
app.include_router(resources_router)


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {"message": "PartsHub API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))  # Use PORT env var, default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
