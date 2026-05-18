from fastapi import APIRouter, Response, UploadFile, File, HTTPException
from modules.image_generator import generate_image
from pydantic import BaseModel, Field
from anyio import to_thread

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    steps: int = Field(default=4, ge=1, le=10)
    seed: int = Field(default=42)


@router.post("/generate")
async def from_text(request: GenerateRequest):
    try:
        result = await to_thread.run_sync(
            generate_image, request.prompt, request.seed, request.steps
        )
        return Response(content=result, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"generation failed: {str(e)}")


@router.post("/generate-from-file")
async def from_file(file: UploadFile = File(...)):
    if file.content_type != "text/plain":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a .txt file."
        )

    content = await file.read()
    prompt = content.decode("utf-8").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="File is empty")

    result = await to_thread.run_sync(generate_image, prompt)
    return Response(content=result, media_type="image/png")
