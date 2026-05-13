from fastapi import APIRouter,HTTPException,Depends,Path,Request
from pydantic import BaseModel,Field
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Products
from typing import Annotated


router = APIRouter(
    prefix="/products",
    tags=["products"],
)

def get_db():

    db=SessionLocal()

    try:
        yield db
    finally:
        db.close()



# dependencyinjection
db_dependency= Annotated[Session,Depends(get_db)]



class ProductMake(BaseModel):

    name:str
    description:str
    price:int
    category_id:int
    stock_quantity:int



@router.get("/",status_code=status.HTTP_200_OK)
async def get_all_products(db:db_dependency):
    return db.query(Products).all()

#get single product by ID
@router.get("/{product_id}",status_code=status.HTTP_200_OK)
async def get_by_id(db:db_dependency,product_id:int=Path(gt=0)):
    product = db.query(Products).filter(Products.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product Not Found")
    return product

#filter by price range
@router.get("/filter/price",status_code=status.HTTP_200_OK)
async def filter_by_price(db:db_dependency,min_price:int=0,max_price:int=100000):
    return db.query(Products).filter(Products.price > min_price,Products.price < max_price).all()




@router.post("/create_prod",status_code=status.HTTP_201_CREATED)
async def create_product(product:ProductMake,db:db_dependency):
    new_product = Products(**product.model_dump())

    db.add(new_product)

    db.commit()


# filter product by category_id
@router.get("/category_id",status_code=status.HTTP_200_OK)
async def filter_by_category_id(db:db_dependency,category_id:int):
    return db.query(Products).filter(Products.category_id == category_id).first()

#filter product by quantity
@router.get("/get_by_quantity",status_code=status.HTTP_200_OK)
async def get_by_quantity(db:db_dependency,stock_quantity:int):
    return db.query(Products).filter(Products.stock_quantity == stock_quantity ).first()


#edit product
@router.put("/change_details/{prod_id}",status_code=status.HTTP_204_NO_CONTENT)
async def change_details(product_update:ProductMake,db:db_dependency,prod_id:int=Path(gt=0)):
      prod_model = db.query(Products).filter(Products.id == prod_id ).first()

      if prod_model is None:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product Not Found")

      prod_model.name = product_update.name
      prod_model.description = product_update.description
      prod_model.price = product_update.price
      prod_model.category_id = product_update.category_id
      prod_model.stock_quantity = product_update.stock_quantity

      db.add(prod_model)
      db.commit()
      return {"message":"Product Updated Successfully"}


#delete prod by name
@router.delete("/del_prod/{name}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(db:db_dependency,name:str):
    product = db.query(Products).filter(Products.name == name).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product Not Found")
    db.delete(product)
    db.commit()
    return {"message":"Product Deleted Successfully"}


#delete product by id
@router.delete("/delete_prod",status_code= status.HTTP_204_NO_CONTENT)
async def delete_product(db:db_dependency,product_id:int):
   product = db.query(Products).filter(Products.id == product_id).first()

   if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product Not Found")

   db.delete(product)
   db.commit()












