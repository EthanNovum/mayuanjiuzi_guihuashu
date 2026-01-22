import argparse
import json
import os
import re
from typing import Dict, List


_MD_IMAGE_INLINE_RE = re.compile(r"!\[[^\]]*]\([^)]+\)")
_MD_IMAGE_REF_RE = re.compile(r"!\[[^\]]*]\[[^\]]+\]")
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
# Match HTML comments and extract content: <!-- text -->
_HTML_COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)
# Match other HTML tags (not comments)
_HTML_TAG_RE = re.compile(r"<(?!!--)/?[^>]+>")


def _extract_alt_text(match: re.Match) -> str:
    """Extract alt text from markdown image syntax ![alt](url)"""
    full_match = match.group(0)
    alt_match = re.search(r"!\[([^\]]*)\]", full_match)
    if alt_match:
        return alt_match.group(1)
    return ""


def _extract_comment_text(match: re.Match) -> str:
    """Extract text content from HTML comment <!-- text -->"""
    return match.group(1)


def clean_markdown_text(text: str) -> str:
    # Extract text from HTML comments (e.g., <!-- 心理学 --> becomes 心理学)
    text = _HTML_COMMENT_RE.sub(_extract_comment_text, text)
    text = _MD_IMAGE_INLINE_RE.sub(_extract_alt_text, text)
    text = _MD_IMAGE_REF_RE.sub(_extract_alt_text, text)
    text = _HTML_IMG_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    # Normalize whitespace: collapse multiple spaces/newlines into single space, then strip
    text = re.sub(r"\s+", " ", text).strip()
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


def iter_json_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    files = []
    for filename in sorted(os.listdir(input_dir)):
        if not filename.lower().endswith(".json"):
            continue
        path = os.path.join(input_dir, filename)
        if os.path.isfile(path):
            files.append(path)
    if not files:
        raise ValueError(f"no json files found in {input_dir}")
    return files


def extract_markdown(payload: dict, source: str) -> str:
    result = payload.get("result")
    if isinstance(result, dict):
        markdown = result.get("markdown")
        if isinstance(markdown, str) and markdown.strip():
            return markdown
    raise ValueError(f"no markdown content found in {source}")


def export_markdown_dir(input_dir: str, output_dir: str) -> Dict[str, List[str]]:
    os.makedirs(output_dir, exist_ok=True)
    processed: List[str] = []
    for path in iter_json_files(input_dir):
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        markdown = extract_markdown(payload, path)
        output_name = f"{os.path.splitext(os.path.basename(path))[0]}.md"
        output_path = os.path.join(output_dir, output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        processed.append(output_path)
    return {"processed": processed}


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
    parser.add_argument(
        "--export-json",
        action="store_true",
        help="Export markdown files from JSON results before cleaning",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export markdown from JSON and skip cleaning",
    )
    parser.add_argument(
        "--json-dir",
        default=os.path.join("pdf_result", "json"),
        help="Directory containing JSON files (default: pdf_result/json)",
    )
    parser.add_argument(
        "--md-output-dir",
        default=os.path.join("pdf_result", "md"),
        help="Directory to write exported markdown files (default: pdf_result/md)",
    )
    args = parser.parse_args()

    if args.export_json:
        export_result = export_markdown_dir(args.json_dir, args.md_output_dir)
        print(export_result)
        if args.export_only:
            return

    output_dir = args.output_dir or args.input_dir
    result = clean_markdown_dir(args.input_dir, output_dir)
    print(result)


if __name__ == "__main__":
    main()
