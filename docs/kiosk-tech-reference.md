# Linly-Kiosk 技术参考

## Overview

数字人问答展示系统，面向 2160×3840 竖屏 Kiosk 终端，全屏视频背景 + 浮动问题面板。基于 Python Gradio 6.x，CSS/JS 内联在 app.py 中。24 题国家电网专题问题库，点击后随机刷新 6 题展示。

## Architecture

```
app.py                    # 主应用入口（单文件：CSS + JS + Python）
configs/kiosk_config.py   # 所有可配置项（问题库、颜色、服务器等）
videos/                   # 视频素材（不入库）
  idle.mp4               # 待机视频（循环播放）
  talking.mp4            # 回答视频（点击问题后播放）
  wave/                  # 挥手视频片段（暂未启用）
```

## Key Config Variables

| 变量 | 位置 | 说明 |
|------|------|------|
| `QUESTION_POOL` | `configs/kiosk_config.py:68` | 完整问题库，24 题，每题为 `{id, question, answer}` |
| `PRESET_QUESTIONS` | `configs/kiosk_config.py:31` | 初始显示用（兼容），分 left/right |
| `VIDEOS` | `configs/kiosk_config.py:9` | idle/talking 视频路径 |
| `WAVE_CONFIG` | `configs/kiosk_config.py:15` | 挥手动画开关（当前 disabled） |
| `UI_CONFIG` | `configs/kiosk_config.py:154` | 面板标题等 UI 文案 |
| `ANSWER_CONFIG` | `configs/kiosk_config.py:182` | 自动回归待机时间（30s） |
| `SERVER_CONFIG` | `configs/kiosk_config.py:172` | 端口/地址配置 |
| `DISPLAY_COUNT` | `app.py:24` | 每屏显示问题数（6） |

## CSS Structure (`KIOSK_CSS`)

| 选择器 | 行号 | 用途 |
|--------|------|------|
| `body` | 29 | 全局黑底、隐藏溢出 |
| `.video-container` | 78 | 全屏视频层 |
| `.video-layer.active/.inactive` | 93 | 双缓冲视频切换（opacity 0.4s） |
| `.question-panel` | 164 | 浮动毛玻璃面板（rgba(8,12,32,0.88)） |
| `.panel-left/.panel-right` | 179 | 左右定位 |
| `.panel-title` | 196 | 面板标题（居中、底部金线） |
| `.q-btn` | 208 | 问题按钮（深海蓝配色） |
| `.q-btn:hover` | 229 | 蓝色微光 |
| `.q-btn.active` | 237 | 选中态 |
| `.answer-caption` | 275 | 答案字幕条 |
| `.caption-answer .answer-seg` | 313 | 答案分段交错过场动画 |

## JavaScript Architecture (`VIDEO_JS`)

### 问题管理
- `ALL_QUESTIONS` — 完整问题库（Python 端 `json.dumps` 注入）
- `currentQuestions[]` — 当前显示的 6 题
- `previousQuestions[]` — 上一轮显示的题（用于去重）
- `pickRandomQuestions(n)` — Fisher-Yates 洗牌
- `refreshQuestionButtons()` — 淡出→换字→淡入（200ms）
- `onQuestionClick(idx)` — 点击处理（保留当前题、随机换 5 题）

### 视频控制
- `switchToTalking()` — 双缓冲切换到回答视频
- `switchToIdle()` — 切回待机 + 问题刷新 + 恢复欢迎语

### 字幕
- `showCaption(question, answer)` — 答案分段交错渐显（每句 0.12s delay）
- `resetCaption()` — 恢复欢迎语

## Gradio 6.x Migration Note

原始代码将 `<script>` 嵌入 `gr.HTML(value=...)`。Gradio 6.x 警告 `innerHTML` 不执行脚本。
修复：JS 移至 `app.launch(js=VIDEO_JS)`，移除 HTML 中的 `<script>` 标签。

## Files Changed

| File | Status | Lines |
|------|--------|-------|
| `.gitignore` | Modified | +1 (videos/wave/*.mp4) |
| `app.py` | Modified | +323/-93 |
| `configs/kiosk_config.py` | Modified | +75/-43 |
| `requirements.txt` | New | +1 |
| `videos/.gitkeep` | New | 0 |
| `videos/wave/.gitkeep` | New | 0 |
