from fastapi import FastAPI
from routes.internal.microlesson_routes import router as microlesson_router

app = FastAPI()

app.include_router(microlesson_router, prefix="/microlesson")


@app.get("/")
async def root():
    return {"USE ROUTE : /microlesson/generate"}
