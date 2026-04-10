from app.routes.auth import router as auth_router
from app.routes.payments import router as payments_router

__all__ = ["auth_router", "payments_router"]
