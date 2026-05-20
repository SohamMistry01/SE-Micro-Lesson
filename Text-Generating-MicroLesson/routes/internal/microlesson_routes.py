from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from modules.orchestrator import process_microlessons_logic
from modules.prompt_config import DEFAULT_CUSTOM_PROMPT

router = APIRouter()


class MicroLessonRequest(BaseModel):
    category: str = Field(
        default="general",
        description="Category of the micro-lesson (e.g., 'theoretical', 'practical', 'general')",
    )
    template_path: str = Field(
        default="default",
        description="Key for the template to use (e.g., 'default'). Maps to predefined paths in the backend.",
    )
    priority_llm: Optional[str] = Field(
        default=None, description="Optional LLM model name to prioritize for this task."
    )
    filename: Optional[str] = Field(
        default=None,
        description="Optional custom filename base. Can include placeholders like {uid} and {timestamp}. Default is '{uid}_{timestamp}'.",
    )
    custom_prompt: Optional[str] = Field(
        default=DEFAULT_CUSTOM_PROMPT,
        description="Fully custom prompt template to override the default category prompt. MUST contain '{content}'.",
    )


# i changed this to /generate from /microlessons/generate for simplicity, change if wrong
@router.post("/generate")
async def generate_microlesson(request: MicroLessonRequest):
    try:
        result = process_microlessons_logic(
            category=request.category,
            template_path=request.template_path,
            priority_llm=request.priority_llm,
            custom_prompt=request.custom_prompt,
            filename_pattern=request.filename,
        )
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
