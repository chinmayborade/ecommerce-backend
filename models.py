from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base
from sqlalchemy.orm import relationship


# users table
class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    orders = relationship("Orders", back_populates="user")
    name = Column(String)
    email = Column(String, unique=True)
    gender = Column(String)
    address = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean)
    role = Column(String)


# product tables

class Products(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    order_items = relationship("OrderItems", back_populates="product")
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    stock_quantity = Column(Integer)


# cart items
class CartItems(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product = relationship("Products")
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("Users", back_populates="orders")
    total_price = Column(String)
    status = Column(String, default="pending")
    created_at = Column(String)


class OrderItems(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Products", back_populates="order_items")
    quantity = Column(Integer)
    price_at_purchase = Column(Integer)


class Cart(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
