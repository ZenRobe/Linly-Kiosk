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

import gradio as gr
from configs import kiosk_config as config

# 视频资源路径
IDLE_VIDEO = config.VIDEOS["idle"]
TALKING_VIDEO = config.VIDEOS["talking"]

# 问题库（JSON 格式供前端 JS 使用）
ALL_QUESTIONS_JS = json.dumps(config.QUESTION_POOL, ensure_ascii=False)
DISPLAY_COUNT = 6  # 每次显示6个问题（左3右3）

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
    transition: opacity 0.42s ease-in-out;
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
var idleTimer = null;

/* ============ 问题管理 ============ */
var ALL_QUESTIONS = {all_questions};
var currentQuestions = [];
var previousQuestions = [];

/* 随机选取 n 个不重复问题（尽量与上一轮不重复）*/
function pickRandomQuestions(n) {{
    var pool = ALL_QUESTIONS.slice();
    var result = [];
    // 优先排除上一轮的问题
    var fresh = pool.filter(function(q) {{ return previousQuestions.indexOf(q.id) === -1; }});
    if (fresh.length < n) fresh = pool;
    // Fisher-Yates 部分洗牌
    for (var i = 0; i < n && i < fresh.length; i++) {{
        var j = i + Math.floor(Math.random() * (fresh.length - i));
        var tmp = fresh[i]; fresh[i] = fresh[j]; fresh[j] = tmp;
        result.push(fresh[i]);
    }}
    return result;
}}

