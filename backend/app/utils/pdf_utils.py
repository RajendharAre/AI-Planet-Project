import fitz  # PyMuPDF

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes using PyMuPDF"""
    try:
        # Open PDF from bytes
        doc = fitz.Document(stream=file_bytes, filetype="pdf")
        text = []
        
        # Extract text from each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text.append(page.get_text())
        
        doc.close()
        return "\n".join(text)
        
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
