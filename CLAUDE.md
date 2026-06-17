# Linly-Kiosk 项目指南

## Vibe Coding 工作流

当用户提到**新功能开发、需求讨论、编码任务**时，主动提醒用户：

> "检测到开发需求，建议先输入 `/vibe-coding` 加载 7 阶段 Vibe Coding 工作流（初始化→需求→计划→编码→Review→文档→提交）。"

当用户输入 `/vibe-coding` 后，严格按照 `.claude/commands/vibe-coding.md` 中定义的流程执行。

## 项目简介

数字人问答展示系统，运行在 2160×3840 竖屏大屏上，基于 Python + Gradio 构建。

## 技术栈

- **语言**: Python 3.8+
- **框架**: Gradio
- **依赖管理**: 直接 pip install，无 requirements.txt / pyproject.toml
- **前端**: HTML/CSS/JS 内联在 Python 字符串中，无前端构建工具

## 架构约束

- 主应用入口：`app.py`（单文件架构，CSS/JS 以内联字符串嵌入）
- 配置文件：`configs/kiosk_config.py`（所有可配置项集中管理）
- 视频素材：`videos/` 目录
- 文档：`docs/` 目录
- 工作流状态：`.vibe/` 目录（不入版本库）

## 代码风格

- Python 遵循 PEP 8
- 缩进使用 4 空格
- 函数/变量命名使用 snake_case
- 常量使用 UPPER_CASE
- HTML/CSS/JS 字符串使用 Python 三引号包裹

## 质量门禁

目前无 lint/format/test 配置。编译检查命令：

```bash
python -c "import app"
python -c "from configs import kiosk_config; print('Config OK')"
```

## 运行方式

```bash
pip install gradio
python app.py
```

访问 `http://localhost:6006`
