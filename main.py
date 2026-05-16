from fastapi import FastAPI, Request, Depends

from database import engine, Base
from routers.product import router as Product
from routers.auth import router as Auth
from routers.admin import router as Admin
from routers.user import router as User
from typing import Annotated

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/health_check")
def health_check():
    return {"status": "ok"}


app.include_router(Product)
app.include_router(Auth)
app.include_router(Admin)
app.include_router(User)