"""
数字人问答展示系统 - 主应用
功能：点击问题播放数字人视频，包含随机挥手动画
"""
import os
import sys

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import gradio as gr
from configs import kiosk_config as config

# 视频资源路径
IDLE_VIDEO = config.VIDEOS["idle"]
TALKING_VIDEO = config.VIDEOS["talking"]

# ============================================
# CSS 样式
# ============================================

KIOSK_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    background: #000;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

/* 隐藏Gradio内置工具栏(下载/投屏/API等) */
footer,
[class*="footer"]:not(.my-footer),
[id*="footer"],
[data-testid="footer"] {
    display: none !important;
}

/* ============ 全屏视频层 ============ */
.main-content {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 1;
    pointer-events: none;
}

/* 只有浮动面板和底部可交互 */
.question-panel,
.question-panel *,
.footer {
    pointer-events: auto !important;
}

.video-html-wrapper {
    position: fixed !important;
    top: 0;
    left: 0;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 0;
    pointer-events: none;
}

.video-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000;
    z-index: 0;
}

/* 双缓冲视频层 */
.video-layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    transition: opacity 0.4s ease-in-out;
}

.video-layer.active {
    opacity: 1;
    z-index: 10;
}

.video-layer.inactive {
    opacity: 0;
    z-index: 5;
}

/* 挥手覆盖层 */
.wave-overlay {
    position: absolute;
    bottom: 8%;
    right: 12%;
    width: 12vw;
    height: 12vw;
    z-index: 20;
    display: none;
    pointer-events: none;
}

.wave-overlay.active {
    display: block;
    animation: waveAnim 1.5s ease-in-out;
}

@keyframes waveAnim {
    0% { transform: scale(0.8); opacity: 0; }
    50% { transform: scale(1.1); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}

/* 加载动画 */
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.loading-spinner {
    width: 60px;
    height: 60px;
    border: 5px solid rgba(255,255,255,0.3);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.hidden {
    display: none !important;
}

/* ============ 浮动问题面板 ============ */
.question-panel {
    position: fixed !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    z-index: 10 !important;
    width: 18vw !important;
    max-width: 380px !important;
    min-width: 240px !important;
    max-height: 80vh !important;
    overflow-y: auto !important;
    background: rgba(20, 20, 40, 0.75) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    pointer-events: auto !important;
}

/* 左侧面板固定在左 */
.panel-left {
    left: 30px !important;
}

/* 右侧面板固定在右 */
.panel-right {
    right: 30px !important;
}

/* 问题按钮 */
.q-btn {
    width: 100% !important;
    padding: 14px 16px !important;
    margin: 8px 0 !important;
    font-size: 1.05rem !important;
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #eee !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
    text-align: left !important;
    min-height: 48px !important;
    cursor: pointer !important;
    white-space: normal !important;
    line-height: 1.4 !important;
}

.q-btn:hover {
    background: rgba(102,126,234,0.6) !important;
    color: white !important;
    border-color: rgba(102,126,234,0.8) !important;
    box-shadow: 0 4px 20px rgba(102,126,234,0.4);
    transform: translateX(6px);
}

.q-btn.active {
    background: rgba(102,126,234,0.8) !important;
    color: white !important;
    border-color: #667eea !important;
    box-shadow: 0 4px 25px rgba(102,126,234,0.5) !important;
    transform: translateX(6px);
}

/* ============ 底部信息 ============ */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    z-index: 10;
    padding: 10px 0;
    background: rgba(0,0,0,0.5);
    color: rgba(255,255,255,0.5);
    text-align: center;
    font-size: 0.85rem;
    pointer-events: none;
}

/* 滚动条美化 */
.question-panel::-webkit-scrollbar {
    width: 4px;
}
.question-panel::-webkit-scrollbar-track {
    background: transparent;
}
.question-panel::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.2);
    border-radius: 2px;
}
"""

# ============================================
# JavaScript - 视频切换 + 挥手动画
# ============================================

VIDEO_JS = """
var waveInterval = null;
var currentMode = 'idle';
var idleTimer = null;

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

    // 移除按钮高亮
    document.querySelectorAll('.q-btn').forEach(function(b) {{ b.classList.remove('active'); }});

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
""".format(
    talking_video=TALKING_VIDEO,
    idle_video=IDLE_VIDEO,
    wave_videos=config.WAVE_CONFIG["videos"],
    min_interval=config.WAVE_CONFIG["min_interval"],
    max_interval=config.WAVE_CONFIG["max_interval"],
    auto_return_idle="true" if config.ANSWER_CONFIG["auto_return_idle"] else "false",
    answer_duration=config.ANSWER_CONFIG["answer_duration"]
)


# ============================================
# 创建应用
# ============================================

def create_kiosk_app():
    """创建展示应用"""

    with gr.Blocks(
        title="数字人问答系统"
    ) as app:

        # 状态变量
        current_question = gr.State(value=None)
        current_answer = gr.State(value=None)

        # 顶部标题 - 已移除

        # 主内容区（全屏覆盖）
        with gr.Row(elem_classes="main-content"):

            # ==================== 左侧浮动问题面板 ====================
            with gr.Column(elem_classes=["question-panel", "panel-left"]):
                left_buttons = []
                for q in config.PRESET_QUESTIONS["left"]:
                    btn = gr.Button(
                        q["question"],
                        elem_classes="q-btn",
                        variant="secondary"
                    )
                    left_buttons.append((btn, q))

            # ==================== 中间视频区域（全屏背景）====================
            with gr.Column():

                # 双缓冲视频容器 + 挥手覆盖层
                gr.HTML(value=f'''
                <div class="video-container">
                    <video id="videoBack" class="video-layer inactive" autoplay loop muted playsinline>
                        <source src="/gradio_api/file={IDLE_VIDEO}" type="video/mp4">
                    </video>
                    <video id="videoFront" class="video-layer active" autoplay loop muted playsinline>
                        <source src="/gradio_api/file={IDLE_VIDEO}" type="video/mp4">
                    </video>
                    <div id="waveOverlay" class="wave-overlay"></div>
                    <div id="loadingOverlay" class="loading-overlay hidden">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
                <script>{VIDEO_JS}</script>
                ''', elem_classes="video-html-wrapper")

            # ==================== 右侧浮动问题面板 ====================
            with gr.Column(elem_classes=["question-panel", "panel-right"]):
                right_buttons = []
                for q in config.PRESET_QUESTIONS["right"]:
                    btn = gr.Button(
                        q["question"],
                        elem_classes="q-btn",
                        variant="secondary"
                    )
                    right_buttons.append((btn, q))

        # ===== 统一注册事件（所有组件已创建完毕）=====
        all_buttons = left_buttons + right_buttons
        for btn, q in all_buttons:
            btn.click(
                fn=lambda q=q: (
                    q["question"],
                    q.get("answer", ""),
                ),
                outputs=[current_question, current_answer]
            ).then(
                fn=None,
                js="""() => {
    document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
    var btns = document.querySelectorAll('.q-btn');
    if (btns[""" + str(all_buttons.index((btn, q))) + """]) {
        btns[""" + str(all_buttons.index((btn, q))) + """].classList.add('active');
    }
    switchToTalking();
}"""
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
    print(f"📋 问题数量: {len(config.PRESET_QUESTIONS['left']) + len(config.PRESET_QUESTIONS['right'])}")
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
        theme=gr.themes.Monochrome(),
        show_error=True,
        footer_links=["_"]  # 传递非falsy值，绕过Gradio空列表bug，且不渲染任何链接
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=None, help="Port to run the server on")
    args = parser.parse_args()
    main(port=args.port)
