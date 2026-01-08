import argparse
import json
import os
import re
from typing import Dict, Iterable, List, Optional

import requests


class OCRClient:
    def __init__(self, app_id: str, secret_code: str):
        self.app_id = app_id
        self.secret_code = secret_code

    def recognize(self, file_content: bytes, options: Dict[str, object]) -> str:
        params = {key: str(value) for key, value in options.items() if value is not None}
        headers = {
            "x-ti-app-id": self.app_id,
            "x-ti-secret-code": self.secret_code,
            "x-ti-client-source": "sample-code-v1.0",
            "Content-Type": "application/octet-stream",
        }
        response = requests.post(
            "https://api.textin.com/ai/service/v1/pdf_to_markdown",
            params=params,
            headers=headers,
            data=file_content,
            timeout=120,
        )
        response.raise_for_status()
        return response.text


_BLANK_LINES_RE = re.compile(r"\n{3,}")


def load_env_file(env_path: Optional[str]) -> Dict[str, str]:
    if not env_path:
        return {}
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"env file not found: {env_path}")
    values: Dict[str, str] = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def normalize_markdown(text: str) -> str:
    text = text.strip()
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def build_markdown_from_detail(detail: Iterable[Dict[str, object]]) -> str:
    items: List[str] = []
    for idx, item in enumerate(detail):
        raw_text = (item.get("text") or "").strip()
        if not raw_text:
            continue
        outline_level = item.get("outline_level")
        sub_type = str(item.get("sub_type") or "").lower()
        is_title = "title" in sub_type
        if is_title:
            level = 1
            if isinstance(outline_level, int) and outline_level >= 0:
                level = min(6, outline_level + 1)
            items.append(f"{'#' * level} {raw_text}")
        else:
            items.append(raw_text)
    return normalize_markdown("\n\n".join(items))


def build_markdown_from_pages(pages: Iterable[Dict[str, object]]) -> str:
    chunks: List[str] = []
    for page in sorted(pages, key=lambda p: p.get("page_id", 0)):
        content = page.get("content") or []
        lines: List[str] = []
        for item in content:
            text = (item.get("text") or "").strip()
            if text:
                lines.append(text)
        if lines:
            chunks.append("\n".join(lines))
    return normalize_markdown("\n\n".join(chunks))


def build_markdown_from_result(result_json: Dict[str, object]) -> str:
    result = result_json.get("result") or {}
    detail = result.get("detail") or []
    if isinstance(detail, list) and detail:
        return build_markdown_from_detail(detail)
    pages = result.get("pages") or []
    if isinstance(pages, list) and pages:
        return build_markdown_from_pages(pages)
    markdown = result.get("markdown") or ""
    if isinstance(markdown, str) and markdown.strip():
        return normalize_markdown(markdown)
    return ""


def build_markdown_from_json_file(json_path: str) -> str:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"json file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"json root is not an object: {json_path}")
    return build_markdown_from_result(data)


def write_markdown_from_json(json_path: str, md_path: str) -> None:
    markdown_text = build_markdown_from_json_file(json_path)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)


def iter_jsons(input_dir: str) -> List[str]:
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


def iter_pdfs(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    files = []
    for filename in sorted(os.listdir(input_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(input_dir, filename)
        if os.path.isfile(path):
            files.append(path)
    if not files:
        raise ValueError(f"no pdf files found in {input_dir}")
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDFs to JSON and Markdown.")
    parser.add_argument("input_dir", help="Directory containing PDF files")
    parser.add_argument(
        "--output-root",
        default="pdf_result",
        help="Root directory for output (default: pdf_result)",
    )
    parser.add_argument("--env", default=None, help="Optional env file path")
    parser.add_argument("--app-id", default=None, help="TextIn app id")
    parser.add_argument("--secret-code", default=None, help="TextIn secret code")
    parser.add_argument("--dpi", type=int, default=144, help="DPI for OCR")
    parser.add_argument(
        "--parse-mode", default="auto", help="TextIn parse mode (default: auto)"
    )
    parser.add_argument(
        "--table-flavor", default="html", help="Table flavor (default: html)"
    )
    parser.add_argument(
        "--from-json",
        default=None,
        help="Directory containing JSON files to convert into markdown",
    )
    args = parser.parse_args()

    output_root = args.output_root
    json_dir = os.path.join(output_root, "json")
    md_dir = os.path.join(output_root, "md")
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    options = {
        "dpi": args.dpi,
        "get_image": "objects",
        "markdown_details": 1,
        "parse_mode": args.parse_mode,
        "table_flavor": args.table_flavor,
    }

    if args.from_json:
        json_files = iter_jsons(args.from_json)
        for json_path in json_files:
            filename = os.path.basename(json_path)
            base_name = os.path.splitext(filename)[0]
            md_path = os.path.join(md_dir, f"{base_name}.md")
            if os.path.exists(md_path):
                print(f"{filename} 已存在 -> {md_path}，跳过")
                continue
            try:
                write_markdown_from_json(json_path, md_path)
                print(f"{filename} 处理完成 -> {md_path}")
            except Exception as exc:
                print(f"{filename} 处理出错: {exc}")
        return

    env_values = load_env_file(args.env)
    app_id = args.app_id or env_values.get("TEXTIN_APP_ID") or os.getenv("TEXTIN_APP_ID")
    secret_code = (
        args.secret_code
        or env_values.get("TEXTIN_SECRET_CODE")
        or os.getenv("TEXTIN_SECRET_CODE")
    )
    if not app_id or not secret_code:
        raise ValueError("TEXTIN_APP_ID/TEXTIN_SECRET_CODE are required")

    client = OCRClient(app_id, secret_code)
    pdf_files = iter_pdfs(args.input_dir)
    pdf_files = pdf_files[:]

    for path in pdf_files:
        filename = os.path.basename(path)
        base_name = os.path.splitext(filename)[0]
        md_path = os.path.join(md_dir, f"{base_name}.md")
        if os.path.exists(md_path):
            print(f"{filename} 已存在 -> {md_path}，跳过")
            continue
        with open(path, "rb") as f:
            file_content = f.read()
        try:
            response_text = client.recognize(file_content, options)
            json_path = os.path.join(json_dir, f"{base_name}.json")
            with open(json_path, "w", encoding="utf-8") as fw:
                fw.write(response_text)
            result_json = json.loads(response_text)
            markdown_text = build_markdown_from_result(result_json)
            with open(md_path, "w", encoding="utf-8") as fw:
                fw.write(markdown_text)
            print(f"{filename} 处理完成 -> {md_path}")
        except Exception as exc:
            print(f"{filename} 处理出错: {exc}")


if __name__ == "__main__":
    main()
