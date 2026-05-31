from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    gender = Column(String)
    address = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")

    orders = relationship("Orders", back_populates="user")
    cart = relationship("Cart", back_populates="user", uselist=False)


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, unique=True)

    products = relationship("Products", back_populates="category")


class Products(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    stock_quantity = Column(Integer)

    category = relationship("Categories", back_populates="products")
    order_items = relationship("OrderItems", back_populates="product")
    cart_items = relationship("CartItems", back_populates="product")


class Cart(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)

    user = relationship("Users", back_populates="cart")
    cart_items = relationship("CartItems", back_populates="cart")


class CartItems(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)

    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Products", back_populates="cart_items")


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_price = Column(Integer)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    delivery_address = Column(String)

    user = relationship("Users", back_populates="orders")
    order_items = relationship("OrderItems", back_populates="order")


class OrderItems(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_purchase = Column(Integer)

    order = relationship("Orders", back_populates="order_items")
    product = relationship("Products", back_populates="order_items")
