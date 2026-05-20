import os
import re
from datetime import datetime
from collections import defaultdict
import time
from typing import Optional

from modules.config import settings
from modules import google_services as gs
from modules import rag_engine
from modules import pdf_generator
from modules.prompt_config import get_resolved_prompt
from modules import ppt_generator
from modules import image_generator


def save_generated_image(prompt: str, output_path: str) -> bool:
    """
    Calls the SDXL pipeline, extracts the raw bytes, and saves them locally.
    """
    try:
        # Ensure the directory exists (e.g., creating the ./temp folder)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"🎨 Generating SDXL Turbo image for prompt: '{prompt[:50]}...'")

        # Call your function (uses 1 step, guidance_scale=0.0 as you configured)
        img_bytes = image_generator.generate_image(prompt=prompt, steps=1, seed=42)

        # Write the binary stream data to disk
        with open(output_path, "wb") as f:
            f.write(img_bytes)

        print(f"✅ Image successfully saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to generate or save image: {e}")
        return False


def extract_drive_id(url: str) -> str:

    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)

    if match:
        return match.group(1)

    match = re.search(r"id=([a-zA-Z0-9_-]+)", url)

    if match:
        return match.group(1)

    return None


def fetch_content_smart(content_cell: str) -> str:
    """

    Intelligently extracts text from direct text, Google Docs, Drive PDFs, or Web PDFs.

    """

    content_cell = str(content_cell).strip()

    if not content_cell:
        return ""

    # 1. Direct Text (If it doesn't look like a URL, treat it as raw text)

    if not content_cell.startswith(("http://", "https://", "www.")):
        print("   Detected Direct Text Content.")

        return content_cell

    # 2. Google Drive Links (Docs, PDFs, TXT)

    if "drive.google.com" in content_cell or "docs.google.com" in content_cell:
        file_id = extract_drive_id(content_cell)

        if file_id:
            print(f"   Detected Drive Link. Parsing ID: {file_id}")

            return gs.get_and_parse_drive_file(file_id)

        else:
            print(f"   Warning: Could not extract ID from Drive URL: {content_cell}")

            return ""

    # 3. Standard Web URLs (Direct PDF links or Text files)

    try:
        response = requests.get(content_cell)

        response.raise_for_status()

        # Check if the URL is a standard Web PDF

        if content_cell.lower().endswith(
            ".pdf"
        ) or "application/pdf" in response.headers.get("Content-Type", ""):
            print("   Detected standard Web PDF. Parsing...")

            pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(response.content))

            extracted_text = []

            # Legacy PyPDF2 iteration

            for i in range(pdf_reader.getNumPages()):
                page = pdf_reader.getPage(i)

                text = page.extractText()  # Capital 'T'

                if text:
                    extracted_text.append(text)

            return "\n".join(extracted_text)

        print("   Detected standard Web content.")

        return response.text

    except Exception as e:
        print(f"   Error fetching URL {content_cell}: {e}")

        return ""


TEMPLATE_MAP = {
    "default": settings.DEFAULT_TEMPLATE_PATH,
    # Easily add more templates here in the future:
    # "minimal": "./modules/microlesson_generator/pdf_templates/minimal.pdf",
    # "dark_theme": "./modules/microlesson_generator/pdf_templates/dark.pdf"
}


