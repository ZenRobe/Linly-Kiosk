# 数字人问答展示系统

一个面向 2160×3840 竖屏的数字人问答展示系统，用户通过点击预设问题触发数字人视频播放。

## 功能特点

- 📺 **双缓冲视频切换** - 点击问题无缝切换视频
- 👋 **随机挥手动画** - 回答过程中随机触发挥手动作
- 🎨 **美观界面** - 渐变背景 + 毛玻璃效果
- ⚙️ **灵活配置** - 通过配置文件自定义问题和视频

## 项目结构

```
Linly-Kiosk/
├── app.py                   # 主应用
├── configs/
│   └── kiosk_config.py     # 配置文件
├── videos/                  # 视频资源
│   ├── idle.mp4           # 待机视频
│   ├── talking.mp4        # 回答视频
│   └── wave/              # 挥手视频
│       ├── wave_1.mp4
│       ├── wave_2.mp4
│       └── wave_3.mp4
├── docs/
│   └── 开发方案.md         # 开发文档
└── README.md              # 本文件
```

## 快速开始

### 1. 准备视频资源

在 `videos` 目录下放置以下视频：

| 文件 | 说明 |
|------|------|
| `videos/idle.mp4` | 待机状态视频（站着不动） |
| `videos/talking.mp4` | 回答状态视频（嘴动） |
| `videos/wave/wave_1.mp4` | 挥手片段1 |
| `videos/wave/wave_2.mp4` | 挥手片段2 |
| `videos/wave/wave_3.mp4` | 挥手片段3 |

### 2. 安装依赖

```bash
pip install gradio
```

### 3. 启动应用

```bash
python app.py
```

### 4. 访问系统

打开浏览器访问：`http://localhost:6006`

## 配置说明

### 修改问题

编辑 `configs/kiosk_config.py` 中的 `PRESET_QUESTIONS`：

```python
PRESET_QUESTIONS = {
    "left": [
        {"id": "q01", "question": "你的问题", "answer": "回答内容"},
    ],
    "right": [
        {"id": "q02", "question": "你的问题", "answer": "回答内容"},
    ]
}
```

### 修改挥手配置

编辑 `WAVE_CONFIG`：

```python
WAVE_CONFIG = {
    "enabled": True,                   # 是否启用挥手
    "min_interval": 8,                 # 最小间隔（秒）
    "max_interval": 15,               # 最大间隔（秒）
    "videos": [                       # 挥手视频列表
        "videos/wave/wave_1.mp4",
    ]
}
```

### 修改端口

编辑 `SERVER_CONFIG`：

```python
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 6006,    # 修改端口号
    "share": False,
}
```

## 视频要求

- **格式**: MP4
- **编码**: H.264
- **比例**: 竖屏 9:16 或相近比例
- **大小**: 建议 10MB 以内

## 屏幕适配

- 分辨率: 2160×3840
- 布局: 左侧20% | 中间60% | 右侧20%

## 技术栈

- Python 3.8+
- Gradio 4.0+
- HTML/CSS/JavaScript

## 许可证

MIT License
