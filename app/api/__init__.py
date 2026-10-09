from app.api.health      import router as health_router
from app.api.cv_routes   import router as cv_router
from app.api.query_routes import router as query_router

__all__ = ["health_router", "cv_router", "query_router"]
