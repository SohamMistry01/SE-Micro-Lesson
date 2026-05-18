import io
import os
import markdown
from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader

# Margins
TOP_MARGIN = "140pt"    
BOTTOM_MARGIN = "100pt" 
SIDE_MARGIN = "60pt"

def sanitize_text(text: str) -> str:
    """
    Aggressively cleans text to ensure PDF compatibility.
    1. Replaces known 'fancy' characters with standard ASCII equivalents.
    2. Strips any remaining non-standard characters that cause 'blocks'.
    """
    # 1. Specific replacements for common LLM artifacts
    replacements = {
        "–": "-",  # En-dash 
        "‑": "-",
        "—": "-",  # Em-dash
        "’": "'",  # Smart quote
        "‘": "'",  # Smart quote
        "“": '"',  # Smart double quote
        "”": '"',  # Smart double quote
        "…": "...", # Ellipsis
        "•": "*",  # Bullet point (sometimes causes issues)
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # 2. Aggressive ASCII normalization
    # This encodes to ASCII (ignoring errors) and decodes back.
    # It removes any invisible/weird characters that the font can't render.
    text = text.encode("ascii", "ignore").decode("ascii")
    
    return text

def create_pdf_bytes(markdown_content: str, template_path: str) -> bytes:
    """
    Generates a PDF in memory with the template overlay.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    # 1. Sanitize the text to remove 'strange blocks'
    cleaned_content = sanitize_text(markdown_content)

    # 2. HTML Conversion
    # Removed 'codehilite' to prevent xhtml2pdf rendering bugs with complex spans
    html_body = markdown.markdown(cleaned_content, extensions=['extra', 'sane_lists'])
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: a4 portrait;
                margin-top: {TOP_MARGIN};
                margin-bottom: {BOTTOM_MARGIN};
                margin-left: {SIDE_MARGIN};
                margin-right: {SIDE_MARGIN};
                background-color: transparent;
            }}
            body {{ 
                font-family: Helvetica, sans-serif; 
                font-size: 11pt; 
                background-color: transparent; 
                color: #333333;
            }}
            h1 {{ color: #2E3E4E; border-bottom: 2px solid #2E3E4E; padding-bottom: 5px; }}
            h2 {{ color: #2E3E4E; margin-top: 20px; }}
            h3 {{ color: #2E3E4E; margin-top: 15px; }}
            p {{ line-height: 1.5; text-align: justify; margin-bottom: 10px; }}
            ul, ol {{ line-height: 1.5; margin-bottom: 10px; }}
            li {{ margin-bottom: 5px; }}
            
            /* --- FIX 1: TABLE STYLES --- */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #777777;
                padding: 8px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #e0e0e0;
                font-weight: bold;
            }}

            /* --- FIX 2: INLINE CODE (Replaces Pink Color) --- */
            code {{
                font-family: 'Courier New', Courier, monospace;
                color: #2c3e50; /* Dark slate instead of pink */
                background-color: #f4f6f7;
                border: 1px solid #dcdcdc;
                padding: 2px 4px;
                border-radius: 3px;
                font-size: 10.5pt;
            }}
            
            /* --- FIX 3: CODE BLOCKS (Indentation & Spacing) --- */
            pre {{
                background-color: #f8f9fa;
                padding: 12px;
                margin: 15px 0;
                border: 1px solid #cccccc;
                border-left: 4px solid #4a90e2; /* Nice blue accent line */
                font-family: 'Courier New', Courier, monospace;
                font-size: 10pt;
                
                /* CRITICAL: Forces code alignment to left, overriding the global p text-align: justify */
                text-align: left; 
                
                white-space: pre-wrap; 
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            
            /* Reset inline code styles when inside a pre block */
            pre code {{
                background-color: transparent;
                border: none;
                padding: 0;
                color: #333333;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    content_pdf_buffer = io.BytesIO()
    
    # encoding='utf-8' ensures special characters are handled correctly
    pisa_status = pisa.CreatePDF(
        src=html_template, 
        dest=content_pdf_buffer,
        encoding='utf-8'
    )
    
    if pisa_status.err:
        raise Exception("Error generating HTML PDF")

    # 3. Merge Logic (Template UNDER Text)
    content_pdf_buffer.seek(0)
    content_reader = PdfReader(content_pdf_buffer)
    template_reader = PdfReader(template_path)
    writer = PdfWriter()

    bg_page = template_reader.pages[0]

    for content_page in content_reader.pages:
        content_page.merge_page(bg_page, over=False)
        writer.add_page(content_page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()