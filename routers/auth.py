from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.util import deprecated
from jose import jwt

from models import Users
from passlib.context import CryptContext
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = "985fa8bc6badb328bbc98de44e594927ca4c54f34a59428a70d6f6ab13daa864"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

http_bearer = HTTPBearer()


class CreateUserRequest(BaseModel):
    name: str
    email: str
    gender: str
    address: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(email: str, password: str, db):
    user = db.query(Users).filter(Users.email == email).first()

    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(email: str, user_id: int, expires_delta: timedelta, role: str):
    encode = {'sub': email, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# auth.py - add this function
async def get_curr_user(token: Annotated[str, Depends(oauth2_bearer)]):
    if token is None:                          # ← ADD THIS CHECK
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')

        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )
        return {'email': email, 'user_id': user_id, 'role': user_role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_req: CreateUserRequest, db: db_dependency):
    create_user_model = Users(
        name=create_user_req.name,
        email=create_user_req.email,
        gender=create_user_req.gender,
        address=create_user_req.address,
        hashed_password=bcrypt_context.hash(create_user_req.password),
        role=create_user_req.role

    )

    db.add(create_user_model)
    db.commit()
    return {"message": "User Created Successfully"}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    token = create_access_token(user.email, user.id, timedelta(minutes=20), user.role)

    return {'access_token': token, 'token_type': 'bearer'}
