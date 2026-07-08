# Videogen-Wan 🎬

[中文文档](README_CN.md)

A Claude Code / OpenClaw skill for generating video clips with Chinese video models across three providers — Alibaba Bailian (Wan/PixVerse/Kling/Vidu/HappyHorse), Volcengine Ark (Jimeng/即梦), and MiniMax (海螺 AI).

## Why This Skill?

| | Native Claude Code | Videogen-Wan |
|---|---|---|
| Text-to-video | ❌ | ✅ 7 model families across 3 providers |
| Image-to-video | ❌ | ✅ Animate any still image |
| First+last frame (kf2v) | ❌ | ✅ PixVerse / Kling / Vidu |
| Reference-to-video (r2v) | ❌ | ✅ Character-consistent clips |
| Multi-provider | ❌ | ✅ Bailian + Jimeng + MiniMax |
| Chinese prompts | — | ✅ First-class |
| Async task handling | — | ✅ Submit → poll → download, resumable |
| Vertical (9:16) video | — | ✅ For Douyin / Xiaohongshu / Shorts |

## Features

- **Four modes, one script**: prompt → t2v; `--image` → i2v; `+ --last-frame` → kf2v; `--ref name=img` → r2v
- **Seven model families across three providers**: Bailian (Wan, PixVerse, Kling, Vidu, HappyHorse), Jimeng (Volcengine), MiniMax (Hailuo)
- **Provider auto-detection**: `--provider` flag or auto-detect from model name; backward compatible
- **Local images just work**: base64 for Wan/HappyHorse/Jimeng; auto-upload for PixVerse/Kling/Vidu/MiniMax
- **Multi-shot narratives**: `wan2.7-t2v` renders up to 15s with per-shot descriptions
- **Audio control**: `--audio` (third-party) / `--no-audio` (Wan)
- **Resumable**: long tasks print a task id; `--task-id` resumes polling

## Install the Skill

**365-Skills Marketplace (recommended):**

```bash
# In Claude Code — installs and auto-updates
/plugin install videogen-wan@365-skills
```

**Claude Code (manual):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git /tmp/videogenCN
ln -s /tmp/videogenCN/skills/videogen-wan ~/.claude/skills/videogen-wan
```

**Claude Code (project):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git /tmp/videogenCN
ln -s /tmp/videogenCN/skills/videogen-wan .claude/skills/videogen-wan
```

**OpenClaw:**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git /tmp/videogenCN
ln -s /tmp/videogenCN/skills/videogen-wan ~/.openclaw/skills/videogen-wan
```

## Requirements

- Python 3.8+
- `pip install requests`
- At least one provider API key (see below)

### Provider API Keys

| Provider | Env Vars | Get Key At |
|----------|----------|------------|
| **Bailian** (Wan/PixVerse/Kling/Vidu/HappyHorse) | `DASHSCOPE_API_KEY` | https://bailian.console.aliyun.com/ |
| **Jimeng** (即梦) | `ARK_API_KEY` | https://console.volcengine.com/ark/ |
| **MiniMax** (海螺 AI) | `MINIMAX_API_KEY` | https://platform.minimax.io |

```bash
# Bailian (required for default provider)
export DASHSCOPE_API_KEY='your-api-key'

# Jimeng (optional)
export ARK_API_KEY='your-api-key'

# MiniMax (optional)
export MINIMAX_API_KEY='your-api-key'
```

Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `DASHSCOPE_API_BASE` | Bailian region: `cn` (default) / `sg` / `us` or a full URL |
| `DASHSCOPE_VIDEO_MODEL` | Bailian default model override |

## Quick Start

**Natural language** (in Claude Code):

> 用万相生成一段 5 秒的视频:一只柴犬在樱花树下奔跑
> 用即梦生成一段 10 秒的竖屏视频:赛博朋克雨夜街头

**Command line:**

```bash
# Text-to-video (Bailian default)
python scripts/generate_video.py "A shiba inu running under cherry blossoms" out.mp4

# Image-to-video (animate a still)
python scripts/generate_video.py "Camera slowly zooms in" out.mp4 --image photo.png

# Vertical short-video clip
python scripts/generate_video.py "Cyberpunk rainy street" city.mp4 --ratio 9:16

# Jimeng (即梦)
python scripts/generate_video.py "城市日落延时摄影" sunset.mp4 --provider jimeng --duration 10

# MiniMax (海螺)
python scripts/generate_video.py "海浪拍打礁石" ocean.mp4 --provider minimax --duration 6
```

## Models

### Bailian (百炼) — 5 families

| Family | Models | Modes | Duration |
|--------|--------|-------|----------|
| Wan 通义万相 | `wan2.7-t2v-*` (t2v default), `wan2.6-i2v-flash` (i2v default), `wan2.5/2.2/wanx2.1` series | t2v, i2v | up to 15s |
| PixVerse 爱诗 | `pixverse/pixverse-{c1,v6,v5.6}-{t2v,it2v,kf2v,r2v}` | all four | 1–15s |
| Kling 可灵 | `kling/kling-v3-video-generation`, `kling/kling-v3-omni-video-generation` | t2v, i2v, kf2v (+r2v on omni) | 3–15s |
| Vidu | `vidu/viduq3-{pro,turbo}_{text2video,img2video,start-end2video}`, `viduq2*` | t2v, i2v, kf2v | q3: 1–16s |
| HappyHorse | `happyhorse-{1.1,1.0}-{t2v,i2v}` | t2v, i2v | 3–15s |

### Jimeng (即梦 / Volcengine Ark)

| Family | Models | Modes | Duration |
|--------|--------|-------|----------|
| Jimeng Seedance | `doubao-seedance-2-0-260128` (default), `doubao-seedance-2-0-fast-260128`, `doubao-seedance-1-5-pro-251215`, `doubao-seedance-1-0-pro` | t2v, i2v | up to 15s |

> ✅ Tested: t2v 5s, ~4 min, 5.6 MB MP4

### MiniMax (海螺 AI)

| Family | Models | Modes | Duration |
|--------|--------|-------|----------|
| MiniMax | `video-01` (t2v/i2v default) | t2v, i2v | 6s |

> ✅ Tested: t2v 6s, ~3 min, 2.9 MB MP4

Run `python scripts/generate_video.py --list-models` for the current list. Third-party Bailian families are Beijing region (`cn`) only.

> **Cost**: video generation bills per second of output (roughly $0.04–0.14/s depending on model and resolution). Result URLs expire after 24h — the script downloads immediately.

## License

MIT

## Author

**Agents365-ai** — [GitHub](https://github.com/Agents365-ai)
