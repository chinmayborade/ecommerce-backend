from fastapi import APIRouter, HTTPException, Depends, Path
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Categories
from typing import Annotated
from pydantic import BaseModel
from routers.auth import get_curr_user

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
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


class CategoryCreateReq(BaseModel):
    id:int
    name: str


class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CategoryResponse], status_code=status.HTTP_200_OK)
async def view_all_categ(db: db_dependency):
    categories = db.query(Categories).all()
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Categories Found"
        )
    return categories


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_category(req: CategoryCreateReq, _: admin_dependency, db: db_dependency):
    existing_id = db.query(Categories).filter(Categories.id == req.id).first()
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with id {req.id} already exists"
        )

    existing = db.query(Categories).filter(Categories.name == req.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category {req.name} already exists"
        )
    category = Categories(id=req.id,name=req.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return {"message": f"Category '{req.name}' created with id {req.id}", "id": category.id}


@router.put("/modify_category/{category_id}", status_code=status.HTTP_200_OK)
async def modify_category(
        req: CategoryCreateReq,
        _: admin_dependency,
        db: db_dependency,
        category_id: int = Path(gt=0)
):
    category = db.query(Categories).filter(Categories.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category Not Found"
        )

    existing = db.query(Categories).filter(Categories.name == req.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{req.name}' already exists"
        )

    category.name = req.name
    db.commit()
    return {"message": "Category Updated Successfully"}


@router.delete("/delete_categ/{category_id}", status_code=status.HTTP_200_OK)
async def delete_cat_by_id(_: admin_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    category = db.query(Categories).filter(Categories.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category Not Found"
        )

    db.delete(category)
    db.commit()
    return {"message":"Category Deleted Successfully"}
