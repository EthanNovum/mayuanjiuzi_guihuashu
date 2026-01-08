import argparse
import os
import re
from typing import Dict, List


_MD_IMAGE_INLINE_RE = re.compile(r"!\[[^\]]*]\([^)]+\)")
_MD_IMAGE_REF_RE = re.compile(r"!\[[^\]]*]\[[^\]]+\]")
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"</?[^>]+>")


def clean_markdown_text(text: str) -> str:
    text = _MD_IMAGE_INLINE_RE.sub("", text)
    text = _MD_IMAGE_REF_RE.sub("", text)
    text = _HTML_IMG_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = re.sub(r"[\s]+", "",text)
    return text


def iter_md_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    files = []
    for filename in sorted(os.listdir(input_dir)):
        if not filename.lower().endswith(".md"):
            continue
        path = os.path.join(input_dir, filename)
        if os.path.isfile(path):
            files.append(path)
    if not files:
        raise ValueError(f"no markdown files found in {input_dir}")
    return files


def clean_markdown_dir(input_dir: str, output_dir: str) -> Dict[str, List[str]]:
    os.makedirs(output_dir, exist_ok=True)
    processed: List[str] = []
    for path in iter_md_files(input_dir):
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        cleaned_text = clean_markdown_text(raw_text)
        output_path = os.path.join(output_dir, os.path.basename(path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        processed.append(output_path)
    return {"processed": processed}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove HTML tags and images from Markdown files."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=os.path.join("pdf_result", "md"),
        help="Directory containing markdown files (default: pdf_result/md)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for cleaned files (default: in-place)",
    )
    args = parser.parse_args()

    output_dir = args.output_dir or args.input_dir
    result = clean_markdown_dir(args.input_dir, output_dir)
    print(result)


if __name__ == "__main__":
    main()
