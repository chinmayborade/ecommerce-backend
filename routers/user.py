from fastapi import APIRouter, HTTPException, Depends, Path
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users
from typing import Annotated
from pydantic import BaseModel
from routers.auth import get_curr_user
from passlib.context import CryptContext

router = APIRouter(
    prefix="/user",
    tags=["user"]

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You Must Be User")

    return user


user_logged_dependency = Annotated[dict, Depends(get_user_info)]


class UserInfo(BaseModel):
    name: str
    email: str
    gender: str
    address: str

    class Config:
        from_attributes = True


class UpdateProfileReq(BaseModel):
    name: str
    gender: str
    address: str


class ChangePassReq(BaseModel):
    current_pass: str
    new_pass: str


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/profile_info", status_code=status.HTTP_200_OK, response_model=UserInfo)
async def get_info(current_user: user_logged_dependency, db: db_dependency):
    user = db.query(Users).filter(Users.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found"
        )
    return user


@router.put("/update_profile", status_code=status.HTTP_200_OK)
async def update_profile(
        update_data: UpdateProfileReq,
        current_user: user_logged_dependency,
        db: db_dependency,
):
    user = db.query(Users).filter(Users.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.name = update_data.name
    user.gender = update_data.gender
    user.address = update_data.address

    db.commit()
    return {"message": "Profile updated successfully"}


#view orders

#change password
@router.put("/change_password", status_code=status.HTTP_200_OK)
async def change_pass(req: ChangePassReq, current_user: user_logged_dependency, db: db_dependency):
    user = db.query(Users).filter(Users.id == current_user.get("user_id")).first()

    if not bcrypt_context.verify(req.current_pass, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current Password Is Incorrect"

        )

    user.hashed_password = bcrypt_context.hash(req.new_pass)
    db.commit()
    return {"message": "Password Changed Successfully"}
