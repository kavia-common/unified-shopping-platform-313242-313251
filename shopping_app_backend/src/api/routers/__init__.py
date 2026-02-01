from src.api.routers.auth import router as auth_router
from src.api.routers.cart import router as cart_router
from src.api.routers.orders import router as orders_router
from src.api.routers.products import router as products_router

__all__ = ["auth_router", "products_router", "cart_router", "orders_router"]
