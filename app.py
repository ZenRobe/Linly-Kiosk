"""
数字人问答展示系统 - 主应用
功能：点击问题播放数字人视频，包含随机挥手动画
"""
import os
import sys
import json

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 解析基础路径（开发模式 vs PyInstaller 打包后的 .exe）
def _get_base_path():
    """返回应用根目录，兼容 PyInstaller 打包后的临时解压目录"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_path()

import gradio as gr
from configs import kiosk_config as config

# ============================================
# 语音对话流水线 (ASR → LLM → TTS)
# ============================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from voice_pipeline.routes import register_routes

# 视频资源路径（绝对路径，开发/打包模式通用）
IDLE_VIDEO = os.path.join(BASE_DIR, "videos", "idle.mp4").replace("\\", "/")
# talking.mp4：数字人说话口型动画（~4s，循环播放，静音）；音频由 mp3/TTS 独立驱动，作为回答主时钟
TALKING_VIDEO = os.path.join(BASE_DIR, "videos", "talking.mp4").replace("\\", "/")
# 预设问题配音目录：videos/{id}.mp3（如 xq01.mp3），作为预设问题回答的音频主时钟
SPEAK_AUDIO_DIR = os.path.join(BASE_DIR, "videos").replace("\\", "/")
VIDEO_DIR = os.path.join(BASE_DIR, "videos")

# 问题库（JSON 格式供前端 JS 使用）
ALL_QUESTIONS_JS = json.dumps(config.QUESTION_POOL, ensure_ascii=False)
DISPLAY_COUNT = 8  # 固定显示8个问题（左4右4）

# ============================================
# CSS 样式
# ============================================

KIOSK_CSS = """
:root {
    --grid-deep: #061827;
    --grid-ink: #081220;
    --grid-green: #075b56;
    --grid-teal: #0b8b78;
    --energy-green: #16a783;
    --data-blue: #1e88d1;
    --grid-gold: #c8892b;
    --paper: #fbfefd;
    --line: rgba(184, 220, 209, 0.32);
    --panel: rgba(3, 22, 29, 0.82);
    --panel-strong: rgba(4, 38, 43, 0.92);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    background: #000;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
    color: var(--paper);
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

footer,
[class*="footer"]:not(.my-footer),
[id*="footer"],
[data-testid="footer"] {
    display: none !important;
}

.main-content {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    z-index: 1;
    pointer-events: none;
}

.question-panel,
.question-panel *,
.footer {
    pointer-events: auto !important;
}

.video-html-wrapper {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 0;
    pointer-events: none;
}

.video-container {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background:
        linear-gradient(180deg, #061827 0%, #02070b 46%, #061713 100%);
    z-index: 0;
}

.video-container::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 11;
    pointer-events: none;
    background:
        linear-gradient(90deg, rgba(0, 0, 0, 0.52) 0%, rgba(0, 0, 0, 0.10) 20%, rgba(0, 0, 0, 0.04) 50%, rgba(0, 0, 0, 0.10) 80%, rgba(0, 0, 0, 0.52) 100%),
        linear-gradient(180deg, rgba(6, 24, 39, 0.50) 0%, rgba(3, 10, 18, 0.06) 30%, rgba(3, 18, 15, 0.62) 100%);
}

.video-container::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 12;
    pointer-events: none;
    opacity: 0.58;
    background-image:
        linear-gradient(rgba(184, 220, 209, 0.075) 1px, transparent 1px),
        linear-gradient(90deg, rgba(184, 220, 209, 0.075) 1px, transparent 1px),
        linear-gradient(180deg, transparent 0%, rgba(22, 167, 131, 0.08) 78%, rgba(200, 137, 43, 0.12) 100%);
    background-size: 72px 72px, 72px 72px, 100% 100%;
}

.video-layer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    transition: opacity var(--video-transition, 0.03s) ease-out;
}

.video-layer.active {
    opacity: 1;
    z-index: 6;
}

.video-layer.inactive {
    opacity: 0;
    z-index: 4;
}

.top-identity {
    position: absolute;
    top: 38px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 35;
    width: min(76vw, 1580px);
    height: 88px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 34px;
    color: var(--paper);
    background:
        linear-gradient(90deg, rgba(7, 91, 86, 0.84), rgba(8, 18, 32, 0.72) 50%, rgba(7, 91, 86, 0.84));
    border: 1px solid rgba(184, 220, 209, 0.34);
    border-radius: 8px;
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.top-identity::before,
.top-identity::after {
    content: "";
    position: absolute;
    bottom: -1px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--grid-gold), var(--energy-green), transparent);
}

.top-identity::before {
    left: 32px;
    width: 36%;
}

.top-identity::after {
    right: 32px;
    width: 36%;
}

.identity-kicker {
    font-size: 16px;
    color: rgba(251, 254, 253, 0.68);
    margin-bottom: 6px;
}

.identity-title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.12;
}

.identity-status {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
    color: rgba(251, 254, 253, 0.78);
}

.status-dot {
    width: 10px;
    height: 10px;
    background: var(--energy-green);
    border-radius: 50%;
    box-shadow: 0 0 18px rgba(22, 167, 131, 0.72);
}

.stage-line {
    position: absolute;
    left: 50%;
    bottom: 58px;
    transform: translateX(-50%);
    z-index: 14;
    width: 72vw;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(22, 167, 131, 0.56), rgba(200, 137, 43, 0.50), rgba(22, 167, 131, 0.56), transparent);
}

.stage-line::before {
    content: "";
    position: absolute;
    left: 0;
    top: -1px;
    width: 22%;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(251, 254, 253, 0.84), transparent);
    animation: lineSweep 5.2s ease-in-out infinite;
}

@keyframes lineSweep {
    0% { transform: translateX(0); opacity: 0; }
    14% { opacity: 1; }
    72% { opacity: 1; }
    100% { transform: translateX(360%); opacity: 0; }
}

.wave-overlay {
    position: absolute;
    bottom: 8%;
    right: 12%;
    width: 12vw;
    height: 12vw;
    z-index: 32;
    display: none;
    pointer-events: none;
}

.wave-overlay.active {
    display: block;
    animation: waveAnim 1.5s ease-in-out;
}

@keyframes waveAnim {
    0% { transform: scale(0.92); opacity: 0; }
    40% { transform: scale(1.03); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}

.loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(3, 10, 18, 0.52);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 60;
}

