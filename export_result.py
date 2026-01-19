import argparse
import csv
import json
import os
from typing import Any, Dict, List


DEFAULT_FIELDS = [
    "filename",
    "student_name",
    "provider",
    "model",
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


def find_latest_result(results_dir: str = "results") -> str:
    """Find the most recent result_*.json file in the results directory."""
    if not os.path.isdir(results_dir):
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    json_files = [
        f for f in os.listdir(results_dir)
        if f.startswith("result_") and f.endswith(".json")
    ]

    if not json_files:
        raise FileNotFoundError(f"No result_*.json files found in {results_dir}")

    json_files.sort(reverse=True)
    return os.path.join(results_dir, json_files[0])


def load_json(path: str) -> List[Dict[str, Any]]:
    """Load results from a JSON file (array format)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        return [data]
    raise ValueError(f"Invalid JSON format in {path}")


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load results from a JSONL file (line-by-line format)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSONL file not found: {path}")
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
        raise ValueError(f"No valid JSON objects found in {path}")
    return items


def load_results(path: str) -> List[Dict[str, Any]]:
    """Load results from either JSON or JSONL file based on extension."""
    if path.endswith(".jsonl"):
        return load_jsonl(path)
    return load_json(path)


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


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(item)
    subscores = normalized.pop("subscores", None)
    if isinstance(subscores, dict):
        for key, value in subscores.items():
            normalized.setdefault(key, value)
    return normalized


def build_fieldnames(items: List[Dict[str, Any]]) -> List[str]:
    extra_fields: List[str] = []
    seen = set(DEFAULT_FIELDS)
    for item in items:
        normalized = normalize_item(item)
        for key in normalized.keys():
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
            normalized = normalize_item(item)
            row = {key: merge_bullets(normalized.get(key)) for key in fieldnames}
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export JSON/JSONL results to CSV.")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to input file. If not specified, uses the latest result_*.json in results/",
    )
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory to search for result files (default: results)",
    )
    parser.add_argument(
        "--output",
        default="result.csv",
        help="Path to output CSV (default: result.csv)",
    )
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    else:
        input_path = find_latest_result(args.results_dir)
        print(f"Found latest result file: {input_path}")

    items = load_results(input_path)
    export_csv(items, args.output)
    print(f"Exported {len(items)} items to {args.output}")


if __name__ == "__main__":
    main()
