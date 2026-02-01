from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.routers import auth_router, cart_router, orders_router, products_router

openapi_tags = [
    {"name": "auth", "description": "User registration and login (JWT)."},
    {"name": "products", "description": "Browse products."},
    {"name": "cart", "description": "Manage the authenticated user's cart."},
    {"name": "orders", "description": "Checkout and view orders."},
]

settings = get_settings()

app = FastAPI(
    title="Shopping App Backend API",
    description="Backend API for a fullstack shopping app: auth, products, cart, checkout, orders.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health Check", operation_id="health_check")
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
