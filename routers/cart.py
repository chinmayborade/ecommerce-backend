from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Annotated
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users, Products, Cart, CartItems
from pydantic import BaseModel
from routers.auth import get_curr_user

router = APIRouter(
    prefix="/cart",
    tags=["cart"]

)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_curr_user)]


def get_cur_user_info(user: user_dependency):
    if user.get("role") != "user":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Only Users Can access cart"
        )
    return user


user_logged_dependency = Annotated[dict, Depends(get_cur_user_info)]


class AddToCart(BaseModel):
    prod_id: int
    quantity: int


class UpdateCartReq(BaseModel):
    quantity: int


def get_or_create_cart(user_id: int, db: Session):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


# add to cart
@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_to_cart(req: AddToCart, curr_user: user_logged_dependency, db: db_dependency):
    try:
        product = db.query(Products).filter(Products.id == req.prod_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prod Not Found"
            )

        if product.stock_quantity < req.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} items in stock"
            )

        cart = get_or_create_cart(curr_user.get("user_id"), db)

        existing_item = db.query(CartItems).filter(
            CartItems.cart_id == cart.id,
            CartItems.product_id == req.prod_id
        ).first()

        if existing_item:
            existing_item.quantity += req.quantity
            db.commit()
            return {"message": "Cart updated Successfully"}

        cart_item = CartItems(
            cart_id=cart.id,
            product_id=req.prod_id,
            quantity=req.quantity
        )
        db.add(cart_item)
        db.commit()
        return {"message": "Prod Added To Cart Successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"CART ERROR: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# view added to cart items
@router.get("/", status_code=status.HTTP_200_OK)
async def get_cart_items(curr_user: user_logged_dependency, db: db_dependency, ):
    cart = db.query(Cart).filter(Cart.user_id == curr_user.get("user_id")).first()

    if not cart:
        return {"cart": [], "total": 0}

    items = db.query(CartItems).filter(CartItems.cart_id == cart.id).all()

    cart_data = []
    total = 0

    for item in items:
        products = db.query(Products).filter(Products.id == item.product_id).first()
        item_total = products.price * item.quantity
        total += item_total
        cart_data.append(
            {
                "cart_item_id": item.id,
                "product_id": products.id,
                "product_name": products.name,
                "price": products.price,
                "quantity": item.quantity,
                "item_total": item_total

            }
        )

    return {"cart": cart_data, "total": total}


# update quantity
@router.put("/update/{item_id}", status_code=status.HTTP_200_OK)
async def update_cart_item(req: UpdateCartReq, curr_user: user_logged_dependency, db: db_dependency,
                           item_id: int = Path(gt=0)):
    cart = db.query(Cart).filter(Cart.user_id == curr_user.get("user_id")).first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart Not Found"
        )

    cart_item = db.query(CartItems).filter(CartItems.id == item_id, CartItems.cart_id == cart.id).first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item Not Found In Cart"
        )

    product = db.query(Products).filter(Products.id == cart_item.product_id).first()

    if product.stock_quantity < req.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f" Only {product.stock_quantity} items in stock"

        )

    cart_item.quantity = req.quantity
    db.commit()
    return {"message": "Cart Item Updated Successfully"}


# remove item from cart
@router.delete("/remove/{item_id}", status_code=status.HTTP_200_OK)
async def remove_frm_cart(
        curr_user: user_logged_dependency,
        db: db_dependency,
        item_id: int = Path(gt=0),
):
    cart = db.query(Cart).filter(Cart.user_id == curr_user.get("user_id")).first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart Not Found"
        )

    cart_item = db.query(CartItems).filter(
        CartItems.id == item_id,  # ✅ item_id not item.id
        CartItems.cart_id == cart.id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item Not Found In Cart"
        )

    db.delete(cart_item)
    db.commit()
    return {"message": "Item Removed From Cart Successfully"}


# clear cart
@router.delete("/clear_cart", status_code=status.HTTP_200_OK)
async def clear_cart(
        curr_user: user_logged_dependency,
        db: db_dependency
):
    cart = db.query(Cart).filter(Cart.user_id == curr_user.get("user_id")).first()

    if not cart:
        return {"message": "Cart is already empty"}

    db.query(CartItems).filter(CartItems.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart Cleared Successfully"}
