import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()