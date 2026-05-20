import os
import io
from datetime import datetime
from ..config import settings
from ..prompt_config import get_resolved_prompt
from .. import rag_engine
from .. import google_services as gs
from typing import Optional
from .helpers import (
    _fetch_pending_tasks,
    _plan_and_generate_images,
    _build_extended_prompt,
    _generate_filenames,
    _generate_and_upload_assets,
    _fetch_content_smart
)



TEMPLATE_MAP = {
    "default": settings.DEFAULT_TEMPLATE_PATH,
    # Easily add more templates here in the future:
    # "minimal": "./modules/microlesson_generator/pdf_templates/minimal.pdf",
    # "dark_theme": "./modules/microlesson_generator/pdf_templates/dark.pdf"
}

# ==========================================
# Main Processor
# ==========================================

def process_microlessons_logic(
    category: str,
    template_path: Optional[str] = None,
    priority_llm: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    filename_pattern: Optional[str] = None,
):
    resolved_prompt = get_resolved_prompt(category, custom_prompt)
    template_path = template_path or "default"
    final_template_path = TEMPLATE_MAP.get(template_path.lower())

    # 1. Fetch & Filter Data
    tasks = _fetch_pending_tasks()
    if tasks is None:
        return {"status": "No data found"}

    results_summary = []

    # 2. Process each UID task loop
    for uid, items in tasks.items():
        print(f"\nProcessing UID: {uid}...")

        # Extract Text
        contents = []
        for item in items:
            text = _fetch_content_smart(item["content_data"])
            if text and text.strip():
                contents.append(text.strip())

        if not contents:
            print(f"Skipping {uid}: No valid textual content found.")
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 3. Plan & Generate Images
        image_instructions = _plan_and_generate_images(uid, contents, priority_llm, timestamp)
        extended_prompt = _build_extended_prompt(resolved_prompt, image_instructions)

        # 4. Generate Final Lesson Content
        lesson_md = rag_engine.run_rag_pipeline(
            contents=contents,
            category=category,
            priority_llm=priority_llm,
            prompt_template=extended_prompt,
        )

        # 5. Determine Filenames & Generate Assets
        txt_filename, pdf_filename, ppt_filename = _generate_filenames(
            uid, timestamp, filename_pattern, len(tasks)
        )
        
        txt_link, pdf_link, ppt_link = _generate_and_upload_assets(
            uid, lesson_md, txt_filename, pdf_filename, ppt_filename, final_template_path
        )

        # 6. Write results back to Google Sheet
        gs.append_output_data([uid, txt_link, pdf_link, ppt_link, timestamp])

        for item in items:
            gs.update_row_status(item["row_index"], "Yes")

        results_summary.append(f"UID {uid} processed successfully.")

    return {"processed": results_summary}