/* 刷新按钮文字（左3 + 右3，带淡入淡出）*/
function refreshQuestionButtons() {{
    currentQuestions = pickRandomQuestions({display_count});
    previousQuestions = currentQuestions.map(function(q) {{ return q.id; }});
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

/* 点击问题按钮 */
function onQuestionClick(btnIndex) {{
    if (btnIndex >= currentQuestions.length) return;
    var q = currentQuestions[btnIndex];
    showCaption(q.question, q.answer);
    switchToTalking();
    // 记录点击的问题 id，刷新时保留它
    var clickedId = q.id;
    var btns = document.querySelectorAll('.q-btn');
    btns.forEach(function(b) {{ b.classList.remove('active'); }});
    if (btns[btnIndex]) btns[btnIndex].classList.add('active');
    // 淡出 + 刷新
    btns.forEach(function(b) {{ b.style.opacity = '0'; }});
    setTimeout(function() {{
        // 生成新6题，确保包含点击的那个
        var pool = ALL_QUESTIONS.slice();
        var rest = pool.filter(function(x) {{ return x.id !== clickedId; }});
        // Fisher-Yates shuffle rest
        for (var i = rest.length - 1; i > 0; i--) {{
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = rest[i]; rest[i] = rest[j]; rest[j] = tmp;
        }}
        currentQuestions = [q].concat(rest.slice(0, 5));
        previousQuestions = currentQuestions.map(function(x) {{ return x.id; }});
        // 保持点击的问题在同一个按钮位置
        for (var i = 0; i < btns.length && i < currentQuestions.length; i++) {{
            btns[i].textContent = currentQuestions[i].question;
        }}
        setTimeout(function() {{
            btns.forEach(function(b) {{ b.style.opacity = '1'; }});
        }}, 50);
    }}, 200);
}}

/* 切换到回答模式 - 播放 talking.mp4 */
function switchToTalking() {{
    var backVideo = document.getElementById('videoBack');
    var frontVideo = document.getElementById('videoFront');
    var loading = document.getElementById('loadingOverlay');

    if (!frontVideo || !backVideo) return;
    currentMode = 'talking';

    // 清除旧的自动回归定时器（重置）
    if (idleTimer) {{
        clearTimeout(idleTimer);
        idleTimer = null;
    }}

    // 启动自动回归待机定时器
    var autoReturnIdle = {auto_return_idle};
    var answerDuration = {answer_duration};
    if (autoReturnIdle) {{
        idleTimer = setTimeout(function() {{
            switchToIdle();
        }}, answerDuration * 1000);
    }}

    if (loading) loading.classList.remove('hidden');

    // 后台加载回答视频
    backVideo.src = '/gradio_api/file={talking_video}';
    backVideo.load();

    backVideo.oncanplay = function() {{
        // 淡入新视频，淡出旧视频
        frontVideo.classList.remove('active');
        frontVideo.classList.add('inactive');
        backVideo.classList.remove('inactive');
        backVideo.classList.add('active');
        backVideo.play().catch(function(e){{}});

        setTimeout(function(){{ if (loading) loading.classList.add('hidden'); }}, 300);

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
}}

/* 切换到待机模式 - 播放 idle.mp4 */
function switchToIdle() {{
    var backVideo = document.getElementById('videoBack');
    var frontVideo = document.getElementById('videoFront');
    currentMode = 'idle';
    stopWaveAnimation();

    // 清除自动回归定时器
    if (idleTimer) {{
        clearTimeout(idleTimer);
        idleTimer = null;
    }}

    // 移除按钮高亮 + 刷新问题列表
    document.querySelectorAll('.q-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    resetCaption();
    refreshQuestionButtons();

    backVideo.src = '/gradio_api/file={idle_video}';
    backVideo.load();

    backVideo.oncanplay = function() {{
        frontVideo.classList.remove('active');
        frontVideo.classList.add('inactive');
        backVideo.classList.remove('inactive');
        backVideo.classList.add('active');
        backVideo.play().catch(function(e){{}});

        setTimeout(function() {{
            frontVideo.src = '';
            var tempId = frontVideo.id;
            frontVideo.id = backVideo.id;
            backVideo.id = tempId;
        }}, 500);
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
    }} else {{
        setTimeout(initWhenReady, 150);
    }}
}})();
""".format(
    talking_video=TALKING_VIDEO,
    idle_video=IDLE_VIDEO,
    wave_videos=config.WAVE_CONFIG["videos"],
    min_interval=config.WAVE_CONFIG["min_interval"],
    max_interval=config.WAVE_CONFIG["max_interval"],
    auto_return_idle="true" if config.ANSWER_CONFIG["auto_return_idle"] else "false",
    answer_duration=config.ANSWER_CONFIG["answer_duration"],
    all_questions=ALL_QUESTIONS_JS,
    display_count=DISPLAY_COUNT
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

            # ==================== 左侧浮动问题面板（3个按钮）====================
            with gr.Column(elem_classes=["question-panel", "panel-left"]):
                gr.HTML(f'<div class="panel-title">{config.UI_CONFIG["left_title"]}</div>')
                for i in range(3):
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
                    <video id="videoBack" class="video-layer inactive" autoplay loop muted playsinline>
                        <source src="/gradio_api/file={IDLE_VIDEO}" type="video/mp4">
                    </video>
                    <video id="videoFront" class="video-layer active" autoplay loop muted playsinline>
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
                    <div id="loadingOverlay" class="loading-overlay hidden">
                        <div class="loading-spinner"></div>
                    </div>
                    <div id="answerCaption" class="answer-caption">
                        <div id="captionQuestion" class="caption-question">欢迎使用智能问答</div>
                        <div id="captionAnswer" class="caption-answer">点击左右两侧问题，开启智慧电力探索之旅</div>
                    </div>
                    <div class="stage-line"></div>
                </div>
                ''', elem_classes="video-html-wrapper")

            # ==================== 右侧浮动问题面板（3个按钮）====================
            with gr.Column(elem_classes=["question-panel", "panel-right"]):
                gr.HTML(f'<div class="panel-title">{config.UI_CONFIG["right_title"]}</div>')
                for i in range(3):
                    btn = gr.Button(
                        "正在加载问题",
                        elem_classes="q-btn",
                        variant="secondary"
                    )
                    btn.click(
                        fn=None,
                        js=f"() => {{ onQuestionClick({i + 3}); }}"
                    )

    return app


def check_video_files():
    """检查视频资源文件是否存在"""
    missing = []

    if not os.path.exists(IDLE_VIDEO):
        missing.append(f"待机视频: {IDLE_VIDEO}")
    if not os.path.exists(TALKING_VIDEO):
        missing.append(f"回答视频: {TALKING_VIDEO}")

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
    print(f"👋 挥手动画: {'启用' if config.WAVE_CONFIG['enabled'] else '禁用'}")
    print(f"📋 问题总数: {len(config.QUESTION_POOL)}（每次随机展示{DISPLAY_COUNT}个）")
    print(f"🌐 访问地址: http://localhost:{server_port}")
    print("="*50 + "\n")

    check_video_files()

    app = create_kiosk_app()
    app.launch(
        server_name=config.SERVER_CONFIG["host"],
        server_port=server_port,
        share=config.SERVER_CONFIG["share"],
        allowed_paths=[os.path.abspath("videos/")],
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
