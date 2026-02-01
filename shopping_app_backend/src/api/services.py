from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.api.core.security import create_access_token, hash_password, verify_password
from src.api.db.models import Cart, CartItem, Order, OrderItem, Product, User


def _money(value: Decimal) -> Decimal:
    # Normalize Decimal with 2 places for predictable JSON.
    return value.quantize(Decimal("0.01"))


def _get_or_create_active_cart(db: Session, user_id: int) -> Cart:
    cart = db.execute(select(Cart).where(Cart.user_id == user_id, Cart.status == "active")).scalar_one_or_none()
    if cart:
        return cart
    cart = Cart(user_id=user_id, status="active")
    db.add(cart)
    db.flush()
    return cart


# PUBLIC_INTERFACE
def register_user(db: Session, *, email: str, password: str, full_name: str | None) -> tuple[User, str]:
    """Create a new user and return (user, access_token)."""
    user = User(email=email.lower(), password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return user, token


# PUBLIC_INTERFACE
def login_user(db: Session, *, email: str, password: str) -> tuple[User, str]:
    """Authenticate user and return (user, access_token)."""
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    return user, token


# PUBLIC_INTERFACE
def list_products(db: Session) -> list[Product]:
    """List active products."""
    return list(db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.id)).scalars().all())


# PUBLIC_INTERFACE
def get_product(db: Session, product_id: int) -> Product:
    """Get a product by id."""
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# PUBLIC_INTERFACE
def get_cart(db: Session, *, user_id: int) -> Cart:
    """Return the active cart for the user (creates if missing)."""
    cart = _get_or_create_active_cart(db, user_id)
    cart = db.execute(select(Cart).options(joinedload(Cart.items).joinedload(CartItem.product)).where(Cart.id == cart.id)).scalar_one()
    return cart


# PUBLIC_INTERFACE
def upsert_cart_item(db: Session, *, user_id: int, product_id: int, quantity: int) -> Cart:
    """Add a product to cart or update its quantity; returns updated cart."""
    product = get_product(db, product_id)
    cart = _get_or_create_active_cart(db, user_id)

    existing = db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    ).scalar_one_or_none()

    if existing is None:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, unit_price=product.price)
        db.add(item)
    else:
        existing.quantity = quantity
        existing.unit_price = product.price

    db.commit()
    return get_cart(db, user_id=user_id)


# PUBLIC_INTERFACE
def remove_cart_item(db: Session, *, user_id: int, cart_item_id: int) -> Cart:
    """Remove a cart item by id; returns updated cart."""
    cart = _get_or_create_active_cart(db, user_id)
    item = db.execute(select(CartItem).where(CartItem.id == cart_item_id, CartItem.cart_id == cart.id)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(item)
    db.commit()
    return get_cart(db, user_id=user_id)


# PUBLIC_INTERFACE
def clear_cart(db: Session, *, user_id: int) -> Cart:
    """Remove all items from the active cart."""
    cart = _get_or_create_active_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    return get_cart(db, user_id=user_id)


# PUBLIC_INTERFACE
def checkout(db: Session, *, user_id: int) -> Order:
    """
    Create an order from the current active cart.
    - Copies cart items into order_items
    - Computes totals
    - Clears cart
    """
    cart = get_cart(db, user_id=user_id)
    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    currency = cart.items[0].product.currency if cart.items else "USD"
    order = Order(user_id=user_id, status="pending", total_amount=Decimal("0.00"), currency=currency)
    db.add(order)
    db.flush()  # get order.id

    total = Decimal("0.00")
    for ci in cart.items:
        unit_price = ci.product.price
        line_total = _money(Decimal(ci.quantity) * unit_price)
        total += line_total
        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            quantity=ci.quantity,
            unit_price=unit_price,
            line_total=line_total,
        )
        db.add(oi)

    order.total_amount = _money(total)
    # Clear cart after creating order
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)

    db.commit()

    order = db.execute(
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .where(Order.id == order.id, Order.user_id == user_id)
    ).scalar_one()
    return order


# PUBLIC_INTERFACE
def list_orders(db: Session, *, user_id: int) -> list[Order]:
    """List orders for current user (most recent first)."""
    return list(
        db.execute(
            select(Order)
            .options(joinedload(Order.items).joinedload(OrderItem.product))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        .scalars()
        .all()
    )


# PUBLIC_INTERFACE
def get_order(db: Session, *, user_id: int, order_id: int) -> Order:
    """Get an order (with items) for current user."""
    order = db.execute(
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .where(Order.user_id == user_id, Order.id == order_id)
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
