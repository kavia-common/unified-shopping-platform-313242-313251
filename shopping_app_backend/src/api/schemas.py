from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, conint, constr


class Message(BaseModel):
    message: str = Field(..., description="Human readable message.")


# --------------------
# Auth
# --------------------
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.")
    password: constr(min_length=8) = Field(..., description="User password (min 8 chars).")
    full_name: Optional[str] = Field(None, description="Optional user full name.")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field("bearer", description="Token type.")


class UserResponse(BaseModel):
    id: int = Field(..., description="User id.")
    email: EmailStr = Field(..., description="User email.")
    full_name: Optional[str] = Field(None, description="User full name.")


# --------------------
# Products
# --------------------
class ProductResponse(BaseModel):
    id: int = Field(..., description="Product id.")
    name: str = Field(..., description="Product name.")
    description: Optional[str] = Field(None, description="Product description.")
    price: Decimal = Field(..., description="Unit price.")
    currency: str = Field(..., description="Currency (ISO 4217).")
    image_url: Optional[str] = Field(None, description="Optional product image URL.")
    is_active: bool = Field(..., description="Whether the product is active.")
    created_at: datetime = Field(..., description="Created timestamp.")
    updated_at: datetime = Field(..., description="Updated timestamp.")


# --------------------
# Cart
# --------------------
class CartItemUpsertRequest(BaseModel):
    product_id: int = Field(..., description="Product id to add/update in cart.")
    quantity: conint(gt=0) = Field(..., description="Quantity (> 0).")


class CartItemResponse(BaseModel):
    id: int = Field(..., description="Cart item id.")
    product: ProductResponse = Field(..., description="Product snapshot.")
    quantity: int = Field(..., description="Quantity.")
    unit_price: Decimal = Field(..., description="Unit price at time of adding to cart.")


class CartResponse(BaseModel):
    id: int = Field(..., description="Cart id.")
    status: str = Field(..., description="Cart status, usually 'active'.")
    items: List[CartItemResponse] = Field(default_factory=list, description="Cart items.")
    subtotal: Decimal = Field(..., description="Subtotal across items.")


# --------------------
# Checkout / Orders
# --------------------
class CheckoutRequest(BaseModel):
    """
    For this app, checkout uses the active cart items.
    Optionally accept an idempotency key for frontend retries.
    """

    idempotency_key: Optional[str] = Field(None, description="Optional idempotency key.")


class OrderItemResponse(BaseModel):
    id: int = Field(..., description="Order item id.")
    product: ProductResponse = Field(..., description="Purchased product.")
    quantity: int = Field(..., description="Quantity purchased.")
    unit_price: Decimal = Field(..., description="Unit price at purchase time.")
    line_total: Decimal = Field(..., description="Line total (quantity * unit_price).")


class OrderResponse(BaseModel):
    id: int = Field(..., description="Order id.")
    status: str = Field(..., description="Order status.")
    total_amount: Decimal = Field(..., description="Total order amount.")
    currency: str = Field(..., description="Currency.")
    created_at: datetime = Field(..., description="Created timestamp.")
    updated_at: datetime = Field(..., description="Updated timestamp.")
    items: List[OrderItemResponse] = Field(default_factory=list, description="Order items.")


class OrdersListResponse(BaseModel):
    orders: List[OrderResponse] = Field(..., description="List of orders.")
