"""Split data.txt into individual complaint files (.txt or .docx) inside data/."""
from pathlib import Path

from docx import Document

BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "data.txt"
DATA_DIR = BASE_DIR / "data"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for block in SOURCE.read_text(encoding="utf-8").split("====="):
        header, _, body = block.strip().partition("\n")
        path = DATA_DIR / header.removeprefix("###").strip()
        if path.suffix == ".docx":
            doc = Document()
            for line in body.strip().splitlines():
                doc.add_paragraph(line)
            doc.save(str(path))
        else:
            path.write_text(body.strip() + "\n", encoding="utf-8")
        print(f"Created {path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
