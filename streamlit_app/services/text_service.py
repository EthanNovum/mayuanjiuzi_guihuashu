"""
文本处理服务
封装 clean_md 功能
"""
import re
from typing import Dict, List


# 正则表达式模式
_MD_IMAGE_INLINE_RE = re.compile(r"!\[[^\]]*]\([^)]+\)")
_MD_IMAGE_REF_RE = re.compile(r"!\[[^\]]*]\[[^\]]+\]")
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_HTML_COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<(?!--)[^>]+>")


def _extract_alt_text(match: re.Match) -> str:
    """从 Markdown 图片语法中提取 alt 文本"""
    full_match = match.group(0)
    alt_match = re.search(r"!\[([^\]]*)\]", full_match)
    if alt_match:
        return alt_match.group(1)
    return ""


def _extract_comment_text(match: re.Match) -> str:
    """从 HTML 注释中提取文本内容"""
    return match.group(1)


def clean_markdown_text(text: str, preserve_structure: bool = False) -> str:
    """
    清理 Markdown 文本

    Args:
        text: 原始 Markdown 文本
        preserve_structure: 是否保留段落结构

    Returns:
        清理后的文本
    """
    # 提取 HTML 注释中的文本
    text = _HTML_COMMENT_RE.sub(_extract_comment_text, text)

    # 替换图片为 alt 文本
    text = _MD_IMAGE_INLINE_RE.sub(_extract_alt_text, text)
    text = _MD_IMAGE_REF_RE.sub(_extract_alt_text, text)

    # 移除 HTML img 标签
    text = _HTML_IMG_RE.sub("", text)

    # 移除其他 HTML 标签
    text = _HTML_TAG_RE.sub("", text)

    if preserve_structure:
        # 保留段落结构，只压缩多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        # 压缩所有空白为单个空格
        text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_markdown_batch(
    items: List[Dict],
    preserve_structure: bool = False
) -> List[Dict]:
    """
    批量清理 Markdown 文本

    Args:
        items: 包含 markdown 字段的字典列表
        preserve_structure: 是否保留段落结构

    Returns:
        处理后的字典列表
    """
    results = []
    for item in items:
        new_item = dict(item)
        if "markdown" in new_item and new_item["markdown"]:
            new_item["markdown"] = clean_markdown_text(
                new_item["markdown"],
                preserve_structure=preserve_structure
            )
            new_item["cleaned"] = True
        results.append(new_item)
    return results


def get_text_stats(text: str) -> Dict:
    """
    获取文本统计信息

    Returns:
        统计信息字典
    """
    if not text:
        return {
            "char_count": 0,
            "word_count": 0,
            "line_count": 0,
            "paragraph_count": 0,
        }

    lines = text.split("\n")
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    # 中文字符计数
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    # 英文单词计数
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    return {
        "char_count": len(text),
        "chinese_chars": chinese_chars,
        "english_words": english_words,
        "line_count": len(lines),
        "paragraph_count": len(paragraphs),
    }
