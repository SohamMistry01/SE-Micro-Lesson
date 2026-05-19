from fastapi import FastAPI
from routes.internal.imagegen_route import router as imagegen_router
from routes.internal.microlesson_routes import router as microlesson_router

app = FastAPI()

app.include_router(imagegen_router, prefix="/imagegen")
app.include_router(microlesson_router, prefix="/microlesson")


@app.get("/")
async def root():
    return {"Message : /generate for raw text, /generate-from-file for plain text file"}
