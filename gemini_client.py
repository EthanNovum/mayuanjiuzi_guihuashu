import argparse
import json
import os
import urllib.error
import urllib.request


def load_env(env_path: str) -> dict:
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"config file not found: {env_path}")
    values = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_api_key(env_values: dict) -> str:
    api_key = env_values.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in env file")
    return api_key


def load_model(env_values: dict) -> str | None:
    return env_values.get("MODEL")


def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def load_markdown_files(mds_dir: str) -> list[tuple[str, str]]:
    if not os.path.isdir(mds_dir):
        raise FileNotFoundError(f"mds directory not found: {mds_dir}")
    md_files = sorted(
        entry
        for entry in os.listdir(mds_dir)
        if entry.lower().endswith(".md") and os.path.isfile(os.path.join(mds_dir, entry))
    )
    if not md_files:
        raise ValueError(f"no markdown files found in {mds_dir}")
    items: list[tuple[str, str]] = []
    for filename in md_files:
        path = os.path.join(mds_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            items.append((filename, content))
    if not items:
        raise ValueError(f"markdown files are empty in {mds_dir}")
    return items


def extract_message(response_json: dict) -> str:
    candidates = response_json.get("candidates") or []
    if not candidates:
        raise ValueError("no candidates in response")
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    if not parts or "text" not in parts[0]:
        raise ValueError("no message text in response")
    return parts[0]["text"]


def call_gemini(api_key: str, prompt_text: str, model: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt_text}],
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"gemini request failed: {e.code} {error_body}") from e
    response_json = json.loads(body)
    return extract_message(response_json)


def build_prompt(base_prompt: str, planbook_text: str) -> str:
    return f"{base_prompt}\n\n规划书内容如下：\n{planbook_text}\n"


def append_jsonl(output_path: str, json_text: str) -> None:
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json_text.strip() + "\n")


def clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in response")
    return text[start : end + 1]


def derive_student_name(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    if "__" in name:
        return name.split("__")[-1].strip() or name
    return name


def main() -> None:
    parser = argparse.ArgumentParser(description="Request Gemini with a prompt file.")
    parser.add_argument(
        "--prompt",
        default="prompts/prompt_v2.txt",
        help="Path to prompt file",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env (expects GEMINI_API_KEY=...)",
    )
    parser.add_argument(
        "--mds",
        default="mds",
        help="Directory containing markdown planbook files",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model name (overrides MODEL in env)",
    )
    parser.add_argument(
        "--output",
        default="result.jsonl",
        help="Path to append JSONL results",
    )
    args = parser.parse_args()

    env_values = load_env(args.env)
    api_key = load_api_key(env_values)
    model = args.model or load_model(env_values) or "gemini-2.5-flash"
    base_prompt = load_prompt(args.prompt)
    md_items = load_markdown_files(args.mds)
    for filename, content in md_items:
        prompt_text = build_prompt(base_prompt, content)
        message = call_gemini(api_key, prompt_text, model)
        clean_message = clean_json_text(message)
        print(f"{filename}:\n{clean_message}")
        result = json.loads(clean_message)
        if isinstance(result, dict):
            result["filename"] = filename
            if not result.get("student_name"):
                result["student_name"] = derive_student_name(filename)
        append_jsonl(args.output, json.dumps(result, ensure_ascii=False))
    


if __name__ == "__main__":
    main()
