"""
数据持久化存储服务
将处理结果保存到本地 JSON 文件，实现数据持久化
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_data_dir() -> Path:
    """获取数据存储目录"""
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_processed_markdowns_path() -> Path:
    """获取 OCR 处理结果存储路径"""
    return get_data_dir() / "processed_markdowns.json"


def get_scoring_results_path() -> Path:
    """获取评分结果存储路径"""
    return get_data_dir() / "scoring_results.json"


def get_history_path() -> Path:
    """获取历史记录存储路径"""
    return get_data_dir() / "history.json"


# ============================================================
# OCR 处理结果持久化
# ============================================================

def save_processed_markdowns(markdowns: List[Dict]) -> None:
    """保存 OCR 处理结果到文件"""
    path = get_processed_markdowns_path()

    # 加载现有数据
    existing = load_processed_markdowns()

    # 合并新数据（按文件名去重，新数据覆盖旧数据）
    existing_map = {m.get("filename"): m for m in existing}
    for m in markdowns:
        filename = m.get("filename")
        if filename:
            existing_map[filename] = m

    # 保存
    merged = list(existing_map.values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)


def load_processed_markdowns() -> List[Dict]:
    """从文件加载 OCR 处理结果"""
    path = get_processed_markdowns_path()
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def delete_processed_markdown(filename: str) -> bool:
    """删除指定的 OCR 处理结果"""
    markdowns = load_processed_markdowns()
    new_markdowns = [m for m in markdowns if m.get("filename") != filename]

    if len(new_markdowns) < len(markdowns):
        path = get_processed_markdowns_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_markdowns, f, ensure_ascii=False, indent=2)
        return True
    return False


def clear_processed_markdowns() -> None:
    """清空所有 OCR 处理结果"""
    path = get_processed_markdowns_path()
    if path.exists():
        path.unlink()


# ============================================================
# 评分结果持久化
# ============================================================

def save_scoring_results(results: List[Dict], append: bool = True) -> None:
    """
    保存评分结果到文件

    Args:
        results: 评分结果列表
        append: 是否追加到现有数据（默认追加）
    """
    path = get_scoring_results_path()

    if append:
        existing = load_scoring_results()
        # 合并（按 filename + provider + prompt_name 去重）
        existing_map = {}
        for r in existing:
            key = (r.get("filename", ""), r.get("provider", ""), r.get("prompt_name", ""))
            existing_map[key] = r

        for r in results:
            key = (r.get("filename", ""), r.get("provider", ""), r.get("prompt_name", ""))
            existing_map[key] = r

        merged = list(existing_map.values())
    else:
        merged = results

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)


def load_scoring_results() -> List[Dict]:
    """从文件加载评分结果"""
    path = get_scoring_results_path()
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def delete_scoring_result(filename: str, provider: str = None, prompt_name: str = None) -> int:
    """
    删除指定的评分结果

    Returns:
        删除的记录数
    """
    results = load_scoring_results()
    original_count = len(results)

    new_results = []
    for r in results:
        match = r.get("filename") == filename
        if provider:
            match = match and r.get("provider") == provider
        if prompt_name:
            match = match and r.get("prompt_name") == prompt_name

        if not match:
            new_results.append(r)

    deleted_count = original_count - len(new_results)

    if deleted_count > 0:
        path = get_scoring_results_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_results, f, ensure_ascii=False, indent=2)

    return deleted_count


def clear_scoring_results() -> None:
    """清空所有评分结果"""
    path = get_scoring_results_path()
    if path.exists():
        path.unlink()


# ============================================================
# 历史记录
# ============================================================

def add_history_entry(action: str, details: Dict = None) -> None:
    """添加历史记录条目"""
    path = get_history_path()

    history = load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details or {},
    }

    history.append(entry)

    # 只保留最近 1000 条
    if len(history) > 1000:
        history = history[-1000:]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_history() -> List[Dict]:
    """加载历史记录"""
    path = get_history_path()
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def clear_history() -> None:
    """清空历史记录"""
    path = get_history_path()
    if path.exists():
        path.unlink()


# ============================================================
# 统一数据管理
# ============================================================

def get_storage_stats() -> Dict:
    """获取存储统计信息"""
    markdowns = load_processed_markdowns()
    results = load_scoring_results()
    history = load_history()

    return {
        "processed_markdowns_count": len(markdowns),
        "scoring_results_count": len(results),
        "history_count": len(history),
        "data_dir": str(get_data_dir()),
    }


def clear_all_data() -> None:
    """清空所有持久化数据"""
    clear_processed_markdowns()
    clear_scoring_results()
    clear_history()
