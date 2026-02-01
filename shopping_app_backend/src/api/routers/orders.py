from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.db.models import Order
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.schemas import CheckoutRequest, OrderItemResponse, OrderResponse, OrdersListResponse, ProductResponse
from src.api.services import checkout, get_order, list_orders

router = APIRouter(tags=["orders"])


def _order_to_response(order: Order) -> OrderResponse:
    items = []
    for oi in order.items:
        items.append(
            OrderItemResponse(
                id=oi.id,
                product=ProductResponse.model_validate(oi.product, from_attributes=True),
                quantity=oi.quantity,
                unit_price=oi.unit_price,
                line_total=oi.line_total,
            )
        )
    return OrderResponse(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        currency=order.currency,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items,
    )


@router.post(
    "/checkout",
    response_model=OrderResponse,
    summary="Checkout",
    description="Creates an order from the authenticated user's active cart and clears the cart.",
    operation_id="checkout_create_order",
)
def checkout_create(payload: CheckoutRequest, db: Session = Depends(get_db), user=Depends(get_current_user)) -> OrderResponse:
    order = checkout(db, user_id=user.id)
    return _order_to_response(order)


@router.get(
    "/orders",
    response_model=OrdersListResponse,
    summary="List orders",
    description="Returns the authenticated user's orders (most recent first).",
    operation_id="orders_list",
)
def orders_list(db: Session = Depends(get_db), user=Depends(get_current_user)) -> OrdersListResponse:
    orders = list_orders(db, user_id=user.id)
    return OrdersListResponse(orders=[_order_to_response(o) for o in orders])


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Order detail",
    description="Returns a single order (with items) for the authenticated user.",
    operation_id="orders_detail",
)
def orders_detail(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> OrderResponse:
    order = get_order(db, user_id=user.id, order_id=order_id)
    return _order_to_response(order)
