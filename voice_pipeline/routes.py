"""
FastAPI 路由：ASR (HTTP POST) + Chat 流式对话 (WebSocket)
注册到 FastAPI app 上（在 app.py 中通过 register_routes 调用）

ASR：POST /asr  接收音频 bytes，返回 {"text": "..."}
Chat：WS /chat/stream  LLM 流式 + TTS 逐句合成（非流式）
"""
import asyncio
import base64
import json
import logging

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from . import asr, llm, streaming, tts

logger = logging.getLogger("voice-pipeline.routes")
logging.basicConfig(level=logging.INFO)


def register_routes(fastapi_app):
    """在给定的 FastAPI app 上注册语音对话路由。"""

    # ==================== ASR 语音识别（HTTP POST）====================

    @fastapi_app.post("/asr")
    async def asr_endpoint(request: Request):
        """接收前端发来的音频 bytes（WAV 格式），调用内网 ASR 返回识别文本。"""
        try:
            audio_bytes = await request.body()
            if not audio_bytes:
                return JSONResponse(
                    status_code=400, content={"error": "empty audio body"}
                )

            logger.info("POST /asr received %d bytes", len(audio_bytes))
            text = await asr.recognize(audio_bytes)

            return {"text": text}
        except Exception as e:
            logger.exception("ASR endpoint error")
            return JSONResponse(status_code=500, content={"error": str(e)})

    # ==================== Chat 流式对话（WebSocket）====================

    @fastapi_app.websocket("/chat/stream")
    async def chat_stream(ws: WebSocket):
        """LLM 流式 → 按句 → TTS 合成 → 文本 delta + base64 音频下发。

        前端发送：{"session_id": "...", "text": "..."}
        后端返回：
          - {"event": "text", "delta": "..."}    LLM token
          - {"event": "audio", "data": "<b64>"}  单句 TTS 音频 (WAV base64)
          - {"event": "done"}                     结束
          - {"event": "error", "message": "..."}  错误
        """
        await ws.accept()
        try:
            first = await ws.receive_json()
            text = (first.get("text") or "").strip()
            if not text:
                await ws.send_json({"event": "done"})
                return
            session_id = first.get("session_id", "")

            def _has_speech_content(s: str) -> bool:
                return any(
                    ch not in "。！？!？…\n，,;； \t\r" for ch in s
                )

            # 并发 TTS 任务队列：每句 TTS 与 LLM 流并行
            tts_tasks: list[asyncio.Task] = []

            async def _synthesize_and_send(sentence: str) -> None:
                """合成单句并发送 base64 音频帧。"""
                try:
                    audio = await tts.synthesize(sentence)
                    if audio:
                        audio_b64 = base64.b64encode(audio).decode("utf-8")
                        await ws.send_json({"event": "audio", "data": audio_b64})
                except Exception as e:
                    logger.exception("TTS per-sentence error")
                    await ws.send_json({"event": "error", "message": f"TTS: {e}"})

            splitter = streaming.SentenceSplitter()
            async for delta in llm.chat_stream(session_id, text):
                await ws.send_json({"event": "text", "delta": delta})
                for sentence in splitter.feed(delta):
                    if _has_speech_content(sentence):
                        tts_tasks.append(asyncio.create_task(_synthesize_and_send(sentence)))

            # 处理剩余文本
            for sentence in splitter.flush():
                if _has_speech_content(sentence):
                    tts_tasks.append(asyncio.create_task(_synthesize_and_send(sentence)))

            # 等待所有 TTS 任务完成
            if tts_tasks:
                await asyncio.gather(*tts_tasks, return_exceptions=True)

            await ws.send_json({"event": "done"})

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.exception("chat_stream error")
            try:
                await ws.send_json({"event": "error", "message": str(e)})
            except Exception:
                pass
