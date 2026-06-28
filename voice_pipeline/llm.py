"""LLM 对话：内网 Qwen3 235B MoE REST API

请求格式：POST JSON {"stream": true, "messages": [...]}
请求头：APP_ID / SECRET_KEY
响应格式：SSE 流式（OpenAI 兼容格式）
"""
import json
import logging
from typing import AsyncIterator

import httpx

from . import config, sessions

logger = logging.getLogger("voice-pipeline.llm")


async def chat_stream(
    session_id: str,
    text: str,
    system: str | None = None,
) -> AsyncIterator[str]:
    """流式多轮对话：逐 token yield delta；流结束后用完整 reply 追加历史。

    Args:
        session_id: 会话 ID（用于多轮对话历史）
        text: 用户输入文本
        system: 系统提示词（默认使用 config 中的预设）

    Yields:
        LLM 输出的 token delta 字符串
    """
    if system is None:
        system = config.LLM_CONFIG["system_prompt"]

    cfg = config.LLM_CONFIG

    # 构建消息列表（含历史）
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in sessions.get_history(session_id)
    ]
    messages = [{"role": "system", "content": system}] + history
    messages.append({"role": "user", "content": text})

    payload = {
        "stream": True,
        "messages": messages,
    }
    headers = {
        "Content-Type": "application/json",
        "APP_ID": cfg["app_id"],
        "SECRET_KEY": cfg["secret_key"],
    }

    logger.info("LLM request → %s (messages=%d)", cfg["base_url"], len(messages))

    parts: list[str] = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", cfg["base_url"], headers=headers, json=payload
        ) as resp:
            resp.raise_for_status()

            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                # SSE 格式：data: {...}
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # OpenAI 兼容格式：choices[0].delta.content
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            parts.append(content)
                            yield content

    # 流结束后追加完整历史
    full_reply = "".join(parts)
    if full_reply:
        sessions.append_message(session_id, "user", text)
        sessions.append_message(session_id, "assistant", full_reply)
    logger.info("LLM complete: %d chars", len(full_reply))
