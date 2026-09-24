import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoadError(Exception):
    pass


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


READERS = {".txt": _read_txt, ".pdf": _read_pdf, ".docx": _read_docx}


def list_documents(data_dir: Path, extensions: list[str]) -> list[Path]:
    if not data_dir.is_dir():
        raise DocumentLoadError(f"Data folder not found: {data_dir}")
    allowed = {e.lower() for e in extensions} & READERS.keys()
    files = sorted(p for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed)
    skipped = [p.name for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() not in allowed]
    if skipped:
        logger.warning("Skipping unsupported files: %s", ", ".join(skipped))
    return files


def load_document(path: Path) -> str:
    try:
        text = READERS[path.suffix.lower()](path)
    except Exception as e:
        raise DocumentLoadError(f"Failed to read {path.name}: {e}") from e
    text = text.strip()
    if not text:
        raise DocumentLoadError(f"No text content found in {path.name}")
    return text
