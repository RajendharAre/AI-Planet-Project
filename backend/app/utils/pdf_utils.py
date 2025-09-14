import fitz  # PyMuPDF

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = []
    for page in doc:
        text.append(page.get_text("text"))
    return "\n".join(text)
