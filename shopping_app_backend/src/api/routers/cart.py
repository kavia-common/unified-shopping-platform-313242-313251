from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.db.models import Cart
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.schemas import CartItemResponse, CartItemUpsertRequest, CartResponse, ProductResponse
from src.api.services import clear_cart, get_cart, remove_cart_item, upsert_cart_item

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_to_response(cart: Cart) -> CartResponse:
    subtotal = Decimal("0.00")
    items: list[CartItemResponse] = []
    for ci in cart.items:
        subtotal += Decimal(ci.quantity) * ci.unit_price
        items.append(
            CartItemResponse(
                id=ci.id,
                product=ProductResponse.model_validate(ci.product, from_attributes=True),
                quantity=ci.quantity,
                unit_price=ci.unit_price,
            )
        )
    return CartResponse(id=cart.id, status=cart.status, items=items, subtotal=subtotal.quantize(Decimal("0.01")))


@router.get(
    "",
    response_model=CartResponse,
    summary="Get current cart",
    description="Returns the authenticated user's active cart (created if missing).",
    operation_id="cart_get",
)
def cart_get(db: Session = Depends(get_db), user=Depends(get_current_user)) -> CartResponse:
    cart = get_cart(db, user_id=user.id)
    return _cart_to_response(cart)


@router.post(
    "/items",
    response_model=CartResponse,
    summary="Add/update cart item",
    description="Upserts a cart item for the authenticated user's active cart.",
    operation_id="cart_upsert_item",
)
def cart_upsert_item(payload: CartItemUpsertRequest, db: Session = Depends(get_db), user=Depends(get_current_user)) -> CartResponse:
    cart = upsert_cart_item(db, user_id=user.id, product_id=payload.product_id, quantity=payload.quantity)
    return _cart_to_response(cart)


@router.delete(
    "/items/{cart_item_id}",
    response_model=CartResponse,
    summary="Remove cart item",
    description="Removes an item from the authenticated user's active cart.",
    operation_id="cart_remove_item",
)
def cart_remove_item(cart_item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> CartResponse:
    cart = remove_cart_item(db, user_id=user.id, cart_item_id=cart_item_id)
    return _cart_to_response(cart)


@router.delete(
    "",
    response_model=CartResponse,
    summary="Clear cart",
    description="Clears all items from the authenticated user's active cart.",
    operation_id="cart_clear",
)
def cart_clear(db: Session = Depends(get_db), user=Depends(get_current_user)) -> CartResponse:
    cart = clear_cart(db, user_id=user.id)
    return _cart_to_response(cart)
