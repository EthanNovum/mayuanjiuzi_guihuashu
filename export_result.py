import argparse
import csv
import json
import os
from typing import Any, Dict, Iterable, List


DEFAULT_FIELDS = ["filename", "student_name", "score", "strengths", "gaps", "suggestions"]


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"jsonl file not found: {path}")
    items: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if isinstance(data, dict):
                items.append(data)
    if not items:
        raise ValueError(f"no valid JSON objects found in {path}")
    return items


def merge_bullets(value: Any) -> str:
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            else:
                parts.append(json.dumps(item, ensure_ascii=False))
        return "\n".join([p for p in parts if p])
    if value is None:
        return ""
    return str(value)


def build_fieldnames(items: Iterable[Dict[str, Any]]) -> List[str]:
    extra_fields: List[str] = []
    seen = set(DEFAULT_FIELDS)
    for item in items:
        for key in item.keys():
            if key in seen:
                continue
            seen.add(key)
            extra_fields.append(key)
    return DEFAULT_FIELDS + extra_fields


def export_csv(items: List[Dict[str, Any]], output_path: str) -> None:
    fieldnames = build_fieldnames(items)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            row = {key: merge_bullets(item.get(key)) for key in fieldnames}
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export JSONL to CSV.")
    parser.add_argument(
        "--input",
        default="result.jsonl",
        help="Path to JSONL file (default: result.jsonl)",
    )
    parser.add_argument(
        "--output",
        default="result.csv",
        help="Path to output CSV (default: result.csv)",
    )
    args = parser.parse_args()

    items = load_jsonl(args.input)
    export_csv(items, args.output)
    print(f"导出完成 -> {args.output}")


if __name__ == "__main__":
    main()
