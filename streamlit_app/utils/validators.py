"""
输入验证模块
"""
import os
from typing import Tuple, Optional


def validate_api_key(key: str, provider: str) -> Tuple[bool, str]:
    """
    验证 API Key 格式

    Returns:
        (is_valid, message)
    """
    if not key or not key.strip():
        return False, f"{provider} API Key 不能为空"

    key = key.strip()

    # 基本长度检查
    if len(key) < 10:
        return False, f"{provider} API Key 格式无效（太短）"

    # 特定提供商格式检查
    if provider.upper() == "OPENAI":
        if not key.startswith("sk-"):
            return False, "OpenAI API Key 应以 'sk-' 开头"

    return True, "验证通过"


def validate_file(file, allowed_extensions: list = None, max_size_mb: int = 50) -> Tuple[bool, str]:
    """
    验证上传文件

    Returns:
        (is_valid, message)
    """
    if file is None:
        return False, "未选择文件"

    # 检查文件扩展名
    if allowed_extensions:
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return False, f"不支持的文件格式，仅支持：{', '.join(allowed_extensions)}"

    # 检查文件大小
    file_size_mb = file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"文件过大（{file_size_mb:.1f}MB），最大支持 {max_size_mb}MB"

    return True, "验证通过"


def validate_pdf(file) -> Tuple[bool, str]:
    """验证 PDF 文件"""
    return validate_file(file, allowed_extensions=[".pdf"], max_size_mb=50)


def derive_student_name(filename: str) -> str:
    """从文件名提取学生姓名"""
    name = os.path.splitext(filename)[0]
    if "__" in name:
        return name.split("__")[-1].strip() or name
    return name


def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """验证 Prompt 内容"""
    if not prompt or not prompt.strip():
        return False, "Prompt 不能为空"

    if len(prompt) < 50:
        return False, "Prompt 内容过短，请提供更详细的评分标准"

    return True, "验证通过"
