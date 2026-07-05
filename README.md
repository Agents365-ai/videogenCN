# Videogen-Wan 🎬

[中文文档](README_CN.md)

A Claude Code / OpenClaw skill for generating video clips with Chinese video models via the Alibaba Cloud Bailian (DashScope) API — Wan (通义万相), PixVerse (爱诗), Kling (可灵), Vidu, and HappyHorse with one API key.

## Why This Skill?

| | Native Claude Code | Videogen-Wan |
|---|---|---|
| Text-to-video | ❌ | ✅ Wan, PixVerse, Kling, Vidu, HappyHorse |
| Image-to-video | ❌ | ✅ Animate any still image |
| First+last frame (kf2v) | ❌ | ✅ PixVerse / Kling / Vidu |
| Reference-to-video (r2v) | ❌ | ✅ Character-consistent clips |
| Chinese prompts | — | ✅ First-class |
| Async task handling | — | ✅ Submit → poll → download, resumable |
| Vertical (9:16) video | — | ✅ For Douyin / Xiaohongshu / Shorts |

## Features

- **Four modes, one script**: prompt → t2v; `--image` → i2v; `+ --last-frame` → kf2v; `--ref name=img` → r2v
- **Five model families**: Alibaba Wan plus third-party PixVerse (c1/v6/v5.6), Kling v3, Vidu (q3/q2), HappyHorse
- **Local images just work**: base64 for Wan/HappyHorse; auto-upload to DashScope temp storage for PixVerse/Kling/Vidu
- **Multi-shot narratives**: `wan2.7-t2v` renders up to 15s with per-shot descriptions
- **Audio control**: `--audio` (third-party) / `--no-audio` (Wan)
- **Resumable**: long tasks print a task id; `--task-id` resumes polling

## Install the Skill

**Claude Code (global):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git ~/.claude/skills/videogen-wan
```

**Claude Code (project):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git .claude/skills/videogen-wan
```

**OpenClaw:**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git ~/.openclaw/skills/videogen-wan
```

## Requirements

- Python 3.8+
- `pip install requests`
- A Bailian API key: https://bailian.console.aliyun.com/

```bash
export DASHSCOPE_API_KEY='your-api-key'
```

Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `DASHSCOPE_API_BASE` | `cn` (default) / `sg` / `us` or a full URL |
| `DASHSCOPE_VIDEO_MODEL` | default model override |

## Quick Start

**Natural language** (in Claude Code):

> 用万相生成一段 5 秒的视频:一只柴犬在樱花树下奔跑

**Command line:**

```bash
# Text-to-video
python scripts/generate_video.py "A shiba inu running under cherry blossoms" out.mp4

# Image-to-video (animate a still)
python scripts/generate_video.py "Camera slowly zooms in" out.mp4 --image photo.png

# Vertical short-video clip
python scripts/generate_video.py "Cyberpunk rainy street" city.mp4 --ratio 9:16
```

## Models

| Family | Models | Modes | Duration |
|--------|--------|-------|----------|
| Wan 通义万相 | `wan2.7-t2v-*` (t2v default), `wan2.6-i2v-flash` (i2v default), `wan2.5/2.2/wanx2.1` series | t2v, i2v | up to 15s |
| PixVerse 爱诗 | `pixverse/pixverse-{c1,v6,v5.6}-{t2v,it2v,kf2v,r2v}` | all four | 1–15s |
| Kling 可灵 | `kling/kling-v3-video-generation`, `kling/kling-v3-omni-video-generation` | t2v, i2v, kf2v (+r2v on omni) | 3–15s |
| Vidu | `vidu/viduq3-{pro,turbo}_{text2video,img2video,start-end2video}`, `viduq2*` | t2v, i2v, kf2v | q3: 1–16s |
| HappyHorse | `happyhorse-{1.1,1.0}-{t2v,i2v}` | t2v, i2v | 3–15s |

Run `python scripts/generate_video.py --list-models` for the current list. Third-party families are Beijing region (`cn`) only.

> **Cost**: video generation bills per second of output (roughly $0.04–0.14/s depending on model and resolution). Result URLs expire after 24h — the script downloads immediately.

## License

MIT

## Author

**Agents365-ai** — [GitHub](https://github.com/Agents365-ai)
