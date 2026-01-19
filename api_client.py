"""
Multi-provider API client for LLM calls.
Supports: gemini, openai, claude, deepseek, qwen, doubao, kimi
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Protocol


# ============================================================
# Utility Functions
# ============================================================

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


def load_prompt_path(env_values: dict, fallback: str) -> str:
    return env_values.get("PROMPT_PATH") or fallback


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


def build_opener(proxy_url: str | None) -> urllib.request.OpenerDirector:
    """Build a URL opener with optional proxy support."""
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy_url,
            'https': proxy_url
        })
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


# ============================================================
# Provider Configuration
# ============================================================

PROVIDER_DEFAULTS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-reasoner",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "claude": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.5-pro-preview-05-06",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-1-5-thinking-pro-250415",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
}

SUPPORTED_PROVIDERS = list(PROVIDER_DEFAULTS.keys())


# ============================================================
# API Client Protocol
# ============================================================

class APIClient(Protocol):
    """API client protocol for different providers."""
    provider: str
    model: str

    def call(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        """Call the API and return (message, thinking)."""
        ...


# ============================================================
# OpenAI Compatible Client (deepseek, openai, qwen, doubao, kimi)
# ============================================================

class OpenAICompatibleClient:
    """Client for OpenAI-compatible APIs."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str,
        proxy_url: str | None = None,
        timeout: int = 300,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.proxy_url = proxy_url
        self.timeout = timeout

    def call(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        opener = build_opener(self.proxy_url)

        try:
            with opener.open(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"{self.provider} request failed: {e.code} {error_body}") from e

        response_json = json.loads(body)
        return self._extract_response(response_json)

    def _extract_response(self, response_json: dict) -> tuple[str, str | None]:
        choices = response_json.get("choices") or []
        if not choices:
            raise ValueError("no choices in response")

        choice = choices[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        reasoning_content = message.get("reasoning_content")

        if not content:
            raise ValueError("no content in response")

        return content.strip(), reasoning_content


# ============================================================
# Claude Client (Anthropic format)
# ============================================================

class ClaudeClient:
    """Client for Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        proxy_url: str | None = None,
        timeout: int = 300,
    ):
        self.provider = "claude"
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.proxy_url = proxy_url
        self.timeout = timeout

    def call(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_content},
            ],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        opener = build_opener(self.proxy_url)

        try:
            with opener.open(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Claude request failed: {e.code} {error_body}") from e

        response_json = json.loads(body)
        return self._extract_response(response_json)

    def _extract_response(self, response_json: dict) -> tuple[str, str | None]:
        content_blocks = response_json.get("content") or []
        text_parts = []
        thinking_parts = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "thinking":
                thinking_parts.append(block.get("thinking", ""))

        message_text = "\n".join(text_parts).strip()
        if not message_text:
            raise ValueError("no text content in response")

        thinking_text = "\n".join(thinking_parts).strip() or None
        return message_text, thinking_text


# ============================================================
# Gemini Client
# ============================================================

class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        proxy_url: str | None = None,
        timeout: int = 300,
    ):
        self.provider = "gemini"
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.proxy_url = proxy_url
        self.timeout = timeout

    def call(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        url = f"{self.base_url}/models/{self.model}:generateContent"
        contents = [
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_content}]},
        ]
        payload = {
            "contents": contents,
            "generationConfig": {
                "thinkingConfig": {"includeThoughts": True},
                "temperature": 0,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        opener = build_opener(self.proxy_url)

        try:
            with opener.open(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini request failed: {e.code} {error_body}") from e

        response_json = json.loads(body)
        return self._extract_response(response_json)

    def _extract_response(self, response_json: dict) -> tuple[str, str | None]:
        candidates = response_json.get("candidates") or []
        if not candidates:
            raise ValueError("no candidates in response")

        candidate = candidates[0]
        content = candidate.get("content") or {}
        parts = content.get("parts") or []

        text_parts: list[str] = []
        thought_parts: list[str] = []

        for part in parts:
            text = part.get("text")
            if not text:
                continue
            if part.get("thought"):
                thought_parts.append(str(text))
            else:
                text_parts.append(str(text))

        message_text = "\n".join(text_parts).strip()
        if not message_text:
            raise ValueError("no message text in response")

        thought_text = "\n".join(
            item.strip() for item in thought_parts if str(item).strip()
        ).strip()

        return message_text, (thought_text or None)


# ============================================================
# Client Factory
# ============================================================

def create_client(
    provider: str,
    env_values: dict,
    model_override: str | None = None,
) -> APIClient:
    """Create an API client based on provider name."""
    provider = provider.lower()

    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(f"Unknown provider: {provider}. Supported: {', '.join(SUPPORTED_PROVIDERS)}")

    defaults = PROVIDER_DEFAULTS[provider]
    prefix = provider.upper()

    api_key = env_values.get(f"{prefix}_API_KEY")
    if not api_key:
        raise ValueError(f"{prefix}_API_KEY not found in env file")

    model = model_override or env_values.get(f"{prefix}_MODEL") or defaults["model"]
    base_url = env_values.get(f"{prefix}_BASE_URL") or defaults["base_url"]
    proxy_url = env_values.get(f"{prefix}_PROXY") or None

    if provider == "gemini":
        return GeminiClient(api_key, model, base_url, proxy_url)
    elif provider == "claude":
        return ClaudeClient(api_key, model, base_url, proxy_url)
    else:
        # OpenAI-compatible: deepseek, openai, qwen, doubao, kimi
        return OpenAICompatibleClient(provider, api_key, model, base_url, proxy_url)


def create_clients(
    providers: list[str],
    env_values: dict,
) -> list[APIClient]:
    """Create multiple API clients."""
    clients = []
    for provider in providers:
        try:
            client = create_client(provider, env_values)
            clients.append(client)
        except ValueError as e:
            print(f"Warning: Skipping {provider}: {e}")
    return clients


# ============================================================
# Processing Functions
# ============================================================

def process_single_file(
    client: APIClient,
    prompt: str,
    filename: str,
    content: str,
) -> dict:
    """Process a single file with a single client."""
    try:
        message_text, thought_text = client.call(prompt, content)
        clean_message = clean_json_text(message_text)
        result = json.loads(clean_message)

        if isinstance(result, dict):
            result["filename"] = filename
            result["provider"] = client.provider
            result["model"] = client.model
            if not result.get("student_name"):
                result["student_name"] = derive_student_name(filename)
            result["thinking"] = thought_text or ""
            return result
        else:
            return {
                "result": result,
                "filename": filename,
                "provider": client.provider,
                "model": client.model,
                "student_name": derive_student_name(filename),
                "thinking": thought_text or "",
            }
    except Exception as e:
        return {
            "filename": filename,
            "provider": client.provider,
            "model": client.model,
            "student_name": derive_student_name(filename),
            "error": str(e),
        }


def process_file_with_clients(
    clients: list[APIClient],
    prompt: str,
    filename: str,
    content: str,
) -> list[dict]:
    """Process a single file with multiple clients in parallel."""
    if len(clients) == 1:
        return [process_single_file(clients[0], prompt, filename, content)]

    results = []
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = {
            executor.submit(process_single_file, client, prompt, filename, content): client
            for client in clients
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    return results


# ============================================================
# Output Functions
# ============================================================

def save_results(results: list[dict], output_dir: str = "results") -> str:
    """Save results to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"result_{timestamp}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return output_path


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Call LLM API with a prompt file.")
    parser.add_argument(
        "--prompt",
        default="prompts/prompt_mayuan_0108.txt",
        help="Path to prompt file",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file",
    )
    parser.add_argument(
        "--mds",
        default="mds",
        help="Directory containing markdown planbook files",
    )
    parser.add_argument(
        "--providers",
        default="gemini",
        help="Comma-separated list of providers (e.g., gemini,deepseek,openai)",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save result JSON files",
    )
    args = parser.parse_args()

    env_values = load_env(args.env)

    provider_list = [p.strip() for p in args.providers.split(",") if p.strip()]
    if not provider_list:
        raise ValueError("No providers specified")

    clients = create_clients(provider_list, env_values)
    if not clients:
        raise ValueError("No valid clients could be created")

    print(f"Providers: {', '.join(c.provider for c in clients)}")
    print(f"Models: {', '.join(f'{c.provider}:{c.model}' for c in clients)}")

    prompt_path = load_prompt_path(env_values, args.prompt)
    base_prompt = load_prompt(prompt_path)
    preview = base_prompt.strip().replace("\n", " ")
    preview = preview[:200] + ("..." if len(preview) > 200 else "")
    print(f"Prompt preview ({prompt_path}): {preview}")

    md_items = load_markdown_files(args.mds)
    results: list[dict] = []

    for i, (filename, content) in enumerate(md_items, 1):
        print(f"[{i}/{len(md_items)}] Processing {filename}...")
        file_results = process_file_with_clients(clients, base_prompt, filename, content)
        for r in file_results:
            if "error" in r:
                print(f"  -> {r['provider']}: Error - {r['error']}")
            else:
                print(f"  -> {r['provider']}: OK")
            results.append(r)

    output_path = save_results(results, args.output_dir)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
