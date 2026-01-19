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


def call_gemini(api_key: str, model: str, prompt_text: str) -> dict:
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
    return json.loads(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple Gemini API test.")
    parser.add_argument("--env", default=".env", help="Path to .env")
    parser.add_argument("--model", default=None, help="Model name override")
    parser.add_argument("--prompt", default="Hello from test.py", help="Prompt text")
    args = parser.parse_args()

    env_values = load_env(args.env)
    api_key = env_values.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in env file")
    model = args.model or env_values.get("MODEL") or "gemini-3-pro-preview"

    response = call_gemini(api_key, model, args.prompt)
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
