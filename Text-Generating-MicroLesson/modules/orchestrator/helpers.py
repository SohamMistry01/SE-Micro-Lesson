import os
import re
import io
import requests
import json
import PyPDF2
from collections import defaultdict
from typing import Optional, Dict, List, Tuple
from .. import image_generator
from .. import google_services as gs
from .. import rag_engine
from ..ppt_generator import ppt_generator
from .. import pdf_generator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from modules.config import settings

# ==========================================
# Core Utility Functions
# ==========================================


def save_generated_image(prompt: str, output_path: str) -> bool:
    """
    Calls the SDXL pipeline, extracts the raw bytes, and saves them locally.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"Generating SDXL Turbo image for prompt: '{prompt[:50]}...'")
        img_bytes = image_generator.generate_image(prompt=prompt, steps=1, seed=42)

        with open(output_path, "wb") as f:
            f.write(img_bytes)

        print(f"Image successfully saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to generate or save image: {e}")
        return False

def extract_drive_id(url: str) -> Optional[str]:
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    
    match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
        
    return None



def _fetch_content_smart(content_cell: str) -> str:
    """
    Intelligently extracts text from direct text, Google Docs, Drive PDFs, or Web PDFs.
    """
    content_cell = str(content_cell).strip()
    if not content_cell:
        return ""

    # 1. Direct Text (If it doesn't look like a URL, treat it as raw text)
    if not content_cell.startswith(("http://", "https://", "www.")):
        print("Detected Direct Text Content.")
        return content_cell

    # 2. Google Drive Links (Docs, PDFs, TXT)
    if "drive.google.com" in content_cell or "docs.google.com" in content_cell:
        file_id = extract_drive_id(content_cell)
        if file_id:
            print(f"Detected Drive Link. Parsing ID: {file_id}")
            return gs.get_and_parse_drive_file(file_id)
        else:
            print(f"Warning: Could not extract ID from Drive URL: {content_cell}")
            return ""

    # 3. Standard Web URLs (Direct PDF links or Text files)
    try:
        response = requests.get(content_cell)
        response.raise_for_status()

        # Check if the URL is a standard Web PDF
        if content_cell.lower().endswith(".pdf") or "application/pdf" in response.headers.get("Content-Type", ""):
            print("   Detected standard Web PDF. Parsing...")
            pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(response.content))
            extracted_text = []

            for i in range(pdf_reader.getNumPages()):
                page = pdf_reader.getPage(i)
                text = page.extractText()
                if text:
                    extracted_text.append(text)
            return "\n".join(extracted_text)

        print("Detected standard Web content.")
        return response.text
    except Exception as e:
        print(f"Error fetching URL {content_cell}: {e}")
        return ""



def _fetch_pending_tasks() -> Optional[Dict[str, List[Dict]]]:
    """Fetches data from Google Sheets and groups pending tasks by UID."""
    rows = gs.fetch_input_data()
    if not rows:
        return None

    data_rows = rows[1:]
    tasks = defaultdict(list)

    for i, row in enumerate(data_rows):
        sheet_row_index = i + 2
        if len(row) < 3:
            continue
            
        uid, content_cell, status = row[0], row[1], row[2]

        if status.strip().lower() == "no":
            tasks[uid].append({
                "row_index": sheet_row_index, 
                "content_data": content_cell
            })
            
    return tasks





# ==========================================
# Microlesson Workflow Helpers
# ==========================================



def _plan_and_generate_images(uid: str, contents: List[str], priority_llm: Optional[str], timestamp: str, no_of_images: int = 2) -> str:
    if no_of_images <= 0:
        return ""
        
    print(f"Planning {no_of_images} visual illustrations for UID: {uid}...")

    clean_context = "\n\n".join(contents)
    # Optional: Truncate context if it's massively huge to save tokens for the prompt
    clean_context = clean_context[:20000] 

    image_planning_query = (
        f"Based on the following document context, identify {no_of_images} sections that would benefit "
        f"from a simple visual diagram or illustration.\n\n"
        f"STRICT RULES for the image prompts:\n"
        f"- Maximum 10 words per prompt.\n"
        f"- NEVER ask for timelines, or charts — SDXL cannot render those.\n"
        f"- Only describe physical, concrete objects or simple scenes "
        f"(e.g. 'army soldiers marching battlefield', 'cannon fire smoke field', "
        f"'old ship ocean sailing', 'ancient crown throne room').\n"
        f"- Use nouns and adjectives only. No verbs, no sentences.\n\n"
        f"Return your answer EXACTLY as a valid JSON array containing exactly {no_of_images} objects. "
        f"Do not include any conversational text or markdown. Each object must have exactly these two keys:\n"
        f"1. \"description\": One sentence on where/why this image fits.\n"
        f"2. \"prompt\": The max 10-word physical scene prompt.\n\n"
        f"Example format:\n"
        f"[\n"
        f"  {{\"description\": \"Fits in the intro to show setting.\", \"prompt\": \"ancient castle ruins foggy mountains\"}}\n"
        f"]\n\n"
        f"Context:\n{clean_context}"
    )

    # 1. FIX: Call the LLM directly, skipping the summarization pipeline
    try:
        # Use a low temperature (0.1) to force strict JSON compliance
        model_to_use = priority_llm if priority_llm else "llama-3.3-70b-versatile"
        llm = ChatGroq(model=model_to_use, temperature=0.1, api_key=settings.GROQ_API_KEY)
        direct_prompt = ChatPromptTemplate.from_template("{query}")
        chain = direct_prompt.pipe(llm).pipe(StrOutputParser())
        
        raw_image_plan = chain.invoke({"query": image_planning_query})
    except Exception as e:
        print(f"Error during direct LLM call for image planning: {e}")
        return ""

    # 2. Clean the LLM output
    cleaned_plan = raw_image_plan.strip()
    if cleaned_plan.startswith("```json"):
        cleaned_plan = cleaned_plan[7:]
    elif cleaned_plan.startswith("```"):
        cleaned_plan = cleaned_plan[3:]
        
    if cleaned_plan.endswith("```"):
        cleaned_plan = cleaned_plan[:-3]
        
    cleaned_plan = cleaned_plan.strip()

    image_injection_instructions = ""

    # 3. Parse JSON
    try:
        image_data = json.loads(cleaned_plan)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from LLM: {e}\nRaw Output: {raw_image_plan}")
        return image_injection_instructions

    if not isinstance(image_data, list):
        print("Warning: LLM did not return a JSON array.")
        return image_injection_instructions
        
    image_data = image_data[:no_of_images]

    # 4. Generate Images
    for i, img_obj in enumerate(image_data, 1):
        desc = img_obj.get("description", "")
        prompt = img_obj.get("prompt", "")

        if not desc or not prompt:
            print(f"Warning: Missing data for image {i}, skipping.")
            continue

        safe_prompt = " ".join(prompt.strip().split()[:10])
        path = f"./temp/{uid}_{timestamp}_img{i}.png"

        if save_generated_image(safe_prompt, path):
            image_injection_instructions += (
                f"\n- Image {i} File Path: {path}\n"
                f"  Context/Description: {desc.strip()}\n"
            )

    return image_injection_instructions



def _build_extended_prompt(resolved_prompt: str, image_instructions: str) -> str:
    """Appends strict image layout instructions to the primary LLM prompt if images exist."""
    if not image_instructions:
        return resolved_prompt
        
    return resolved_prompt + (
        f"\n\nMANDATORY IMAGE PLACEMENT RULES — follow exactly:\n"
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
        f"Available assets:\n{image_instructions}"
    )



def _generate_filenames(uid: str, timestamp: str, filename_pattern: Optional[str], total_tasks: int) -> Tuple[str, str, str]:
    """Generates the filenames for the txt, pdf, and pptx assets based on the provided pattern."""
    if filename_pattern:
        base_name = filename_pattern.replace("{uid}", str(uid)).replace("{timestamp}", timestamp)
        if "{uid}" not in filename_pattern and total_tasks > 1:
            base_name = f"{base_name}_{uid}"
        return f"{base_name}.txt", f"{base_name}.pdf", f"{base_name}.pptx"
        
    return f"{uid}_{timestamp}.txt", f"{uid}_{timestamp}.pdf", f"{uid}_{timestamp}.pptx"



def _generate_and_upload_assets(uid: str, lesson_md: str, txt_name: str, pdf_name: str, ppt_name: str, pdf_template_path: str, ppt_template_path: str) -> Tuple[str, str, str]:
    """Handles generating and uploading the text, PDF, and PPT files to Google Drive."""
    # Upload TXT
    txt_link = gs.upload_to_drive(txt_name, lesson_md.encode("utf-8"), "text/plain")

    # Generate & Upload PDF
    try:
        pdf_bytes = pdf_generator.create_pdf_bytes(lesson_md, pdf_template_path)
        pdf_link = gs.upload_to_drive(pdf_name, pdf_bytes, "application/pdf")
    except Exception as e:
        print(f"PDF Gen Error for {uid}: {e}")
        pdf_link = "Error Generating PDF"

    # Generate & Upload PPT
    try:
        print(f"Generating PPT for UID: {uid}...")
        ppt_bytes = ppt_generator.create_ppt_bytes(lesson_md, ppt_template_path)
        ppt_link = gs.upload_to_drive(
            ppt_name,
            ppt_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        print(f"PPT uploaded: {ppt_link}")
    except Exception as e:
        print(f"PPT Gen Error for {uid}: {e}")
        ppt_link = "Error Generating PPT"

    return txt_link, pdf_link, ppt_link