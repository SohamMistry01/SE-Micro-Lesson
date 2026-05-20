from typing import Optional

# Extracted Mandatory Instructions to keep output consistently formatted
MANDATORY_INSTRUCTIONS = """Strict Requirements:
- Output MUST be in valid Markdown format. Do NOT use emojis.
- Start with a clear, engaging main title using a single '#'.
- Use '##' for main sections.
- Use bullet points and numbered lists to break down complex information."""

PROMPT_TEMPLATES = {
    "theoretical": "You are an expert academic educator. Create a comprehensive, conceptually rich Micro-Lesson.\n\n"
    + MANDATORY_INSTRUCTIONS
    + """
    - Focus heavily on foundational concepts, theoretical frameworks, historical context, and deep understanding.
    - Use '##' for main sections (e.g., Core Theory, Historical Context, Key Principles, Conceptual Framework).
    - Avoid adding hands-on exercises; instead, focus on thought-provoking questions or analytical perspectives.
    
    Summaries to base the lesson on:
    {content}
    
    Micro-Lesson:""",
    "practical": "You are an expert applied skills coach. Create a highly practical, action-oriented Micro-Lesson.\n\n"
    + MANDATORY_INSTRUCTIONS
    + """
    - Focus heavily on application, real-world scenarios, and actionable takeaways.
    - Use '##' for main sections (e.g., Real-World Application, Step-by-Step Guide, Try It Yourself).
    - You MUST include a 'Practical Exercise' or 'Activity' section with a concrete task the learner can perform immediately.
    
    Summaries to base the lesson on:
    {content}
    
    Micro-Lesson:""",
    "general": "You are an expert educator. Create a detailed, engaging Micro-Lesson.\n\n"
    + MANDATORY_INSTRUCTIONS
    + """
    - Structure the lesson logically using '##' for section headers (e.g., Overview, Key Takeaways, Detailed Explanation, Summary).
    
    Summaries to base the lesson on:
    {content}
    
    Micro-Lesson:""",
}

# The template that will appear in the Swagger UI for users to edit
DEFAULT_CUSTOM_PROMPT = (
    "You are an expert educator. Create a highly customized Micro-Lesson.\n\n"
    + MANDATORY_INSTRUCTIONS
    + """
- [ADD YOUR CUSTOM INSTRUCTIONS HERE]

Summaries to base the lesson on:
{content}

Micro-Lesson:"""
)


def get_resolved_prompt(category: str, custom_prompt: Optional[str] = None) -> str:
    """
    Returns the custom prompt if provided, otherwise fetches the category's enhanced prompt.
    """
    if custom_prompt and custom_prompt.strip():
        # Safety catch: Ensure {content} exists so the code doesn't break
        if "{content}" not in custom_prompt:
            custom_prompt += "\n\nSummaries:\n{content}\n\nMicro-Lesson:"
        return custom_prompt
    return PROMPT_TEMPLATES.get(category.lower(), PROMPT_TEMPLATES["general"])

