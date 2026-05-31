from fastapi import FastAPI
from database import engine, Base
from routers.product import router as Product
from routers.auth import router as Auth
from routers.admin import router as Admin
from routers.user import router as User
from routers.cart import router as Cart
from routers.categories import router as Categories
from routers.orders import router as Orders

app = FastAPI()

app.openapi_schema = None

Base.metadata.create_all(bind=engine)


@app.get("/health_check")
def health_check():
    return {"status": "ok"}


app.include_router(Product)
app.include_router(Auth)
app.include_router(Admin)
app.include_router(User)
app.include_router(Cart)
app.include_router(Orders)
app.include_router(Categories)
