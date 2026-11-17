import io, re
import fitz
from PIL import Image

def pdf_pages(data: bytes) -> list:
    doc = fitz.open(stream=data, filetype="pdf"); out = []
    for i, p in enumerate(doc, 1):
        txt = p.get_text("text").strip()
        if len(txt) < 30:   # scanned page -> OCR fallback
            try:
                import pytesseract
                txt = pytesseract.image_to_string(Image.open(io.BytesIO(p.get_pixmap(dpi=200).tobytes("png"))))
            except Exception: txt = ""
        out.append((i, txt))
    return out

def image_text(data: bytes) -> str:
    try:
        import pytesseract; return pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    except Exception: return ""

def chunk(pages: list, size: int = 500, overlap: int = 80) -> list:
    chunks = []
    for pg, txt in pages:
        cur = ""
        for s in re.split(r"(?<=[.!?\n])\s+", txt):
            if len(cur) + len(s) > size and cur:
                chunks.append({"text": cur.strip(), "page": pg}); cur = cur[-overlap:]
            cur += " " + s
        if cur.strip(): chunks.append({"text": cur.strip(), "page": pg})
    return chunks
