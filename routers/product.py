from fastapi import APIRouter, HTTPException, Path
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
    return db.query(Products).all()


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



@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_by_id(db: db_dependency, product_id: int = Path(gt=0)):
    product = db.query(Products).filter(Products.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found"
        )
    return product