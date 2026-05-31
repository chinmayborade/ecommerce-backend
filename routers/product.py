from fastapi import APIRouter, HTTPException, Path, Query
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Products
from typing import Annotated
from fastapi import Depends

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_products(db: db_dependency):
    products = db.query(Products).all()

    result = []

    for product in products:
        result.append({

            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "category_name": product.category.name if product.category else None,
            "stock_quantity": product.stock_quantity
        })

    return result


@router.get("/filter/price", status_code=status.HTTP_200_OK)
async def filter_by_price(db: db_dependency, min_price: int = 0, max_price: int = 100000):
    return db.query(Products).filter(
        Products.price > min_price,
        Products.price < max_price
    ).all()


@router.get("/filter/category", status_code=status.HTTP_200_OK)
async def filter_by_category_id(db: db_dependency, category_id: int):
    return db.query(Products).filter(Products.category_id == category_id).first()


@router.get("/filter/quantity", status_code=status.HTTP_200_OK)
async def get_by_quantity(db: db_dependency, stock_quantity: int):
    return db.query(Products).filter(Products.stock_quantity == stock_quantity).first()


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_products(
        db: db_dependency,
        q: str = Query(..., min_length=1, description="Search by product name"),
):
    search_term = f"%{q.lower()}%"
    products = db.query(Products).filter(
        Products.name.ilike(search_term)
    ).all()

    if not products:
        return {
            "message": f"No products found for '{q}'",
            "results": [],
            "count": 0
        }

    results = []
    for product in products:
        results.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "category_name": product.category.name if product.category else None,
            "stock_quantity": product.stock_quantity
        })

    return {
        "results": results,
        "count": len(results)
    }


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_by_id(db: db_dependency, product_id: int = Path(gt=0)):
    product = db.query(Products).filter(Products.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found"
        )
    return product
