import os
from typing import Dict, List

import pymupdf


def clean_pdf(pdf_dir: str = "pdfs") -> Dict[str, List[str]]:
    # Resolve the target directory to an absolute path for consistent behavior.
    dir_path = os.path.abspath(pdf_dir)
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"pdf directory not found: {dir_path}")

    processed = []
    skipped = []

    for filename in sorted(os.listdir(dir_path)):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(dir_path, filename)
        if not os.path.isfile(path):
            continue

        # Drop the first page and the last two pages, keep the middle pages.
        with pymupdf.open(path) as doc:
            total = doc.page_count
            if total <= 3:
                skipped.append(path)
                continue

            keep_from = 1
            keep_to = total - 3
            new_doc = pymupdf.open()
            tmp_path = f"{path}.tmp"
            try:
                new_doc.insert_pdf(doc, from_page=keep_from, to_page=keep_to)
                new_doc.save(tmp_path)
            finally:
                new_doc.close()

        # Replace the original file atomically to avoid partial writes.
        os.replace(tmp_path, path)
        processed.append(path)

    if not processed and not skipped:
        raise ValueError(f"no pdf files found in {dir_path}")

    return {"processed": processed, "skipped": skipped}

def main() -> None:
    original_dir = "pdfs"
    cleaned_data = clean_pdf(original_dir)
    print(cleaned_data)

if __name__ == "__main__":
    main()
