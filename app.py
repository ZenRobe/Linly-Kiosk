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

# 视频资源路径（绝对路径，开发/打包模式通用）
IDLE_VIDEO = os.path.join(BASE_DIR, "videos", "idle.mp4").replace("\\", "/")
TALKING_VIDEO = os.path.join(BASE_DIR, "videos", "talking.mp4").replace("\\", "/")
XUNHUAN_VIDEO = os.path.join(BASE_DIR, "videos", "xunhuan.mp4").replace("\\", "/")
# 讲话配音目录：每题配音文件为 videos/{id}.mp3（如 xq03.mp3），视频 muted，声音由此音频提供。
# 前端点击问题时按问题 id 动态加载对应配音（音频为播放主时钟，决定回答总时长）。
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
    transition: opacity 0.08s ease-out;
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

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""

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

    // 按问题 id 加载对应配音（音频为播放主时钟，决定回答总时长）：videos/{{id}}.mp3
    var speakAudio = document.getElementById('speakAudio');
    if (speakAudio && q && q.id) {{
        speakAudio.pause();
        speakAudio.onended = null;
        speakAudio.src = '/gradio_api/file={speak_audio_dir}/' + q.id + '.mp3';
        speakAudio.load();
    }}

    showCaption(q.question, q.answer);
    switchToTalking();
    var btns = document.querySelectorAll('.q-btn');
    btns.forEach(function(b) {{ b.classList.remove('active'); }});
    if (btns[btnIndex]) btns[btnIndex].classList.add('active');
}}

