from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.db.session import get_db
from src.api.schemas import ProductResponse
from src.api.services import get_product, list_products

router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List products",
    description="Returns active products for browsing.",
    operation_id="products_list",
)
def products_list(db: Session = Depends(get_db)) -> list[ProductResponse]:
    return list_products(db)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product detail",
    description="Returns details for a single product.",
    operation_id="products_detail",
)
def products_detail(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    return get_product(db, product_id)
