"""
评分服务
封装 api_client 功能
"""
import json
import os
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# LLM 提供商配置
PROVIDER_DEFAULTS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.5-pro-preview-05-06",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "claude": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-reasoner",
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


def get_available_providers(api_config: Dict) -> List[str]:
    """获取已配置的可用提供商列表"""
    available = []
    for provider in SUPPORTED_PROVIDERS:
        key_name = f"{provider.upper()}_API_KEY"
        if api_config.get(key_name):
            available.append(provider)
    return available


def clean_json_text(raw_text: str) -> str:
    """清理并提取 JSON 文本"""
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
        raise ValueError("响应中未找到有效的 JSON 对象")
    return text[start:end + 1]


def derive_student_name(filename: str) -> str:
    """从文件名提取学生姓名"""
    name = os.path.splitext(filename)[0]
    if "__" in name:
        return name.split("__")[-1].strip() or name
    return name


class LLMClient:
    """LLM 客户端基类"""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout: int = 300
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, system_prompt: str, user_content: str) -> Tuple[str, Optional[str]]:
        """调用 API，返回 (响应文本, 思考过程)"""
        raise NotImplementedError


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容客户端（支持 deepseek, openai, qwen, doubao, kimi）"""

    def call(self, system_prompt: str, user_content: str) -> Tuple[str, Optional[str]]:
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

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"{self.provider} 请求失败: {e.code} {error_body}") from e

        response_json = json.loads(body)
        choices = response_json.get("choices", [])
        if not choices:
            raise ValueError("响应中无 choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        reasoning = message.get("reasoning_content")

        if not content:
            raise ValueError("响应中无内容")

        return content.strip(), reasoning


class ClaudeClient(LLMClient):
    """Claude 客户端"""

    def call(self, system_prompt: str, user_content: str) -> Tuple[str, Optional[str]]:
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

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Claude 请求失败: {e.code} {error_body}") from e

        response_json = json.loads(body)
        content_blocks = response_json.get("content", [])

        text_parts = []
        thinking_parts = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "thinking":
                thinking_parts.append(block.get("thinking", ""))

        message_text = "\n".join(text_parts).strip()
        if not message_text:
            raise ValueError("响应中无文本内容")

        thinking_text = "\n".join(thinking_parts).strip() or None
        return message_text, thinking_text


class GeminiClient(LLMClient):
    """Gemini 客户端"""

    def call(self, system_prompt: str, user_content: str) -> Tuple[str, Optional[str]]:
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

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini 请求失败: {e.code} {error_body}") from e

        response_json = json.loads(body)
        candidates = response_json.get("candidates", [])
        if not candidates:
            raise ValueError("响应中无 candidates")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        text_parts = []
        thought_parts = []

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
            raise ValueError("响应中无消息文本")

        thought_text = "\n".join(
            item.strip() for item in thought_parts if str(item).strip()
        ).strip() or None

        return message_text, thought_text


def create_client(provider: str, api_config: Dict) -> LLMClient:
    """创建 LLM 客户端"""
    provider = provider.lower()

    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(f"不支持的提供商: {provider}")

    defaults = PROVIDER_DEFAULTS[provider]
    prefix = provider.upper()

    api_key = api_config.get(f"{prefix}_API_KEY")
    if not api_key:
        raise ValueError(f"{prefix}_API_KEY 未配置")

    model = api_config.get(f"{prefix}_MODEL") or defaults["model"]
    base_url = api_config.get(f"{prefix}_BASE_URL") or defaults["base_url"]

    if provider == "gemini":
        return GeminiClient(provider, api_key, model, base_url)
    elif provider == "claude":
        return ClaudeClient(provider, api_key, model, base_url)
    else:
        return OpenAICompatibleClient(provider, api_key, model, base_url)


def score_single_file(
    client: LLMClient,
    prompt: str,
    filename: str,
    content: str,
    prompt_name: str = ""
) -> Dict:
    """对单个文件进行评分"""
    try:
        message_text, thought_text = client.call(prompt, content)
        clean_message = clean_json_text(message_text)
        result = json.loads(clean_message)

        if isinstance(result, dict):
            result["filename"] = filename
            result["provider"] = client.provider
            result["model"] = client.model
            result["prompt_name"] = prompt_name
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
                "prompt_name": prompt_name,
                "student_name": derive_student_name(filename),
                "thinking": thought_text or "",
            }
    except Exception as e:
        return {
            "filename": filename,
            "provider": client.provider,
            "model": client.model,
            "prompt_name": prompt_name,
            "student_name": derive_student_name(filename),
            "error": str(e),
        }


def score_batch(
    files: List[Dict],
    providers: List[str],
    prompt: str,
    api_config: Dict,
    prompt_name: str = "",
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict]:
    """
    批量评分

    Args:
        files: 文件列表，每个包含 filename 和 markdown
        providers: 使用的提供商列表
        prompt: 评分 Prompt
        api_config: API 配置
        prompt_name: Prompt 名称
        progress_callback: 进度回调函数 (current, total, message)

    Returns:
        评分结果列表
    """
    results = []
    total = len(files) * len(providers)
    current = 0

    for file_info in files:
        filename = file_info.get("filename", "unknown")
        content = file_info.get("markdown", "")

        for provider in providers:
            current += 1

            if progress_callback:
                progress_callback(
                    current, total,
                    f"正在评分: {filename} ({provider})"
                )

            try:
                client = create_client(provider, api_config)
                result = score_single_file(
                    client, prompt, filename, content, prompt_name
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "filename": filename,
                    "provider": provider,
                    "prompt_name": prompt_name,
                    "student_name": derive_student_name(filename),
                    "error": str(e),
                })

    return results


def load_prompt_file(prompt_path: str) -> str:
    """加载 Prompt 文件"""
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def list_prompt_files(prompts_dir: str) -> List[Dict]:
    """列出所有 Prompt 文件"""
    prompts = []
    if not os.path.isdir(prompts_dir):
        return prompts

    for filename in sorted(os.listdir(prompts_dir)):
        if filename.endswith(".txt"):
            path = os.path.join(prompts_dir, filename)
            name = os.path.splitext(filename)[0]
            prompts.append({
                "name": name,
                "path": path,
                "filename": filename,
            })

    return prompts
