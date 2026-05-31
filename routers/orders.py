from fastapi import APIRouter, HTTPException, Depends, Path
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Orders, OrderItems, Cart, CartItems, Products, Users
from typing import Annotated
from pydantic import BaseModel
from routers.auth import get_curr_user
from datetime import datetime

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_curr_user)]


def get_user_info(user: user_dependency):
    if user.get("role") != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can place orders"
        )
    return user


user_logged_dependency = Annotated[dict, Depends(get_user_info)]


def require_admin(current_user: user_dependency):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


admin_dependency = Annotated[dict, Depends(require_admin)]


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price_at_purchase: int
    item_total: int

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: int
    status: str
    created_at: str
    order_items: list[OrderItemResponse]

    class Config:
        from_attributes = True


class PlaceOrderReq(BaseModel):
    delivery_address: str


class UpdateOrderStatusReq(BaseModel):
    status: str


@router.post("/place", status_code=status.HTTP_201_CREATED)
async def place_order(
        current_user: user_logged_dependency,
        db: db_dependency,
):
    user_id = current_user.get("user_id")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart is empty"
        )

    cart_items = db.query(CartItems).filter(CartItems.cart_id == cart.id).all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty — add items first"
        )

    for item in cart_items:
        product = db.query(Products).filter(Products.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for {product.name}. Available: {product.stock_quantity}"
            )

    # ✅ calculate total price
    total_price = 0
    for item in cart_items:
        product = db.query(Products).filter(Products.id == item.product_id).first()
        total_price += product.price * item.quantity

    # ✅ create order
    order = Orders(
        user_id=user_id,
        total_price=total_price,
        status="pending",
        created_at=datetime.utcnow(),
        delivery_address=user.address  # ✅ from user profile
    )
    db.add(order)
    db.flush()  # flush to get order.id without committing

    # ✅ create order items & reduce stock
    for item in cart_items:
        product = db.query(Products).filter(Products.id == item.product_id).first()

        order_item = OrderItems(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=product.price
        )
        db.add(order_item)

        # ✅ reduce stock
        product.stock_quantity -= item.quantity
        db.add(product)

    # ✅ clear cart
    db.query(CartItems).filter(CartItems.cart_id == cart.id).delete()

    # ✅ commit everything
    db.commit()
    db.refresh(order)

    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "total_price": total_price,
        "status": "pending",
        "delivery_address": user.address
    }


# ── VIEW USER'S ORDERS ─────────────────────────────────────────────────────────
@router.get("/my_orders", status_code=status.HTTP_200_OK)
async def get_user_orders(
        current_user: user_logged_dependency,
        db: db_dependency,
):
    user_id = current_user.get("user_id")

    user = db.query(Users).filter(Users.id == user_id).first()

    orders = db.query(Orders).filter(Orders.user_id == user_id).all()

    if not orders:
        return {"orders": [], "total_orders": 0}

    result = []
    for order in orders:
        order_items = db.query(OrderItems).filter(OrderItems.order_id == order.id).all()

        items_data = []
        for oi in order_items:
            product = db.query(Products).filter(Products.id == oi.product_id).first()
            items_data.append({
                "product_id": oi.product_id,
                "product_name": product.name,
                "quantity": oi.quantity,
                "price_at_purchase": oi.price_at_purchase,
                "item_total": oi.price_at_purchase * oi.quantity
            })

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "delivery_address": order.delivery_address,

            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "gender": user.gender,
                "address": user.address

            },

            "order_items": items_data
        })

    return {"orders": result, "total_orders": len(result)}


# ── VIEW SINGLE ORDER ──────────────────────────────────────────────────────────
@router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_detail(
        current_user: user_logged_dependency,
        db: db_dependency,
        order_id: int = Path(gt=0),
):
    user_id = current_user.get("user_id")

    user = db.query(Users).filter(Users.id == user_id).first()

    order = db.query(Orders).filter(
        Orders.id == order_id,
        Orders.user_id == user_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order_items = db.query(OrderItems).filter(OrderItems.order_id == order.id).all()

    items_data = []
    for oi in order_items:
        product = db.query(Products).filter(Products.id == oi.product_id).first()
        items_data.append({
            "product_id": oi.product_id,
            "product_name": product.name,
            "quantity": oi.quantity,
            "price_at_purchase": oi.price_at_purchase,
            "item_total": oi.price_at_purchase * oi.quantity
        })

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_price": order.total_price,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "delivery_address": order.delivery_address,

        "user": {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "gender": user.gender,
            "address": user.address
        },

        "order_items": items_data
    }


# ADMIN SIDE ENDPOINTS
# ── ADMIN: VIEW ALL ORDERS ────────────────────────────────────────────────────
@router.get("/admin/all_orders", status_code=status.HTTP_200_OK)
async def get_all_orders(
        _: admin_dependency,
        db: db_dependency,
):
    orders = db.query(Orders).all()

    if not orders:
        return {"orders": [], "total_orders": 0}

    result = []
    for order in orders:
        user = db.query(Users).filter(Users.id == order.user_id).first()
        order_items = db.query(OrderItems).filter(OrderItems.order_id == order.id).all()

        items_data = []
        for oi in order_items:
            product = db.query(Products).filter(Products.id == oi.product_id).first()
            items_data.append({
                "product_id": oi.product_id,
                "product_name": product.name,
                "quantity": oi.quantity,
                "price_at_purchase": oi.price_at_purchase,
                "item_total": oi.price_at_purchase * oi.quantity
            })

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "Unknown",
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "delivery_address": order.delivery_address,
            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "gender": user.gender,
                "address": user.address,
            },

            "order_items": items_data
        })

    return {"orders": result, "total_orders": len(result)}


# ── ADMIN: UPDATE ORDER STATUS ────────────────────────────────────────────────
@router.put("/admin/update_status/{order_id}", status_code=status.HTTP_200_OK)
async def update_order_status(
        req: UpdateOrderStatusReq,
        _: admin_dependency,
        db: db_dependency,
        order_id: int = Path(gt=0),
):
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    order = db.query(Orders).filter(Orders.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order.status = req.status
    db.commit()

    return {
        "message": f"Order status updated to '{req.status}'",
        "order_id": order.id,
        "new_status": order.status
    }
