from fastapi import FastAPI,Request

from database import engine,Base
from routers.product import router as Product
from routers.auth import router as Auth




app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/health_check")
def health_check():
    return {"status": "ok"}


app.include_router(Product)
app.include_router(Auth)

