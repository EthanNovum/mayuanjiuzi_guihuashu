"""
PDF 处理服务
封装 trim_pdf 和 ocr_pdf 功能
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加父目录以导入现有模块
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

try:
    import pymupdf
except ImportError:
    pymupdf = None


def trim_pdf_bytes(
    pdf_bytes: bytes,
    trim_first: int = 1,
    trim_last: int = 2
) -> Tuple[bytes, Dict]:
    """
    裁剪 PDF 页面

    Args:
        pdf_bytes: PDF 文件字节
        trim_first: 删除前 N 页
        trim_last: 删除后 N 页

    Returns:
        (处理后的 PDF 字节, 处理信息)
    """
    if pymupdf is None:
        raise ImportError("pymupdf 未安装，请运行: pip install pymupdf")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
        tmp_in.write(pdf_bytes)
        tmp_in_path = tmp_in.name

    try:
        with pymupdf.open(tmp_in_path) as doc:
            total_pages = doc.page_count
            info = {
                "original_pages": total_pages,
                "trim_first": trim_first,
                "trim_last": trim_last,
            }

            # 检查是否有足够页面可裁剪
            min_pages = trim_first + trim_last + 1
            if total_pages < min_pages:
                info["skipped"] = True
                info["reason"] = f"页数不足（{total_pages} 页，至少需要 {min_pages} 页）"
                info["final_pages"] = total_pages
                return pdf_bytes, info

            # 计算保留的页面范围
            keep_from = trim_first
            keep_to = total_pages - trim_last - 1

            # 创建新文档
            new_doc = pymupdf.open()
            new_doc.insert_pdf(doc, from_page=keep_from, to_page=keep_to)

            # 保存到字节
            output_bytes = new_doc.tobytes()
            new_doc.close()

            info["skipped"] = False
            info["final_pages"] = keep_to - keep_from + 1

            return output_bytes, info

    finally:
        os.unlink(tmp_in_path)


def ocr_pdf_to_markdown(
    pdf_bytes: bytes,
    app_id: str,
    secret_code: str,
    dpi: int = 144,
    parse_mode: str = "auto",
    table_flavor: str = "html"
) -> Tuple[str, Dict]:
    """
    使用 TextIn OCR 将 PDF 转换为 Markdown

    Args:
        pdf_bytes: PDF 文件字节
        app_id: TextIn App ID
        secret_code: TextIn Secret Code
        dpi: OCR DPI
        parse_mode: 解析模式
        table_flavor: 表格格式

    Returns:
        (Markdown 文本, OCR 结果信息)
    """
    import json
    import requests
    import re

    params = {
        "dpi": str(dpi),
        "get_image": "objects",
        "markdown_details": "1",
        "parse_mode": parse_mode,
        "table_flavor": table_flavor,
    }

    headers = {
        "x-ti-app-id": app_id,
        "x-ti-secret-code": secret_code,
        "x-ti-client-source": "streamlit-app-v1.0",
        "Content-Type": "application/octet-stream",
    }

    response = requests.post(
        "https://api.textin.com/ai/service/v1/pdf_to_markdown",
        params=params,
        headers=headers,
        data=pdf_bytes,
        timeout=120,
    )
    response.raise_for_status()

    result_json = response.json()
    info = {
        "code": result_json.get("code"),
        "message": result_json.get("message"),
    }

    # 从结果中提取 Markdown
    result = result_json.get("result", {})

    # 优先使用 detail
    detail = result.get("detail", [])
    if isinstance(detail, list) and detail:
        markdown = _build_markdown_from_detail(detail)
        info["source"] = "detail"
        return markdown, info

    # 其次使用 pages
    pages = result.get("pages", [])
    if isinstance(pages, list) and pages:
        markdown = _build_markdown_from_pages(pages)
        info["source"] = "pages"
        return markdown, info

    # 最后使用 markdown 字段
    markdown = result.get("markdown", "")
    if isinstance(markdown, str) and markdown.strip():
        info["source"] = "markdown"
        return _normalize_markdown(markdown), info

    raise ValueError("OCR 结果中未找到有效内容")


def _normalize_markdown(text: str) -> str:
    """规范化 Markdown 文本"""
    import re
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_markdown_from_detail(detail: list) -> str:
    """从 detail 构建 Markdown"""
    items = []
    for item in detail:
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
    return _normalize_markdown("\n\n".join(items))


def _build_markdown_from_pages(pages: list) -> str:
    """从 pages 构建 Markdown"""
    chunks = []
    for page in sorted(pages, key=lambda p: p.get("page_id", 0)):
        content = page.get("content", [])
        lines = []
        for item in content:
            text = (item.get("text") or "").strip()
            if text:
                lines.append(text)
        if lines:
            chunks.append("\n".join(lines))
    return _normalize_markdown("\n\n".join(chunks))


def process_pdf_file(
    file_bytes: bytes,
    filename: str,
    app_id: str,
    secret_code: str,
    trim_enabled: bool = True,
    trim_first: int = 1,
    trim_last: int = 2,
    dpi: int = 144,
    parse_mode: str = "auto"
) -> Dict:
    """
    处理单个 PDF 文件的完整流程

    Returns:
        处理结果字典
    """
    result = {
        "filename": filename,
        "status": "processing",
        "markdown": "",
        "trim_info": None,
        "ocr_info": None,
        "error": None,
    }

    try:
        # 步骤 1: 裁剪 PDF（可选）
        if trim_enabled:
            file_bytes, trim_info = trim_pdf_bytes(file_bytes, trim_first, trim_last)
            result["trim_info"] = trim_info

        # 步骤 2: OCR 转换
        markdown, ocr_info = ocr_pdf_to_markdown(
            file_bytes,
            app_id=app_id,
            secret_code=secret_code,
            dpi=dpi,
            parse_mode=parse_mode
        )

        result["markdown"] = markdown
        result["ocr_info"] = ocr_info
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result