.loading-spinner {
    width: 62px;
    height: 62px;
    border: 4px solid rgba(184, 220, 209, 0.18);
    border-top-color: var(--grid-gold);
    border-right-color: var(--energy-green);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.hidden {
    display: none !important;
}

.question-panel {
    position: fixed !important;
    top: 52% !important;
    transform: translateY(-50%) !important;
    z-index: 30 !important;
    width: 20vw !important;
    max-width: 460px !important;
    min-width: 340px !important;
    max-height: 76vh !important;
    overflow-y: auto !important;
    padding: 24px 22px 26px !important;
    color: var(--paper) !important;
    background:
        linear-gradient(180deg, rgba(6, 24, 39, 0.90), rgba(3, 36, 39, 0.86));
    border: 1px solid rgba(184, 220, 209, 0.24) !important;
    border-radius: 8px !important;
    box-shadow: 0 18px 52px rgba(0, 0, 0, 0.46), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    pointer-events: auto !important;
}

.question-panel::before {
    content: "";
    position: absolute;
    inset: 8px;
    border: 1px solid rgba(22, 167, 131, 0.15);
    border-radius: 6px;
    pointer-events: none;
}

.panel-left {
    left: 42px !important;
}

.panel-right {
    right: 42px !important;
}

.panel-title {
    position: relative;
    z-index: 1;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: rgba(251, 254, 253, 0.94) !important;
    padding: 0 0 18px !important;
    margin: 0 0 16px !important;
    border-bottom: 1px solid rgba(184, 220, 209, 0.18) !important;
    text-align: center !important;
    letter-spacing: 0 !important;
}

.panel-title::after {
    content: "";
    position: absolute;
    left: 50%;
    bottom: -1px;
    width: 92px;
    height: 2px;
    transform: translateX(-50%);
    background: linear-gradient(90deg, transparent, var(--grid-gold), transparent);
}

.q-btn {
    position: relative !important;
    z-index: 1 !important;
    width: 100% !important;
    min-height: 78px !important;
    margin: 10px 0 !important;
    padding: 16px 18px !important;
    font-size: 20px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    text-align: left !important;
    white-space: normal !important;
    color: rgba(251, 254, 253, 0.84) !important;
    background: rgba(251, 254, 253, 0.045) !important;
    border: 1px solid rgba(184, 220, 209, 0.13) !important;
    border-radius: 8px !important;
    box-shadow: inset 3px 0 0 rgba(22, 167, 131, 0.30) !important;
    cursor: pointer !important;
    transition: opacity 0.2s ease, background 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease, color 0.22s ease, transform 0.18s ease !important;
}

.q-btn:hover {
    color: #ffffff !important;
    background: rgba(11, 139, 120, 0.18) !important;
    border-color: rgba(22, 167, 131, 0.42) !important;
    box-shadow: inset 3px 0 0 var(--grid-gold), 0 10px 28px rgba(0, 0, 0, 0.22) !important;
    transform: translateX(2px);
}

.q-btn.active {
    color: #ffffff !important;
    background: linear-gradient(90deg, rgba(11, 139, 120, 0.30), rgba(30, 136, 209, 0.16)) !important;
    border-color: rgba(200, 137, 43, 0.54) !important;
    box-shadow: inset 3px 0 0 var(--grid-gold), 0 12px 34px rgba(11, 139, 120, 0.28) !important;
}

.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    z-index: 30;
    padding: 10px 0;
    background: rgba(0,0,0,0.45);
    color: rgba(255,255,255,0.5);
    text-align: center;
    font-size: 14px;
    pointer-events: none;
}

.question-panel::-webkit-scrollbar {
    width: 4px;
}
.question-panel::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.04);
}
.question-panel::-webkit-scrollbar-thumb {
    background: rgba(200, 137, 43, 0.34);
    border-radius: 2px;
}
.question-panel::-webkit-scrollbar-thumb:hover {
    background: rgba(200, 137, 43, 0.54);
}

.answer-caption {
    position: absolute;
    bottom: 9.2%;
    left: 50%;
    z-index: 36;
    width: min(58vw, 1240px);
    min-height: 132px;
    transform: translateX(-50%) translateY(0);
    padding: 20px 36px 22px;
    text-align: left;
    color: var(--paper);
    background:
        linear-gradient(180deg, rgba(3, 22, 29, 0.90), rgba(6, 24, 39, 0.86));
    border: 1px solid rgba(184, 220, 209, 0.22);
    border-top: 2px solid rgba(200, 137, 43, 0.74);
    border-radius: 8px;
    box-shadow: 0 20px 54px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    opacity: 1;
    pointer-events: none;
    transition: opacity 0.32s ease, transform 0.38s ease;
}

.answer-caption::before {
    content: "AI 数字讲解员";
    display: block;
    margin-bottom: 9px;
    font-size: 15px;
    font-weight: 700;
    color: rgba(184, 220, 209, 0.78);
}

.answer-caption.updating {
    opacity: 0;
    transform: translateX(-50%) translateY(8px);
}

.caption-question {
    margin-bottom: 10px;
    padding-bottom: 10px;
    font-size: 18px;
    font-weight: 700;
    color: rgba(218, 184, 101, 0.98);
    border-bottom: 1px solid rgba(200, 137, 43, 0.20);
    letter-spacing: 0;
}

.caption-answer {
    font-size: 21px;
    font-weight: 400;
    color: rgba(251, 254, 253, 0.92);
    line-height: 1.65;
    letter-spacing: 0;
}

.caption-answer .answer-seg {
    display: inline;
    opacity: 0;
    animation: segFadeIn 0.36s ease forwards;
}
.caption-answer .answer-seg:first-child { animation-delay: 0.05s; }

@keyframes segFadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.stop-btn {
    position: fixed;
    right: 42px;
    top: 24%;
    z-index: 61;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-width: 196px;
    padding: 17px 30px;
    font-size: 21px;
    font-weight: 600;
    letter-spacing: 2px;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    color: rgba(255, 255, 255, 0.97);
    background: linear-gradient(135deg, rgba(196, 74, 58, 0.90), rgba(150, 42, 33, 0.92));
    border: 1px solid rgba(255, 186, 168, 0.42);
    border-radius: 10px;
    box-shadow: 0 14px 40px rgba(170, 48, 38, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    cursor: pointer;
    opacity: 0;
    transform: translateY(12px);
    pointer-events: none;
    transition: opacity 0.32s ease, transform 0.32s ease, box-shadow 0.22s ease, background 0.22s ease, border-color 0.22s ease;
}

.stop-btn.visible {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
}

.stop-btn:hover {
    background: linear-gradient(135deg, rgba(216, 88, 72, 0.96), rgba(176, 54, 44, 0.96));
    border-color: rgba(200, 137, 43, 0.62);
    box-shadow: 0 18px 48px rgba(196, 62, 50, 0.58), inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.stop-btn:active {
    transform: translateY(1px);
}

/* 图标基类 */
.stop-btn .btn-icon {
    display: inline-block;
    width: 18px;
    height: 18px;
    position: relative;
    flex-shrink: 0;
}

/* 暂停图标：两根竖条（默认显示，提示点击会暂停）*/
.stop-btn .icon-pause::before,
.stop-btn .icon-pause::after {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    width: 5px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 1px;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.40);
}
.stop-btn .icon-pause::before { left: 3px; }
.stop-btn .icon-pause::after { right: 3px; }

/* 继续图标：三角形（默认隐藏）*/
.stop-btn .icon-play {
    display: none;
    width: 0;
    height: 0;
    border-left: 17px solid rgba(255, 255, 255, 0.95);
    border-top: 9px solid transparent;
    border-bottom: 9px solid transparent;
    margin-left: 3px;
    filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.40));
}

/* 已暂停态：切换为"继续"图标 */
.stop-btn.is-paused .icon-pause { display: none; }
.stop-btn.is-paused .icon-play { display: inline-block; }

