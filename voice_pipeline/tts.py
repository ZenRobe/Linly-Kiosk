"""TTS 语音合成：内网 Kokoro REST API

请求格式：POST JSON {"model": "kokoro", "voice": "zm_009", "input": "文本"}
响应格式：二进制音频数据（WAV 格式）
"""
import json
import logging
import httpx

from . import config

logger = logging.getLogger("voice-pipeline.tts")


async def synthesize(text: str) -> bytes:
    """将文本发送到内网 TTS API，返回合成音频 bytes。

    Args:
        text: 要合成的文本

    Returns:
        音频数据 bytes（WAV 格式）
    """
    cfg = config.TTS_CONFIG
    url = config.build_url(
        cfg["base_url"], cfg["app_id"], cfg["auth_key"], cfg["serving_id"]
    )

    payload = {
        "model": cfg["model"],
        "voice": cfg["voice"],
        "input": text,
    }
    headers = {"Content-Type": "application/json"}

    logger.info("TTS request → %s (text=%d chars)", cfg["base_url"], len(text))

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

    resp.raise_for_status()

    audio_bytes = resp.content
    logger.info("TTS response: %d bytes", len(audio_bytes))
    return audio_bytes
