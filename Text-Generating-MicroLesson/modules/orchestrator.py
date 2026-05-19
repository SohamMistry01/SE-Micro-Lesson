import requests
import io
import re
import PyPDF2
from typing import Optional
from datetime import datetime
from collections import defaultdict
from modules.config import settings
from modules import google_services as gs
from modules import rag_engine
from modules import pdf_generator
from modules.prompt_config import get_resolved_prompt


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

    # Process Rows
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

    # Process each UID
    for uid, items in tasks.items():
        print(f"\nProcessing UID: {uid}...")

        contents = []
        for item in items:
            text = fetch_content_smart(item["content_data"])
            # ✅ FIX 1: Strict check to ensure the text isn't just empty space
            if text and text.strip():
                contents.append(text.strip())
            else:
                print(
                    f"   ⚠️ Warning: Extracted text is completely empty. If this is a PDF, it may be a scanned image with no readable text layer."
                )

        # ✅ FIX 2: If ALL files for this UID were empty, skip cleanly
        if not contents:
            print(f"Skipping {uid}: No valid textual content found or extracted.")
            continue

        # Run RAG Engine
        lesson_md = rag_engine.run_rag_pipeline(
            contents=contents,
            category=category,
            priority_llm=priority_llm,
            prompt_template=resolved_prompt,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if filename_pattern:
            base_name = filename_pattern.replace("{uid}", str(uid)).replace(
                "{timestamp}", timestamp
            )
            if "{uid}" not in filename_pattern and len(tasks) > 1:
                base_name = f"{base_name}_{uid}"
            txt_filename = f"{base_name}.txt"
            pdf_filename = f"{base_name}.pdf"
        else:
            txt_filename = f"{uid}_{timestamp}.txt"
            pdf_filename = f"{uid}_{timestamp}.pdf"

        txt_link = gs.upload_to_drive(
            txt_filename, lesson_md.encode("utf-8"), "text/plain"
        )

        try:
            pdf_bytes = pdf_generator.create_pdf_bytes(lesson_md, final_template_path)
            pdf_link = gs.upload_to_drive(pdf_filename, pdf_bytes, "application/pdf")
        except Exception as e:
            print(f"PDF Gen Error for {uid}: {e}")
            pdf_link = "Error Generating PDF"

        gs.append_output_data([uid, txt_link, pdf_link, timestamp])

        for item in items:
            gs.update_row_status(item["row_index"], "Yes")

        results_summary.append(f"UID {uid} processed successfully.")

    return {"processed": results_summary}
