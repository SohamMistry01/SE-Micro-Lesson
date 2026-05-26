import re
import json
import subprocess
import os
import tempfile


def parse_markdown_to_slides(lesson_md: str) -> dict:
    """
    Parses a lesson markdown string into a structured dict for the PPT generator.

    Rules:
    - First # heading  → presentation title
    - Each ## heading  → new slide
    - Bullet / numbered lines → slide bullet points (max 5 per slide to avoid overflow)
    - ![alt](path)     → image for that slide
    - *Figure: ...*    → caption for that image
    - Plain paragraphs → treated as a bullet if > 15 chars
    """
    lines = lesson_md.strip().split("\n")
    title = "Microlesson"
    slides = []
    current_slide = None

    def clean(text: str) -> str:
        """Strip markdown bold/italic/inline-code markers."""
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        return text.strip()

    for line in lines:
        stripped = line.strip()

        # ── Presentation title (H1) ──────────────────────────────────────────
        if re.match(r"^# (?!#)", stripped):
            title = clean(stripped[2:])

        # ── New slide (H2) ───────────────────────────────────────────────────
        elif re.match(r"^## ", stripped):
            if current_slide:
                slides.append(current_slide)
            current_slide = {
                "heading": clean(stripped[3:]),
                "bullets": [],
                "image_path": None,
                "image_caption": None,
            }

        # ── H3 sub-headings become bold bullets ──────────────────────────────
        elif re.match(r"^### ", stripped) and current_slide:
            current_slide["bullets"].append({"text": clean(stripped[4:]), "bold": True})

        # ── Image tag ────────────────────────────────────────────────────────
        elif stripped.startswith("![") and current_slide:
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
            if m:
                path = m.group(2).strip()
                # Resolve relative paths to absolute so Node can find them
                if not os.path.isabs(path):
                    path = os.path.abspath(path)
                current_slide["image_path"] = path

        # ── Figure caption ───────────────────────────────────────────────────
        elif re.match(r"^\*Figure:", stripped) and current_slide:
            current_slide["image_caption"] = clean(stripped.strip("*"))

        # ── Bullet / numbered list items ─────────────────────────────────────
        elif re.match(r"^[-*]\s+|^\d+\.\s+", stripped) and current_slide:
            # Remove the list marker
            text = re.sub(r"^[-*]\s+|^\d+\.\s+", "", stripped)
            text = clean(text)
            if text and len(current_slide["bullets"]) < 5:  # cap at 5 to avoid overflow
                current_slide["bullets"].append({"text": text, "bold": False})

        # ── Plain paragraphs → bullet if long enough ─────────────────────────
        elif stripped and current_slide and not stripped.startswith("#"):
            if not stripped.startswith("![") and not stripped.startswith("*Figure"):
                text = clean(stripped)
                if len(text) > 15 and len(current_slide["bullets"]) < 5:
                    current_slide["bullets"].append({"text": text, "bold": False})

    if current_slide:
        slides.append(current_slide)

    return {"title": title, "slides": slides}


def create_ppt_bytes(lesson_md: str, path: str) -> bytes:
    """
    Converts a markdown lesson string into PPTX bytes.
    Internally calls create_ppt.js via Node.js.
    """
    slide_data = parse_markdown_to_slides(lesson_md)

    # Write structured data to a temp JSON file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(slide_data, f, ensure_ascii=False, indent=2)
        json_path = f.name

    output_path = json_path.replace(".json", ".pptx")
    script_path = os.path.join(os.path.dirname(__file__), path)

    try:
        result = subprocess.run(
            ["node", script_path, json_path, output_path],
            capture_output=True,
            text=True,
            timeout=90,
            env={
                **os.environ,
                "NODE_PATH": os.path.expanduser("~/.npm-global/lib/node_modules"),
            },
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"PPT generation failed (exit {result.returncode}):\n{result.stderr}"
            )

        with open(output_path, "rb") as f:
            return f.read()

    finally:
        if os.path.exists(json_path):
            os.unlink(json_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
