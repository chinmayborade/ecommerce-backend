from fastapi import APIRouter, HTTPException, Depends, Path
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users, Products
from routers.auth import get_curr_user
from typing import Annotated
from pydantic import BaseModel

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_curr_user)]


def require_admin(current_user: user_dependency):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


admin_dependency = Annotated[dict, Depends(require_admin)]


class UserInfo(BaseModel):
    name: str
    email: str
    gender: str
    address: str

    class Config:
        from_attributes = True


class ProductMake(BaseModel):
    name: str
    description: str
    price: int
    category_id: int
    stock_quantity: int


@router.get("/users", response_model=list[UserInfo], status_code=status.HTTP_200_OK)
async def get_all_users(
        current_user: admin_dependency,
        db: db_dependency,
):
    users = db.query(Users).filter(Users.role == "user").all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )
    return users


@router.post("/create_prod", status_code=status.HTTP_201_CREATED)
async def create_product(
        product: ProductMake,
        current_user: admin_dependency,
        db: db_dependency,
):
    new_product = Products(**product.model_dump())
    db.add(new_product)
    db.commit()
    return {"message": "Product Created Successfully"}


@router.put("/update_prod/{prod_id}", status_code=status.HTTP_200_OK)
async def update_product(
        product_update: ProductMake,
        current_user: admin_dependency,
        db: db_dependency,
        prod_id: int = Path(gt=0),
):
    product = db.query(Products).filter(Products.id == prod_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found"
        )
    product.name = product_update.name
    product.description = product_update.description
    product.price = product_update.price
    product.category_id = product_update.category_id
    product.stock_quantity = product_update.stock_quantity

    db.add(product)
    db.commit()
    return {"message": "Product Updated Successfully"}


@router.delete("/delete_prod/{prod_id}", status_code=status.HTTP_200_OK)
async def delete_product(
        current_user: admin_dependency,
        db: db_dependency,
        prod_id: int = Path(gt=0),
):
    product = db.query(Products).filter(Products.id == prod_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found"
        )
    db.delete(product)
    db.commit()
    return {"message": "Product Deleted Successfully"}