def process_microlessons_logic(
    category: str,
    template_path: Optional[str] = None,
    priority_llm: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    filename_pattern: Optional[str] = None,
):
    resolved_prompt = get_resolved_prompt(category, custom_prompt)
    final_template_path = TEMPLATE_MAP.get(
        template_path.lower(), settings.DEFAULT_TEMPLATE_PATH
    )

    # Fetch Input Data
    rows = gs.fetch_input_data()
    if not rows:
        return {"status": "No data found"}

    data_rows = rows[1:]
    tasks = defaultdict(list)

    # Filter rows expecting UID -> Content Link -> Status
    for i, row in enumerate(data_rows):
        sheet_row_index = i + 2
        if len(row) < 3:
            continue
        uid, content_cell, status = row[0], row[1], row[2]

        if status.strip().lower() == "no":
            tasks[uid].append(
                {"row_index": sheet_row_index, "content_data": content_cell}
            )

    results_summary = []

    # Process each UID task loop
    for uid, items in tasks.items():
        print(f"\nProcessing UID: {uid}...")

        contents = []
        for item in items:
            text = fetch_content_smart(item["content_data"])
            if text and text.strip():
                contents.append(text.strip())

        if not contents:
            print(f"Skipping {uid}: No valid textual content found.")
            continue

        # 2. ASK LLM TO DESIGN RELEVANT DIAGRAM CONCEPTS
        print(f"🤖 Planning visual illustrations for UID: {uid}...")
        image_planning_query = (
            f"Based on the following document context, identify 2 sections that would benefit "
            f"from a simple visual diagram or illustration.\n\n"
            f"STRICT RULES for the image prompts:\n"
            f"- Maximum 10 words per prompt.\n"
            f"- NEVER ask for timelines, or charts — SDXL cannot render those.\n"
            f"- Only describe physical, concrete objects or simple scenes "
            f"(e.g. 'army soldiers marching battlefield', 'cannon fire smoke field', "
            f"'old ship ocean sailing', 'ancient crown throne room').\n"
            f"- Use nouns and adjectives only. No verbs, no sentences.\n\n"
            f"Return your answer EXACTLY using this format and nothing else:\n"
            f"IMAGE 1 DESCRIPTION: [one sentence on where/why this image fits]\n"
            f"IMAGE 1 PROMPT: [max 10 words, physical scene only, no proper nouns]\n"
            f"IMAGE 2 DESCRIPTION: [one sentence on where/why this image fits]\n"
            f"IMAGE 2 PROMPT: [max 10 words, physical scene only, no proper nouns]\n\n"
            f"Context:\n{contents}"
        )

        raw_image_plan = rag_engine.run_rag_pipeline(
            contents=[image_planning_query],
            category="general",
            priority_llm=priority_llm,
            prompt_template="{content}",
        )
        print("\n--- DEBUG: RAW IMAGE PLAN FROM LLM ---")
        print(raw_image_plan)
        print("--------------------------------------\n")

        # Parse the structured text lines
        img1_desc = re.search(r"IMAGE 1 DESCRIPTION:\s*(.*)", raw_image_plan)
        img1_prompt = re.search(r"IMAGE 1 PROMPT:\s*(.*)", raw_image_plan)
        img2_desc = re.search(r"IMAGE 2 DESCRIPTION:\s*(.*)", raw_image_plan)
        img2_prompt = re.search(r"IMAGE 2 PROMPT:\s*(.*)", raw_image_plan)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_injection_instructions = ""

        # 3. GENERATE AND COLLECT LOCAL ASSET LINKS
        if img1_prompt and img1_desc:
            # Enforce the 10-word limit as a safety net even if the LLM drifts
            safe_prompt_1 = " ".join(img1_prompt.group(1).strip().split()[:10])
            path_1 = f"./temp/{uid}_{timestamp}_img1.png"
            if save_generated_image(safe_prompt_1, path_1):
                image_injection_instructions += f"\n- Image 1 File Path: {path_1}\n  Context/Description: {img1_desc.group(1).strip()}\n"

        if img2_prompt and img2_desc:
            # Enforce the 10-word limit as a safety net even if the LLM drifts
            safe_prompt_2 = " ".join(img2_prompt.group(1).strip().split()[:10])
            path_2 = f"./temp/{uid}_{timestamp}_img2.png"
            if save_generated_image(safe_prompt_2, path_2):
                image_injection_instructions += f"\n- Image 2 File Path: {path_2}\n  Context/Description: {img2_desc.group(1).strip()}\n"

        # 4. APPEND LAYOUT INSTRUCTIONS FOR THE MAIN LESSON LLM CALL
        extended_prompt = resolved_prompt
        if image_injection_instructions:
            extended_prompt += (
                f"\n\n🚨 MANDATORY IMAGE PLACEMENT RULES — follow exactly:\n"
                f"1. Place each image ONLY at the END of a complete section, never inside a list or mid-paragraph.\n"
                f"2. Always add one blank line before and after the image tag.\n"
                f"3. Always follow each image with a short italic caption on the next line using this format: "
                f"`*Figure: [brief description of what the image shows]*`\n"
                f"4. Never place two images on consecutive pages or directly next to each other.\n"
                f"5. Use standard Markdown syntax: `![Description](File_Path)`. Do not alter the paths.\n"
                f"6. NEVER place an image inside a bullet point list or numbered list.\n\n"
                f"EXAMPLE of correct placement:\n"
                f"...last sentence of a section.\n\n"
                f"![alt text](./temp/image.png)\n"
                f"*Figure: A visual overview of the concept above.*\n\n"
                f"## Next Section Heading\n\n"
                f"Available assets:\n{image_injection_instructions}"
            )

        # 5. GENERATE FINAL LESSON WITH EMBEDDED MARKDOWN IMAGE TAGS
        lesson_md = rag_engine.run_rag_pipeline(
            contents=contents,
            category=category,
            priority_llm=priority_llm,
            prompt_template=extended_prompt,
        )

        # --- File Naming & Uploading logic follows ---
        if filename_pattern:
            base_name = filename_pattern.replace("{uid}", str(uid)).replace(
                "{timestamp}", timestamp
            )
            if "{uid}" not in filename_pattern and len(tasks) > 1:
                base_name = f"{base_name}_{uid}"
            txt_filename = f"{base_name}.txt"
            pdf_filename = f"{base_name}.pdf"
            ppt_filename = f"{base_name}.pptx"
        else:
            txt_filename = f"{uid}_{timestamp}.txt"
            pdf_filename = f"{uid}_{timestamp}.pdf"
            ppt_filename = f"{uid}_{timestamp}.pptx"

        txt_link = gs.upload_to_drive(
            txt_filename, lesson_md.encode("utf-8"), "text/plain"
        )

        try:
            pdf_bytes = pdf_generator.create_pdf_bytes(lesson_md, final_template_path)
            pdf_link = gs.upload_to_drive(pdf_filename, pdf_bytes, "application/pdf")
        except Exception as e:
            print(f"PDF Gen Error for {uid}: {e}")
            pdf_link = "Error Generating PDF"

        try:
            print(f"📊 Generating PPT for UID: {uid}...")
            ppt_bytes = ppt_generator.create_ppt_bytes(lesson_md)
            ppt_link = gs.upload_to_drive(
                ppt_filename,
                ppt_bytes,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            print(f"✅ PPT uploaded: {ppt_link}")
        except Exception as e:
            print(f"❌ PPT Gen Error for {uid}: {e}")
            ppt_link = "Error Generating PPT"

        # ── Step 9: Write results back to sheet ──────────────────────────────
        # Added ppt_link as the 4th column — update your sheet headers accordingly
        gs.append_output_data([uid, txt_link, pdf_link, ppt_link, timestamp])

        for item in items:
            gs.update_row_status(item["row_index"], "Yes")

        results_summary.append(f"UID {uid} processed successfully.")

    return {"processed": results_summary}
