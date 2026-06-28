"""ASR 语音识别：内网 SenseVoice REST API

请求格式：POST JSON {"audio": "<base64>", "lang": "zh"}
响应格式：JSON 文本（包含识别结果）
音频格式：接受 base64 编码的 WAV/PCM 音频
"""
import base64
import json
import logging
import httpx

from . import config

logger = logging.getLogger("voice-pipeline.asr")


async def recognize(audio_bytes: bytes, lang: str = "zh") -> str:
    """将音频 bytes 发送到内网 ASR API，返回识别文本。

    Args:
        audio_bytes: WAV 格式的音频数据
        lang: 语言代码（默认 zh）

    Returns:
        识别的文本（可能为空字符串）
    """
    cfg = config.ASR_CONFIG
    url = config.build_url(
        cfg["base_url"], cfg["app_id"], cfg["auth_key"], cfg["serving_id"]
    )

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    payload = {"audio": audio_b64, "lang": lang}
    headers = {
        "Content-Type": "application/json",
        "Authorization": cfg["authorization"],
    }

    logger.info("ASR request → %s (audio=%d bytes)", cfg["base_url"], len(audio_bytes))

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

    resp.raise_for_status()

    # 尝试解析 JSON 响应
    content_type = resp.headers.get("Content-Type", "")
    if "json" in content_type or resp.text.strip().startswith("{"):
        data = resp.json()
        # 常见返回格式：{"text": "识别文本"} 或 {"result": "识别文本"}
        text = data.get("text") or data.get("result") or data.get("data", {}).get("text", "")
        logger.info("ASR result: %s", text[:100] if text else "(empty)")
        return text.strip()
    else:
        # 纯文本响应
        text = resp.text.strip()
        logger.info("ASR result (text): %s", text[:100] if text else "(empty)")
        return text
