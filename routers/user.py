from fastapi import APIRouter, HTTPException, Depends, Path
from starlette import status
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users
from typing import Annotated
from pydantic import BaseModel
from routers.auth import get_curr_user

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



@router.get("/profile_info", status_code=status.HTTP_200_OK)
async def get_info(user: user_logged_dependency, db: db_dependency):
    user = db.query(Users).filter(Users.id == user.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found"
        )
    return user



# update profile




#view orders

#change password






