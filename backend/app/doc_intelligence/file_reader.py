"""Read text from PDF, DOCX, TXT, CSV files."""
import csv
import io
from pathlib import Path
from typing import Tuple


def read_file(file_path: str) -> Tuple[str, int]:
    """
    Extract plain text from any supported file.
    Returns (text, page_count).
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(file_path)
    elif suffix == ".docx":
        return _read_docx(file_path)
    elif suffix == ".txt":
        return _read_txt(file_path)
    elif suffix == ".csv":
        return _read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _read_pdf(path: str) -> Tuple[str, int]:
    try:
        import PyPDF2
        pages = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages), len(pages)
    except Exception:
        # Fallback: try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages), len(pages)
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")


def _read_docx(path: str) -> Tuple[str, int]:
    from docx import Document
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs), 1


def _read_txt(path: str) -> Tuple[str, int]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return text, 1


def _read_csv(path: str) -> Tuple[str, int]:
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
    return "\n".join(rows), 1
