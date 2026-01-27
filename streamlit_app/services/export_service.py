"""
导出服务
封装 export_result 功能
"""
import csv
import json
import os
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List


DEFAULT_FIELDS = [
    "filename",
    "student_name",
    "provider",
    "model",
    "prompt_name",
    "score",
    "clearness_and_consistency",
    "detail_and_executable",
    "depth_and_intensity",
    "noviceness",
    "fitness",
    "liberal_arts_values",
    "strengths",
    "gaps",
    "profile",
    "planning",
    "suggestions",
]


def merge_bullets(value: Any) -> str:
    """将列表值合并为多行文本"""
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            else:
                parts.append(json.dumps(item, ensure_ascii=False))
        return "\n".join([p for p in parts if p])
    if value is None:
        return ""
    return str(value)


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """规范化结果项"""
    normalized = dict(item)
    subscores = normalized.pop("subscores", None)
    if isinstance(subscores, dict):
        for key, value in subscores.items():
            normalized.setdefault(key, value)
    return normalized


def build_fieldnames(items: List[Dict[str, Any]]) -> List[str]:
    """构建字段名列表"""
    extra_fields = []
    seen = set(DEFAULT_FIELDS)
    for item in items:
        normalized = normalize_item(item)
        for key in normalized.keys():
            if key in seen:
                continue
            seen.add(key)
            extra_fields.append(key)
    return DEFAULT_FIELDS + extra_fields


def export_to_csv_string(items: List[Dict[str, Any]]) -> str:
    """导出结果为 CSV 字符串"""
    if not items:
        return ""

    fieldnames = build_fieldnames(items)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for item in items:
        normalized = normalize_item(item)
        row = {key: merge_bullets(normalized.get(key)) for key in fieldnames}
        writer.writerow(row)

    return output.getvalue()


def export_to_csv_file(items: List[Dict[str, Any]], output_path: str) -> str:
    """导出结果为 CSV 文件"""
    csv_content = export_to_csv_string(items)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
    return output_path


def export_to_json_string(items: List[Dict[str, Any]], indent: int = 2) -> str:
    """导出结果为 JSON 字符串"""
    return json.dumps(items, ensure_ascii=False, indent=indent)


def export_to_json_file(items: List[Dict[str, Any]], output_path: str) -> str:
    """导出结果为 JSON 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return output_path


def generate_export_filename(prefix: str = "result", ext: str = "csv") -> str:
    """生成导出文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{ext}"


def load_results_from_file(file_path: str) -> List[Dict[str, Any]]:
    """从文件加载结果"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        return [data]

    raise ValueError(f"无效的 JSON 格式: {file_path}")


def get_results_summary(items: List[Dict[str, Any]]) -> Dict:
    """获取结果统计摘要"""
    if not items:
        return {
            "total": 0,
            "success": 0,
            "error": 0,
            "avg_score": None,
            "min_score": None,
            "max_score": None,
            "providers": [],
        }

    success_items = [i for i in items if not i.get("error")]
    error_items = [i for i in items if i.get("error")]

    scores = [i.get("score") for i in success_items if i.get("score") is not None]
    providers = list(set(i.get("provider", "") for i in items if i.get("provider")))

    return {
        "total": len(items),
        "success": len(success_items),
        "error": len(error_items),
        "avg_score": sum(scores) / len(scores) if scores else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "providers": providers,
    }