/* 切换到回答模式 - 播 talking.mp4 一遍，音频未结束则循环 xunhuan.mp4，音频结束切 idle */
function switchToTalking() {{
    var backVideo = document.getElementById('videoBack');
    var frontVideo = document.getElementById('videoFront');
    var loading = document.getElementById('loadingOverlay');

    if (!frontVideo || !backVideo) return;
    currentMode = 'talking';
    updateStopButton();  // 显示"暂停回答"按钮
    isPaused = false;    // 新回答从头播放，重置暂停态
    setStopButtonState(false);
    stopIdleLoop();  // 清除 idle 摆臂停顿定时器，避免讲话中又触发重播

    // 音频为播放主时钟：播完即切回 idle
    var speakAudio = document.getElementById('speakAudio');
    if (speakAudio) {{
        speakAudio.onended = null;
        try {{ speakAudio.currentTime = 0; }} catch (e) {{}}
        speakAudio.onended = function() {{
            if (currentMode === 'talking') switchToIdle();
        }};
        // 在用户点击手势链路内触发播放，避免被浏览器自动播放策略拦截
        speakAudio.play().catch(function (e) {{}});
    }}

    if (loading) loading.classList.remove('hidden');

    // 后台加载回答视频 talking.mp4（不循环，播完切到 xunhuan.mp4 循环填充）
    backVideo.loop = false;
    backVideo.oncanplaythrough = null;
    backVideo.onended = null;  // 清除旧事件，避免重复触发
    backVideo.src = '/gradio_api/file={talking_video}';
    backVideo.load();

    backVideo.oncanplaythrough = function() {{
        // talking 播完后：若仍在 talking 模式（音频未结束），切到 xunhuan.mp4 循环填充至音频结束
        backVideo.onended = function() {{
            if (currentMode !== 'talking') return;
            backVideo.loop = true;          // 循环播放 xunhuan.mp4
            backVideo.onended = null;       // loop 期间不再触发 onended，由音频 onended 收尾
            backVideo.oncanplaythrough = function() {{
                backVideo.oncanplaythrough = null;
                backVideo.play().catch(function(e){{}});
            }};
            backVideo.src = '/gradio_api/file={xunhuan_video}';
            backVideo.load();
        }};

        // 先开始播放（此时 backVideo 还是透明状态）
        backVideo.play().catch(function(e){{}});

        // 等待首帧渲染后再切换图层（避免闪现空白帧）
        var swap = function() {{
            frontVideo.classList.remove('active');
            frontVideo.classList.add('inactive');
            backVideo.classList.remove('inactive');
            backVideo.classList.add('active');

            // 交换层级
            setTimeout(function() {{
                frontVideo.src = '';
                var tempId = frontVideo.id;
                frontVideo.id = backVideo.id;
                backVideo.id = tempId;
            }}, 500);

            // 启动随机挥手动画
            startWaveAnimation();
        }};

        // requestVideoFrameCallback: 精确等到首帧渲染（Chrome/Edge）
        // 降级方案: setTimeout ~40ms ≈ 2 帧
        if (backVideo.requestVideoFrameCallback) {{
            backVideo.requestVideoFrameCallback(swap);
            // 100ms 保险：万一回调没触发
            setTimeout(function() {{
                if (backVideo.classList.contains('inactive')) swap();
            }}, 100);
        }} else {{
            setTimeout(swap, 40);
        }}

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
    backVideo.loop = false;  // 不无缝循环，由 startIdleLoop 接管：播完停顿再重播
    backVideo.src = '/gradio_api/file={idle_video}';
    backVideo.load();

    backVideo.oncanplaythrough = function() {{
        // 先开始播放（此时 backVideo 还是透明状态）
        backVideo.play().catch(function(e){{}});

        // 接管 idle 循环：播完随机停顿再重播
        startIdleLoop(backVideo);

        // 等待首帧渲染后再切换图层
        var swap = function() {{
            frontVideo.classList.remove('active');
            frontVideo.classList.add('inactive');
            backVideo.classList.remove('inactive');
            backVideo.classList.add('active');

            setTimeout(function() {{
                frontVideo.src = '';
                var tempId = frontVideo.id;
                frontVideo.id = backVideo.id;
                backVideo.id = tempId;
            }}, 500);
        }};

        if (backVideo.requestVideoFrameCallback) {{
            backVideo.requestVideoFrameCallback(swap);
            setTimeout(function() {{
                if (backVideo.classList.contains('inactive')) swap();
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

/* 暂停/继续切换：同步控制当前 active 视频图层与配音，不切换模式，按钮始终可见 */
var isPaused = false;
function togglePauseAnswer() {{
    if (currentMode !== 'talking') return;
    var activeVideo = document.querySelector('.video-layer.active');
    var speakAudio = document.getElementById('speakAudio');
    if (!isPaused) {{
        // 播放中 → 暂停（视频 + 配音同步停）
        if (activeVideo) activeVideo.pause();
        if (speakAudio) speakAudio.pause();
        isPaused = true;
        setStopButtonState(true);
    }} else {{
        // 暂停中 → 继续
        if (activeVideo) activeVideo.play().catch(function (e) {{}});
        if (speakAudio) speakAudio.play().catch(function (e) {{}});
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

        // 预加载 talking.mp4 / xunhuan.mp4 到浏览器缓存，后续切换瞬间就绪（避免 talking→xunhuan 黑帧）
        ['{talking_video}', '{xunhuan_video}'].forEach(function(src) {{
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
""".format(
    talking_video=TALKING_VIDEO,
    xunhuan_video=XUNHUAN_VIDEO,
    idle_video=IDLE_VIDEO,
    speak_audio_dir=SPEAK_AUDIO_DIR,
    wave_videos=config.WAVE_CONFIG["videos"],
    min_interval=config.WAVE_CONFIG["min_interval"],
    max_interval=config.WAVE_CONFIG["max_interval"],
    all_questions=ALL_QUESTIONS_JS,
    display_count=DISPLAY_COUNT,
    idle_pause_min=config.IDLE_PAUSE["min"],
    idle_pause_max=config.IDLE_PAUSE["max"]
)


# ============================================
# 创建应用
# ============================================

def create_kiosk_app():
    """创建展示应用"""

    with gr.Blocks(
        title="数字人问答系统"
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
        missing.append(f"回答视频: {TALKING_VIDEO}")
    if not os.path.exists(XUNHUAN_VIDEO):
        missing.append(f"循环视频: {XUNHUAN_VIDEO}")
    # 检查 8 段配音（文件名与问题 id 一致：xq01–xq08）
    missing_speak = [f"xq{i:02d}" for i in range(1, 9)
                     if not os.path.exists(os.path.join(SPEAK_AUDIO_DIR, f"xq{i:02d}.mp3"))]
    if missing_speak:
        missing.append(f"讲话配音缺失: {', '.join(missing_speak)}（应在 {SPEAK_AUDIO_DIR} 下）")

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
    """主函数"""
    # 使用命令行指定的端口或配置文件中的端口
    server_port = port if port else config.SERVER_CONFIG["port"]

    print("\n" + "="*50)
    print("🚀 数字人问答展示系统")
    print(f"📹 待机视频: {IDLE_VIDEO}")
    print(f"📹 回答视频: {TALKING_VIDEO}")
    print(f"📹 循环视频: {XUNHUAN_VIDEO}")
    print(f"🔊 讲话配音目录: {SPEAK_AUDIO_DIR}（xq01–xq08.mp3，按问题 id 加载）")
    print(f"👋 挥手动画: {'启用' if config.WAVE_CONFIG['enabled'] else '禁用'}")
    print(f"📋 问题总数: {len(config.QUESTION_POOL)}（固定展示{DISPLAY_COUNT}个：左4常见问题 + 右4热点问答）")
    print(f"🌐 访问地址: http://localhost:{server_port}")
    print("="*50 + "\n")

    check_video_files()

    app = create_kiosk_app()
    app.launch(
        server_name=config.SERVER_CONFIG["host"],
        server_port=server_port,
        share=config.SERVER_CONFIG["share"],
        allowed_paths=[VIDEO_DIR],
        css=KIOSK_CSS,
        js=VIDEO_JS,  # Gradio 6.x: js 参数移到 launch()
        theme=gr.themes.Monochrome(),
        show_error=True,
        footer_links=["_"]
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=None, help="Port to run the server on")
    args = parser.parse_args()
    main(port=args.port)