/* ============ 语音对话按钮 ============ */
.voice-chat-btn {
    position: fixed;
    left: 42px;
    top: 24%;
    z-index: 61;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-width: 196px;
    padding: 17px 30px;
    font-size: 21px;
    font-weight: 600;
    letter-spacing: 2px;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    color: rgba(255, 255, 255, 0.97);
    background: linear-gradient(135deg, rgba(11, 139, 120, 0.90), rgba(7, 91, 86, 0.92));
    border: 1px solid rgba(184, 220, 209, 0.42);
    border-radius: 10px;
    box-shadow: 0 14px 40px rgba(11, 139, 120, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    cursor: pointer;
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
    /* PTT：阻止触屏滚动/手势，保证 pointer 事件不被浏览器打断 */
    touch-action: none;
    transition: opacity 0.32s ease, transform 0.32s ease, box-shadow 0.22s ease, background 0.22s ease, border-color 0.22s ease;
}

.voice-chat-btn:hover {
    background: linear-gradient(135deg, rgba(22, 167, 131, 0.96), rgba(11, 139, 120, 0.96));
    border-color: rgba(200, 137, 43, 0.62);
    box-shadow: 0 18px 48px rgba(11, 139, 120, 0.58), inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.voice-chat-btn:active {
    transform: translateY(1px);
}

/* 聆听态：蓝绿呼吸脉冲 */
.voice-chat-btn.listening {
    background: linear-gradient(135deg, rgba(30, 136, 209, 0.90), rgba(22, 167, 131, 0.88));
    border-color: rgba(100, 200, 255, 0.62);
    box-shadow: 0 14px 40px rgba(30, 136, 209, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.18);
    animation: voicePulse 1.8s ease-in-out infinite;
}

.voice-chat-btn.listening:hover {
    background: linear-gradient(135deg, rgba(40, 150, 230, 0.96), rgba(22, 167, 131, 0.94));
}

@keyframes voicePulse {
    0%, 100% { box-shadow: 0 14px 40px rgba(30, 136, 209, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.14); }
    50% { box-shadow: 0 14px 60px rgba(30, 136, 209, 0.72), inset 0 1px 0 rgba(255, 255, 255, 0.28); }
}

/* 处理态：金色等待 */
.voice-chat-btn.processing {
    background: linear-gradient(135deg, rgba(200, 137, 43, 0.85), rgba(160, 100, 20, 0.82));
    border-color: rgba(200, 137, 43, 0.62);
    box-shadow: 0 14px 40px rgba(200, 137, 43, 0.50), inset 0 1px 0 rgba(255, 255, 255, 0.16);
    cursor: wait;
    pointer-events: none;
}

/* 语音按钮图标 */
.voice-chat-btn .voice-icon {
    display: inline-block;
    width: 20px;
    height: 20px;
    position: relative;
    flex-shrink: 0;
}

/* 麦克风图标（默认：待机） */
.voice-chat-btn .icon-mic {
    display: block;
    width: 12px;
    height: 18px;
    margin: 1px auto 0;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 6px;
    position: relative;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.40);
}
.voice-chat-btn .icon-mic::after {
    content: "";
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    width: 18px;
    height: 4px;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 2px;
}

/* 聆听态：显示声波动画图标，隐藏麦克风 */
.voice-chat-btn.listening .icon-mic { display: none; }
.voice-chat-btn.listening .icon-wave {
    display: block;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 2px;
}
.voice-chat-btn.listening .icon-wave span {
    display: inline-block;
    width: 3px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 1px;
    animation: waveBar 0.8s ease-in-out infinite;
}
.voice-chat-btn.listening .icon-wave span:nth-child(1) { height: 8px; animation-delay: 0s; }
.voice-chat-btn.listening .icon-wave span:nth-child(2) { height: 14px; animation-delay: 0.15s; }
.voice-chat-btn.listening .icon-wave span:nth-child(3) { height: 10px; animation-delay: 0.3s; }
.voice-chat-btn.listening .icon-wave span:nth-child(4) { height: 16px; animation-delay: 0.45s; }

@keyframes waveBar {
    0%, 100% { transform: scaleY(0.6); opacity: 0.5; }
    50% { transform: scaleY(1); opacity: 1; }
}

/* 默认隐藏声波 */
.icon-wave { display: none; }

/* 处理态图标 */
.voice-chat-btn.processing .icon-mic { display: none; }
.voice-chat-btn.processing .icon-wave { display: none; }
.voice-chat-btn.processing .icon-spinner {
    display: block;
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.25);
    border-top-color: rgba(255, 255, 255, 0.95);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
.icon-spinner { display: none; }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""

# ============================================
# AudioWorklet PCM 处理器代码（内联为 Blob URL 加载）
# 注意：此处为纯 JS，用 Python r-string 避免转义，通过 json.dumps 安全注入到前端 JS
# ============================================
PCM_WORKLET_JS = (
    "class PcmProcessor extends AudioWorkletProcessor {\n"
    "    process(inputs) {\n"
    "        const input = inputs[0];\n"
    "        if (input && input.length > 0) {\n"
    "            const channel = input[0];\n"
    "            if (channel && channel.length > 0) {\n"
    "                const pcm = new Int16Array(channel.length);\n"
    "                for (let i = 0; i < channel.length; i++) {\n"
    "                    const s = Math.max(-1, Math.min(1, channel[i]));\n"
    "                    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;\n"
    "                }\n"
    "                try { this.port.postMessage(pcm.buffer, [pcm.buffer]); }\n"
    "                catch(e) { /* 传输失败静默降级 */ }\n"
    "            }\n"
    "        }\n"
    "        return true;\n"
    "    }\n"
    "}\n"
    "registerProcessor('pcm-processor', PcmProcessor);\n"
)

# ============================================
# JavaScript - 视频切换 + 挥手动画
# ============================================

VIDEO_JS = """
var waveInterval = null;
var currentMode = 'idle';

// idle 摆臂节奏：idle.mp4 播完后随机停顿 IDLE_PAUSE_MIN~MAX 秒再重播，避免摆臂过于频繁
var IDLE_PAUSE_MIN = {idle_pause_min};
var IDLE_PAUSE_MAX = {idle_pause_max};
var idlePauseTimer = null;

/* 启动 idle 的"播放-停顿-重播"循环，替代无缝 loop */
function startIdleLoop(video) {{
    if (!video) return;
    video.loop = false;
    video.onended = function () {{
        // 播完冻结在最后一帧（站姿），随机停顿后重播
        var pauseMs = (IDLE_PAUSE_MIN + Math.random() * (IDLE_PAUSE_MAX - IDLE_PAUSE_MIN)) * 1000;
        clearTimeout(idlePauseTimer);
        idlePauseTimer = setTimeout(function () {{
            if (currentMode !== 'idle') return;
            try {{ video.currentTime = 0; }} catch (e) {{}}
            video.play().catch(function (e) {{}});
        }}, pauseMs);
    }};
}}

/* 停止 idle 循环，清除停顿定时器（切到 talking 时调用）*/
function stopIdleLoop() {{
    clearTimeout(idlePauseTimer);
    idlePauseTimer = null;
}}

// 注入双图层交叉淡入时长（来自 kiosk_config.VIDEO_TRANSITION），覆盖 CSS 默认值
document.documentElement.style.setProperty('--video-transition', '{opacity_ms}ms');

/* 双图层交叉切换：激活 newActive、淡出 oldActive；500ms 后清空旧层 src 并交换 id，
   维持"活跃层恒为 videoBack"不变式。供 idle↔talking 与 talking→xunhuan 复用。*/
function swapLayers(newActive, oldActive) {{
    oldActive.classList.remove('active');
    oldActive.classList.add('inactive');
    newActive.classList.remove('inactive');
    newActive.classList.add('active');
    setTimeout(function() {{
        oldActive.src = '';
        var tempId = oldActive.id;
        oldActive.id = newActive.id;
        newActive.id = tempId;
    }}, 500);
}}

/* ============ 问题管理（固定显示，不随机）============ */
var ALL_QUESTIONS = {all_questions};
// 固定 8 题：左栏常见问题 xq01-xq04，右栏热点问答 xq05-xq08
var FIXED_QUESTION_IDS = ['xq01','xq02','xq03','xq04','xq05','xq06','xq07','xq08'];
var currentQuestions = FIXED_QUESTION_IDS.map(function(id) {{
    return ALL_QUESTIONS.find(function(q) {{ return q.id === id; }});
}}).filter(Boolean);

/* 渲染固定问题到按钮（左4 + 右4，带淡入淡出）*/
function refreshQuestionButtons() {{
    var btns = document.querySelectorAll('.q-btn');
    // 淡出
    btns.forEach(function(b) {{ b.style.opacity = '0'; }});
    setTimeout(function() {{
        for (var i = 0; i < btns.length && i < currentQuestions.length; i++) {{
            btns[i].textContent = currentQuestions[i].question;
        }}
        // 淡入
        setTimeout(function() {{
            btns.forEach(function(b) {{ b.style.opacity = '1'; }});
        }}, 50);
    }}, 200);
}}

/* 点击问题按钮（固定显示：仅高亮当前题并播放回答，不刷新其余按钮）*/
function onQuestionClick(btnIndex) {{
    if (btnIndex >= currentQuestions.length) return;
    var q = currentQuestions[btnIndex];

    showCaption(q.question, q.answer);
    // 切换到 talking 视频层（静音循环），就绪后播放 mp3 配音（音频为回答主时钟）
    switchToTalking(function () {{
        var speakAudio = document.getElementById('speakAudio');
        if (speakAudio && q && q.id) {{
            speakAudio.onended = function () {{
                if (currentMode === 'talking') switchToIdle();
            }};
            speakAudio.src = '/gradio_api/file={speak_audio_dir}/' + q.id + '.mp3';
            speakAudio.load();
            speakAudio.play().catch(function (e) {{}});
        }}
    }});
    var btns = document.querySelectorAll('.q-btn');
    btns.forEach(function(b) {{ b.classList.remove('active'); }});
    if (btns[btnIndex]) btns[btnIndex].classList.add('active');
}}

/* 切换到回答模式 - 播放 talking.mp4（静音循环），音频播完后由调用方切回 idle。
   onReady：视频层激活后的回调（预设问题在此启动 mp3；语音对话可省略）*/
function switchToTalking(onReady) {{
    var backVideo = document.getElementById('videoBack');
    var frontVideo = document.getElementById('videoFront');
    var loading = document.getElementById('loadingOverlay');

    if (!frontVideo || !backVideo) return;
    currentMode = 'talking';
    updateStopButton();  // 显示"暂停回答"按钮
    isPaused = false;    // 新回答从头播放，重置暂停态
    setStopButtonState(false);
    stopIdleLoop();  // 清除 idle 摆臂停顿定时器
    stopWaveAnimation();

    if (loading) loading.classList.remove('hidden');

    // talking.mp4：静音 + 循环（音频由 speakAudio/TTS 独立驱动，作为主时钟）
    backVideo.loop = true;
    backVideo.muted = true;
    backVideo.oncanplaythrough = null;
    backVideo.onended = null;
    backVideo.src = '/gradio_api/file={talking_video}';
    backVideo.load();

    backVideo.oncanplaythrough = function() {{
        backVideo.oncanplaythrough = null;

        backVideo.play().catch(function(e){{}});

        // 等待首帧渲染后再切换图层（避免闪现空白帧）
        var swap = function() {{
            swapLayers(backVideo, frontVideo);
            startWaveAnimation();
        }};

        if (backVideo.requestVideoFrameCallback) {{
            backVideo.requestVideoFrameCallback(swap);
            setTimeout(function() {{
                if (backVideo.classList.contains('inactive')) swap();
            }}, 100);
        }} else {{
            setTimeout(swap, 40);
        }}

        // 视频层已激活，触发音频播放（预设问题）/ 标记说话开始（语音对话）
        if (onReady) {{ try {{ onReady(); }} catch(e) {{}} }}

        setTimeout(function(){{ if (loading) loading.classList.add('hidden'); }}, 300);
    }};
}}

/* 切换到待机模式 - 循环播放 idle.mp4
   refreshQuestions: 是否刷新问题列表（自然播完=true；手动停止=false，避免按钮闪烁）*/
function switchToIdle(refreshQuestions) {{
    if (refreshQuestions === undefined) refreshQuestions = true;
    var backVideo = document.getElementById('videoBack');
    var frontVideo = document.getElementById('videoFront');
    currentMode = 'idle';
    updateStopButton();  // 隐藏"暂停回答"按钮
    isPaused = false;    // 重置暂停态，下次回答从头开始
    setStopButtonState(false);
    stopWaveAnimation();

    // 停止讲话音频并彻底解绑事件（从 talking/xunhuan 循环态切出时避免回调串扰）
    var speakAudio = document.getElementById('speakAudio');
    if (speakAudio) {{
        speakAudio.onended = null;
        speakAudio.pause();
        try {{ speakAudio.currentTime = 0; }} catch (e) {{}}
    }}
    // 清理语音对话 TTS 音频队列（停止当前播放 + 清空排队帧）
    resetAudioQueue();
    // 清理两个图层残留的视频事件（xunhuan 循环态可能挂在另一图层上）
    ['videoBack', 'videoFront'].forEach(function(id) {{
        var v = document.getElementById(id);
        if (v) {{ v.onended = null; v.oncanplaythrough = null; }}
    }});

    // 移除按钮高亮 + 重置字幕（手动停止时不刷新问题列表，避免按钮闪烁）
    document.querySelectorAll('.q-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    resetCaption();
    if (refreshQuestions) refreshQuestionButtons();

    stopIdleLoop();
    // idle 加载到空闲层 frontVideo：活跃层 videoBack 仍显示 output，避免加载期间空白；
    // 就绪后 swapLayers 激活 frontVideo（与 switchToTalking 对称）
    frontVideo.muted = true;   // idle 不需要声音
    frontVideo.loop = false;  // 不无缝循环，由 startIdleLoop 接管：播完停顿再重播
    frontVideo.src = '/gradio_api/file={idle_video}';
    frontVideo.load();

    frontVideo.oncanplaythrough = function() {{
        frontVideo.oncanplaythrough = null;  // 防御性解绑
        // 先开始播放（此时 frontVideo 还是透明状态，活跃层 videoBack 仍显示上一段视频）
        frontVideo.play().catch(function(e){{}});

        // 接管 idle 循环：播完随机停顿再重播
        startIdleLoop(frontVideo);

        // 等待首帧渲染后再切换图层
        var swap = function() {{
            swapLayers(frontVideo, backVideo);  // 激活 frontVideo（idle），淡出 backVideo（talking/xunhuan）
        }};

        if (frontVideo.requestVideoFrameCallback) {{
            frontVideo.requestVideoFrameCallback(swap);
            setTimeout(function() {{
                if (frontVideo.classList.contains('inactive')) swap();
            }}, 100);
        }} else {{
            setTimeout(swap, 40);
        }}
    }};
}}

/* 启动随机挥手动画 */
function startWaveAnimation() {{
    if (currentMode !== 'talking') return;

    var waveOverlay = document.getElementById('waveOverlay');
    var waveVideos = {wave_videos};

    // 随机生成间隔
    var minInterval = {min_interval};
    var maxInterval = {max_interval};
    var randomInterval = Math.floor(Math.random() * (maxInterval - minInterval + 1)) + minInterval;

    waveInterval = setTimeout(function() {{
        if (currentMode === 'talking') {{
            // 随机选择挥手视频
            var waveSrc = '/gradio_api/file=' + waveVideos[Math.floor(Math.random() * waveVideos.length)];
            waveOverlay.innerHTML = '<video autoplay style="width:100%;height:100%;object-fit:contain;" src="' + waveSrc + '"></video>';
            waveOverlay.classList.add('active');

            // 挥手结束后移除
            setTimeout(function() {{
                waveOverlay.classList.remove('active');
            }}, 1500);

            // 继续随机挥手
            startWaveAnimation();
        }}
    }}, randomInterval * 1000);
}}

/* 停止挥手动画 */
function stopWaveAnimation() {{
    if (waveInterval) {{
        clearTimeout(waveInterval);
        waveInterval = null;
    }}
    var waveOverlay = document.getElementById('waveOverlay');
    if (waveOverlay) waveOverlay.classList.remove('active');
}}

/* 显示/隐藏"暂停回答"按钮（仅 talking 模式可见）*/
function updateStopButton() {{
    var stopBtn = document.getElementById('stopAnswerBtn');
    if (!stopBtn) return;
    if (currentMode === 'talking') {{
        stopBtn.classList.add('visible');
    }} else {{
        stopBtn.classList.remove('visible');
    }}
}}

/* 更新按钮暂停/继续外观（图标 + 文字）*/
function setStopButtonState(paused) {{
    var stopBtn = document.getElementById('stopAnswerBtn');
    if (!stopBtn) return;
    var textEl = stopBtn.querySelector('.btn-text');
    if (paused) {{
        stopBtn.classList.add('is-paused');
        if (textEl) textEl.textContent = '继续回答';
    }} else {{
        stopBtn.classList.remove('is-paused');
        if (textEl) textEl.textContent = '暂停回答';
    }}
}}

/* 暂停/继续切换：同步控制 talking 视频图层 + 预设配音 mp3 + 语音对话 TTS 音频队列 */
var isPaused = false;
function togglePauseAnswer() {{
    if (currentMode !== 'talking') return;
    var activeVideo = document.querySelector('.video-layer.active');
    var speakAudio = document.getElementById('speakAudio');
    if (!isPaused) {{
        // 播放中 → 暂停（视频 + 预设配音 + TTS 音频同步停）
        if (activeVideo) activeVideo.pause();
        if (speakAudio && !speakAudio.paused) speakAudio.pause();
        if (_currentAudioEl) _currentAudioEl.pause();
        isPaused = true;
        setStopButtonState(true);
    }} else {{
        // 暂停中 → 继续
        if (activeVideo) activeVideo.play().catch(function (e) {{}});
        if (speakAudio && speakAudio.src) speakAudio.play().catch(function (e) {{}});
        if (_currentAudioEl) _currentAudioEl.play().catch(function (e) {{}});
        isPaused = false;
        setStopButtonState(false);
    }}
}}

/* 显示答案字幕（分段交错渐显）*/
function showCaption(question, answer) {{
    var caption = document.getElementById('answerCaption');
    var qEl = document.getElementById('captionQuestion');
    var aEl = document.getElementById('captionAnswer');
    // 先淡出
    if (caption) caption.classList.add('updating');
    setTimeout(function() {{
        if (qEl) qEl.textContent = question;
        if (aEl) {{
            // 将答案按句子拆分，每句包裹 span 并设延迟
            var segs = answer.split(/(?<=[。！？；])/);
            var html = '';
            for (var i = 0; i < segs.length; i++) {{
                if (segs[i].trim()) {{
                    var delay = (i * 0.12).toFixed(2);
                    html += '<span class="answer-seg" style="animation-delay:' + delay + 's">' + segs[i] + '</span>';
                }}
            }}
            aEl.innerHTML = html || answer;
        }}
        if (caption) caption.classList.remove('updating');
    }}, 200);
}}

/* 恢复欢迎语 */
function resetCaption() {{
    var caption = document.getElementById('answerCaption');
    var qEl = document.getElementById('captionQuestion');
    var aEl = document.getElementById('captionAnswer');
    if (caption) caption.classList.add('updating');
    setTimeout(function() {{
        if (qEl) qEl.textContent = '欢迎使用智能问答';
        if (aEl) aEl.innerHTML = '点击左右两侧问题，开启智慧电力探索之旅';
        if (caption) caption.classList.remove('updating');
    }}, 200);
}}

/* 页面加载：等待 Gradio 渲染完成后初始化 */
(function initWhenReady() {{
    var btns = document.querySelectorAll('.q-btn');
    if (btns.length >= {display_count}) {{
        refreshQuestionButtons();

        // 初始 idle 视频接管为"播放-停顿-重播"循环（HTML 已去掉 loop）
        var initFront = document.getElementById('videoFront');
        if (initFront) {{
            startIdleLoop(initFront);
            // 视频可能已 autoplay 播完停住，重置并重播一次以启动循环
            try {{ initFront.currentTime = 0; }} catch (e) {{}}
            initFront.play().catch(function (e) {{}});
        }}

        // 预加载 talking.mp4 到浏览器缓存，后续切换瞬间就绪
        ['{talking_video}'].forEach(function(src) {{
            var preloadVideo = document.createElement('video');
            preloadVideo.preload = 'auto';
            preloadVideo.style.display = 'none';
            preloadVideo.src = '/gradio_api/file=' + src;
            preloadVideo.load();
            setTimeout(function() {{ document.body.contains(preloadVideo) && preloadVideo.remove(); }}, 3000);
        }});
    }} else {{
        setTimeout(initWhenReady, 150);
    }}
}})();
/* ============ 语音对话（ASR → LLM → TTS）内网版 ============ */
var voiceState = {{
    listening: false,
    processing: false,
    sessionId: (typeof crypto !== 'undefined' && crypto.randomUUID)
        ? crypto.randomUUID()
        : 's-' + Date.now(),
    chatWs: null,
    audioCtx: null,
    pcmNode: null,
    stream: null,
    pcmChunks: [],    // 录音缓冲区：Int16Array 数组
    cancelled: false,  // PTT：滑出取消标记
    error: null
}};

/* 获取 DOM 元素 */
function getVoiceBtn() {{ return document.getElementById('voiceChatBtn'); }}
function getVoiceBtnText() {{ return document.getElementById('voiceBtnText'); }}

/* 更新语音按钮状态 */
function setVoiceButtonState(state) {{
    var btn = getVoiceBtn();
    var text = getVoiceBtnText();
    if (!btn || !text) return;
    btn.classList.remove('listening', 'processing');
    if (state === 'listening') {{
        btn.classList.add('listening');
        text.textContent = '松开发送';
    }} else if (state === 'processing') {{
        btn.classList.add('processing');
        text.textContent = '正在生成回复...';
    }} else {{
        text.textContent = '按住说话';
    }}
    voiceState.listening = (state === 'listening');
    voiceState.processing = (state === 'processing');
}}

/* 在字幕区显示语音对话内容 */
function showVoiceCaption(label, content) {{
    var caption = document.getElementById('answerCaption');
    var qEl = document.getElementById('captionQuestion');
    var aEl = document.getElementById('captionAnswer');
    if (caption) caption.classList.remove('updating');
    if (qEl) qEl.textContent = label;
    if (aEl) aEl.textContent = content;
}}

/* ============ WAV 编码（PCM 16bit/16kHz/mono → WAV bytes）============ */

function pcmToWav(pcmData) {{
    var dataLength = pcmData.length * 2;  // Int16Array → 字节数
    var buffer = new ArrayBuffer(44 + dataLength);
    var view = new DataView(buffer);

    function writeStr(offset, str) {{
        for (var i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
    }}

    writeStr(0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeStr(8, 'WAVE');
    writeStr(12, 'fmt ');
    view.setUint32(16, 16, true);           // PCM fmt size
    view.setUint16(20, 1, true);            // PCM = 1
    view.setUint16(22, 1, true);            // mono
    view.setUint32(24, 16000, true);        // sample rate
    view.setUint32(28, 32000, true);        // byte rate
    view.setUint16(32, 2, true);            // block align
    view.setUint16(34, 16, true);           // bits per sample
    writeStr(36, 'data');
    view.setUint32(40, dataLength, true);

    var pcmView = new DataView(buffer, 44);
    for (var i = 0; i < pcmData.length; i++) {{
        pcmView.setInt16(i * 2, pcmData[i], true);
    }}
    return buffer;
}}

function arrayBufferToBase64(buffer) {{
    var bytes = new Uint8Array(buffer);
    var binary = '';
    for (var i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary);
}}

/* ============ 音频播放（WAV base64 顺序播放队列）============ */

var _audioQueue = [];
var _audioPlaying = false;
var _currentAudioEl = null;     // 当前正在播放的 Audio 元素引用（供暂停按钮控制）
var _voiceAudioDrained = false; // 语音对话 done 已收到，等待 TTS 音频排空后切回 idle

function _playNextAudio() {{
    if (_audioQueue.length === 0) {{
        _audioPlaying = false;
        _currentAudioEl = null;
        _checkVoiceAudioDrained();
        return;
    }}
    _audioPlaying = true;
    var b64 = _audioQueue.shift();
    var audio = new Audio('data:audio/wav;base64,' + b64);
    _currentAudioEl = audio;
    audio.onended = function() {{ _currentAudioEl = null; _playNextAudio(); }};
    audio.onerror = function() {{ _currentAudioEl = null; _playNextAudio(); }};
    audio.play().catch(function() {{ _currentAudioEl = null; _playNextAudio(); }});
}}

function enqueueAudioPlayback(b64Data) {{
    _audioQueue.push(b64Data);
    if (!_audioPlaying) _playNextAudio();
}}

/* 检查语音对话 TTS 音频是否已全部播完 → 切回 idle */
function _checkVoiceAudioDrained() {{
    if (_voiceAudioDrained && !_audioPlaying && _audioQueue.length === 0) {{
        _voiceAudioDrained = false;
        if (currentMode === 'talking') switchToIdle(false);
    }}
}}

function resetAudioQueue() {{
    _audioQueue = [];
    _audioPlaying = false;
    if (_currentAudioEl) {{ try {{ _currentAudioEl.pause(); }} catch(e) {{}} }}
    _currentAudioEl = null;
    _voiceAudioDrained = false;
}}

/* ============ 音频采集（PCM 缓冲）============ */

/* AudioWorklet 处理器代码（内联为 Blob URL 加载） */
var PCM_WORKLET_CODE = {pcm_worklet_json};

function _getWorkletUrl() {{
    var blob = new Blob([PCM_WORKLET_CODE], {{ type: 'application/javascript' }});
    return URL.createObjectURL(blob);
}}

/* 开始录音：采集 PCM 数据到内存缓冲区 */
async function startVoiceCapture() {{
    try {{
        voiceState.error = null;
        voiceState.pcmChunks = [];

        // 1. 获取麦克风权限（16kHz 单声道）
        var media = await navigator.mediaDevices.getUserMedia({{
            audio: {{ channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true }}
        }});
        voiceState.stream = media;

        // 2. 创建采集 AudioContext
        voiceState.audioCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
        var ctx = voiceState.audioCtx;

        // 3. 加载 PCM 工作集 → 将 PCM 写入缓冲区
        var workletUrl = _getWorkletUrl();
        await ctx.audioWorklet.addModule(workletUrl);
        URL.revokeObjectURL(workletUrl);

        // 4. 创建工作集节点 → 收集 PCM 到 pcmChunks
        var source = ctx.createMediaStreamSource(media);
        var node = new AudioWorkletNode(ctx, 'pcm-processor');
        voiceState.pcmNode = node;
        node.port.onmessage = function(e) {{
            if (voiceState.listening && e.data) {{
                voiceState.pcmChunks.push(new Int16Array(e.data));
            }}
        }};
        source.connect(node);
        node.connect(ctx.destination);  // 保持节点活跃

        // 取消竞态：若 await 期间用户已滑出取消（listening=false），立即回收刚申请的资源，避免麦指示灯常亮
        if (!voiceState.listening) {{
            try {{ node.disconnect(); }} catch(_e) {{}}
            media.getTracks().forEach(function(t) {{ t.stop(); }});
            ctx.close().catch(function(){{}});
            voiceState.pcmNode = null;
            voiceState.stream = null;
            voiceState.audioCtx = null;
            return true;
        }}

        return true;
    }} catch(e) {{
        voiceState.error = String(e);
        showVoiceCaption('麦克风错误', '无法访问麦克风：' + voiceState.error);
        setVoiceButtonState('idle');
        return false;
    }}
}}

/* 停止录音 → 合并 PCM → 编码 WAV → POST /asr → 启动 Chat */
function stopVoiceCaptureAndRecognize() {{
    // 关闭 PCM 节点
    if (voiceState.pcmNode) {{
        try {{ voiceState.pcmNode.disconnect(); }} catch(e) {{}}
        voiceState.pcmNode = null;
    }}
    // 停止麦克风
    if (voiceState.stream) {{
        voiceState.stream.getTracks().forEach(function(t) {{ t.stop(); }});
        voiceState.stream = null;
    }}
    // 关闭采集 AudioContext
    if (voiceState.audioCtx) {{
        voiceState.audioCtx.close().catch(function(){{}});
        voiceState.audioCtx = null;
    }}
    voiceState.listening = false;

    // 合并所有 PCM 块
    var totalLen = 0;
    voiceState.pcmChunks.forEach(function(c) {{ totalLen += c.length; }});
    if (totalLen === 0) {{
        setVoiceButtonState('idle');
        showVoiceCaption('语音对话', '未检测到语音内容，请重试。');
        return;
    }}
    var merged = new Int16Array(totalLen);
    var offset = 0;
    voiceState.pcmChunks.forEach(function(c) {{
        merged.set(c, offset);
        offset += c.length;
    }});
    voiceState.pcmChunks = [];

    // 编码为 WAV
    var wavBuf = pcmToWav(merged);
    var wavBase64 = arrayBufferToBase64(wavBuf);

    // HTTP POST 到 /asr
    fetch('/asr', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/octet-stream' }},
        body: wavBuf
    }})
    .then(function(resp) {{
        if (!resp.ok) throw new Error('ASR HTTP ' + resp.status);
        return resp.json();
    }})
    .then(function(data) {{
        var recognized = (data.text || '').trim();
        if (recognized) {{
            showVoiceCaption('语音识别', recognized);
            startChatStream(recognized);
        }} else {{
            setVoiceButtonState('idle');
            showVoiceCaption('语音对话', '未识别到语音内容，请重试。');
        }}
    }})
    .catch(function(err) {{
        voiceState.error = String(err);
        showVoiceCaption('识别错误', '语音识别失败：' + voiceState.error);
        setVoiceButtonState('idle');
    }});
}}

/* 取消录音：回收采集资源但不提交识别（按下后滑出按钮时调用） */
function cancelVoiceCapture() {{
    // 关闭 PCM 节点
    if (voiceState.pcmNode) {{
        try {{ voiceState.pcmNode.disconnect(); }} catch(e) {{}}
        voiceState.pcmNode = null;
    }}
    // 停止麦克风
    if (voiceState.stream) {{
        voiceState.stream.getTracks().forEach(function(t) {{ t.stop(); }});
        voiceState.stream = null;
    }}
    // 关闭采集 AudioContext
    if (voiceState.audioCtx) {{
        voiceState.audioCtx.close().catch(function(){{}});
        voiceState.audioCtx = null;
    }}
    voiceState.listening = false;
    voiceState.pcmChunks = [];   // 丢弃本次 PCM
    setVoiceButtonState('idle');
    showVoiceCaption('语音对话', '已取消');
}}

/* ============ Chat 流式对话（LLM + TTS）============ */

function startChatStream(text) {{
    setVoiceButtonState('processing');
    showVoiceCaption('AI 语音助手', '思考中...');
    resetAudioQueue();
    _voiceAudioDrained = false;
    var talkingStarted = false;  // 首个 text/audio 到达后切换到 talking 视频层

    var protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    var chatWs = new WebSocket(protocol + '://' + location.host + '/chat/stream');
    voiceState.chatWs = chatWs;
    var replyText = '';

    /* 切换到 talking 视频层（静音循环），仅切换一次 */
    function ensureTalkingStarted() {{
        if (talkingStarted) return;
        talkingStarted = true;
        switchToTalking();
    }}

    chatWs.onopen = function() {{
        chatWs.send(JSON.stringify({{ session_id: voiceState.sessionId, text: text }}));
    }};

    chatWs.onmessage = function(ev) {{
        if (typeof ev.data !== 'string') return;
        try {{
            var msg = JSON.parse(ev.data);
            if (msg.event === 'text') {{
                ensureTalkingStarted();  // LLM 开始输出 → 数字人进入说话姿态
                replyText += (msg.delta || '');
                showVoiceCaption('AI 语音助手', replyText);
            }} else if (msg.event === 'audio') {{
                // base64 WAV 音频 → 排队播放
                if (msg.data) enqueueAudioPlayback(msg.data);
            }} else if (msg.event === 'done') {{
                // LLM + TTS 均结束：标记排空，等音频播完切回 idle（无音频则立即切回）
                setVoiceButtonState('idle');
                if (!replyText) {{
                    showVoiceCaption('AI 语音助手', '(无回复内容)');
                    if (currentMode === 'talking') switchToIdle(false);
                }} else {{
                    _voiceAudioDrained = true;
                    _checkVoiceAudioDrained();
                }}
            }} else if (msg.event === 'error') {{
                voiceState.error = msg.message || '语音合成出错';
                showVoiceCaption('合成错误', voiceState.error);
                setVoiceButtonState('idle');
                if (currentMode === 'talking') switchToIdle(false);
            }}
        }} catch(e) {{ /* 忽略非 JSON */ }}
    }};

    chatWs.onerror = function() {{
        voiceState.error = '对话服务连接失败';
        showVoiceCaption('连接错误', voiceState.error);
        setVoiceButtonState('idle');
        if (currentMode === 'talking') switchToIdle(false);
    }};

    chatWs.onclose = function() {{
        voiceState.chatWs = null;
    }};
}}

/* ============ 按住说话（Press-to-Talk）事件处理 ============ */

/* 按下：开始录音 */
function onVoicePressStart(e) {{
    e.preventDefault();
    // 释放触屏隐式指针捕获，使 pointerleave 在手指移出按钮时正常触发（滑出取消功能依赖此事件）
    if (e.currentTarget.hasPointerCapture && e.currentTarget.hasPointerCapture(e.pointerId)) {{
        e.currentTarget.releasePointerCapture(e.pointerId);
    }}
    // processing（识别/生成中）锁定，忽略按下
    if (voiceState.processing) return;
    // 已在录音中（同一指头按住）忽略
    if (voiceState.listening) return;

    voiceState.cancelled = false;

    // 准备新一轮语音交互：若当前正在播放（预设问题 mp3 / 上一轮 TTS），先停止音频与视频
    if (currentMode === 'talking') {{
        // 中断正在进行的对话 WebSocket（若有）
        if (voiceState.chatWs) {{
            try {{ voiceState.chatWs.close(); }} catch (err) {{}}
            voiceState.chatWs = null;
        }}
        // switchToIdle 会停止 mp3 + TTS 音频队列 + talking 视频，并切回 idle 待机画面
        switchToIdle(false);
    }}

    // 切聆听态 + 开始采集
    setVoiceButtonState('listening');
    showVoiceCaption('正在聆听...', '请说出您的问题...');
    startVoiceCapture().then(function(ok) {{
        if (!ok) setVoiceButtonState('idle');   // 麦克风授权失败已提示
    }});
}}

/* 在按钮上松开：提交识别 */
function onVoicePressEnd(e) {{
    e.preventDefault();
    if (!voiceState.listening) return;          // 已取消或未录音
    if (voiceState.cancelled) return;           // 滑出取消路径已处理

    setVoiceButtonState('processing');
    showVoiceCaption('语音识别', '正在识别...');
    stopVoiceCaptureAndRecognize();
}}

/* 滑出 / 被系统打断：立即取消，丢弃 PCM */
function onVoicePressCancel(e) {{
    if (!voiceState.listening) return;
    voiceState.cancelled = true;
    cancelVoiceCapture();
}}

/* 清理所有语音资源 */
function cleanupVoice() {{
    if (voiceState.pcmNode) {{
        try {{ voiceState.pcmNode.disconnect(); }} catch(e) {{}}
        voiceState.pcmNode = null;
    }}
    if (voiceState.stream) {{
        voiceState.stream.getTracks().forEach(function(t) {{ t.stop(); }});
        voiceState.stream = null;
    }}
    if (voiceState.audioCtx) {{
        voiceState.audioCtx.close().catch(function(){{}});
        voiceState.audioCtx = null;
    }}
    if (voiceState.chatWs) {{
        try {{ voiceState.chatWs.close(); }} catch(e) {{}}
        voiceState.chatWs = null;
    }}
    resetAudioQueue();
}}

window.addEventListener('beforeunload', cleanupVoice);

""".format(
    talking_video=TALKING_VIDEO,
    idle_video=IDLE_VIDEO,
    speak_audio_dir=SPEAK_AUDIO_DIR,
    wave_videos=config.WAVE_CONFIG["videos"],
    min_interval=config.WAVE_CONFIG["min_interval"],
    max_interval=config.WAVE_CONFIG["max_interval"],
    all_questions=ALL_QUESTIONS_JS,
    display_count=DISPLAY_COUNT,
    idle_pause_min=config.IDLE_PAUSE["min"],
    idle_pause_max=config.IDLE_PAUSE["max"],
    opacity_ms=config.VIDEO_TRANSITION["opacity_ms"],
    pcm_worklet_json=json.dumps(PCM_WORKLET_JS, ensure_ascii=False),
)


# ============================================
# 创建应用
# ============================================

def create_kiosk_app():
    """创建展示应用"""

    with gr.Blocks(
        title="数字人问答系统",
    ) as app:

        # 主内容区（全屏覆盖）
        with gr.Row(elem_classes="main-content"):

            # ==================== 左侧浮动问题面板（4个按钮）====================
            with gr.Column(elem_classes=["question-panel", "panel-left"]):
                gr.HTML(f'<div class="panel-title">{config.UI_CONFIG["left_title"]}</div>')
                for i in range(4):
                    btn = gr.Button(
                        "正在加载问题",
                        elem_classes="q-btn",
                        variant="secondary"
                    )
                    btn.click(
                        fn=None,
                        js=f"() => {{ onQuestionClick({i}); }}"
                    )

            # ==================== 中间视频区域（全屏背景）====================
            with gr.Column():

                # 双缓冲视频容器 + 挥手覆盖层 + 字幕条
                gr.HTML(value=f'''
                <div class="video-container">
                    <video id="videoBack" class="video-layer inactive" autoplay muted playsinline>
                        <source src="/gradio_api/file={IDLE_VIDEO}" type="video/mp4">
                    </video>
                    <video id="videoFront" class="video-layer active" autoplay muted playsinline>
                        <source src="/gradio_api/file={IDLE_VIDEO}" type="video/mp4">
                    </video>
                    <div class="top-identity">
                        <div>
                            <div class="identity-kicker">STATE GRID AI SERVICE TERMINAL</div>
                            <div class="identity-title">国家电网 AI 数字讲解员</div>
                        </div>
                        <div class="identity-status">
                            <span class="status-dot"></span>
                            <span>智慧电力展示终端</span>
                        </div>
                    </div>
                    <div id="waveOverlay" class="wave-overlay"></div>
                    <!-- 讲话配音：talking 模式按问题 id 动态加载（videos/xq0X.mp3），切回 idle 时停止 -->
                    <audio id="speakAudio" preload="auto"></audio>
                    <div id="loadingOverlay" class="loading-overlay hidden">
                        <div class="loading-spinner"></div>
                    </div>
                    <div id="answerCaption" class="answer-caption">
                        <div id="captionQuestion" class="caption-question">欢迎使用智能问答</div>
                        <div id="captionAnswer" class="caption-answer">点击左右两侧问题，开启智慧电力探索之旅</div>
                    </div>
                    <div class="stage-line"></div>
                    <!-- 暂停/继续回答按钮：仅 talking 模式可见，点击在暂停与继续间切换 -->
                    <button id="stopAnswerBtn" class="stop-btn" type="button" onclick="togglePauseAnswer()">
                        <span class="btn-icon icon-pause"></span>
                        <span class="btn-icon icon-play"></span>
                        <span class="btn-text">暂停回答</span>
                    </button>
                    <!-- 语音对话按钮：按住说话（PTT）按下录音 → 松开提交 → 滑出取消 → ASR → LLM → TTS -->
                    <button id="voiceChatBtn" class="voice-chat-btn" type="button"
                            onpointerdown="onVoicePressStart(event)"
                            onpointerup="onVoicePressEnd(event)"
                            onpointerleave="onVoicePressCancel(event)"
                            onpointercancel="onVoicePressCancel(event)">
                        <span class="voice-icon">
                            <span class="icon-mic"></span>
                            <span class="icon-wave">
                                <span></span><span></span><span></span><span></span>
                            </span>
                            <span class="icon-spinner"></span>
                        </span>
                        <span id="voiceBtnText" class="btn-text">按住说话</span>
                    </button>
                </div>
                ''', elem_classes="video-html-wrapper")

            # ==================== 右侧浮动问题面板（4个按钮）====================
            with gr.Column(elem_classes=["question-panel", "panel-right"]):
                gr.HTML(f'<div class="panel-title">{config.UI_CONFIG["right_title"]}</div>')
                for i in range(4):
                    btn = gr.Button(
                        "正在加载问题",
                        elem_classes="q-btn",
                        variant="secondary"
                    )
                    btn.click(
                        fn=None,
                        js=f"() => {{ onQuestionClick({i + 4}); }}"
                    )

    return app


def check_video_files():
    """检查视频资源文件是否存在"""
    missing = []

    if not os.path.exists(IDLE_VIDEO):
        missing.append(f"待机视频: {IDLE_VIDEO}")
    if not os.path.exists(TALKING_VIDEO):
        missing.append(f"说话视频: {TALKING_VIDEO}")

    # 检查挥手视频
    wave_videos = config.WAVE_CONFIG.get("videos", [])
    if config.WAVE_CONFIG.get("enabled", False):
        wave_found = False
        for wv in wave_videos:
            if os.path.exists(wv):
                wave_found = True
                break
        if not wave_found:
            missing.append("挥手视频: wave 目录下未找到任何 mp4 文件")

    if missing:
        print("\n" + "=" * 50)
        print("⚠️  视频资源检查 - 发现缺失文件:")
        for m in missing:
            print(f"   ❌ {m}")
        print("=" * 50)
        print("💡 提示: 请确保视频文件已放置到正确路径")
        print("   系统将继续启动，但部分功能可能不可用\n")
    else:
        print("✅ 视频资源检查通过")


def main(port=None):
    """主函数：通过 FastAPI 同时承载 Gradio 界面 + 语音对话 WebSocket"""
    server_port = port if port else config.SERVER_CONFIG["port"]

    print("\n" + "="*50)
    print("🚀 数字人问答系统")
    print(f"📹 待机视频: {IDLE_VIDEO}")
    print(f"📹 说话视频: {TALKING_VIDEO}")
    print(f"👋 挥手动画: {'启用' if config.WAVE_CONFIG['enabled'] else '禁用'}")
    print(f"📋 问题总数: {len(config.QUESTION_POOL)}（固定展示{DISPLAY_COUNT}个：左4常见问题 + 右4热点问答）")
    print(f"🎤 语音对话: 已启用（左侧'语音对话'按钮）")
    print(f"🌐 访问地址: http://localhost:{server_port}")
    print("="*50 + "\n")

    check_video_files()

    # 语音流水线配置检查（内网 API：ASR/TTS/LLM 凭证已内置）
    from voice_pipeline import config as voice_config
    print("🎙️  ASR 端点:", voice_config.ASR_CONFIG["base_url"])
    print("🔊  TTS 端点:", voice_config.TTS_CONFIG["base_url"])
    print("🤖  LLM 端点:", voice_config.LLM_CONFIG["base_url"])

    # 创建 Gradio Blocks
    gradio_app = create_kiosk_app()

    # 创建 FastAPI 主应用，同时承载 Gradio + 语音 WebSocket 路由
    main_app = FastAPI(title="数字人问答系统")

    # CORS
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册语音对话路由（POST /asr, WS /chat/stream）
    register_routes(main_app)

    # 健康检查端点
    @main_app.get("/health")
    def health():
        return {"status": "ok", "voice_api": "internal"}

    # 将 Gradio 挂载到 / 路径（css/js/theme 注入到页面；allowed_paths 允许提供视频/音频文件服务）
    gr.mount_gradio_app(
        main_app,
        gradio_app,
        path="/",
        allowed_paths=[VIDEO_DIR],
        css=KIOSK_CSS,
        js=VIDEO_JS,
        theme=gr.themes.Monochrome(),
        show_error=True,
        footer_links=["_"],
    )

    # 启动服务
    uvicorn.run(
        main_app,
        host=config.SERVER_CONFIG["host"],
        port=server_port,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=None, help="Port to run the server on")
    args = parser.parse_args()
    main(port=args.port)
