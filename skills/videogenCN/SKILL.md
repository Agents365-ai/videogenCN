---
name: videogenCN
description: Use when generating video clips with Chinese video models — text-to-video (文生视频), image-to-video (图生视频), first/last-frame and reference-to-video across 4 platforms: Bailian (Wan/PixVerse/Kling/Vidu/HappyHorse), Jimeng (doubao-seedance), MiniMax (Hailuo), Hunyuan (hy-video)
author: Agents365-ai
created: 2026-07-05
updated: 2026-07-09
homepage: https://github.com/Agents365-ai/videogenCN
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["DASHSCOPE_API_KEY"]},"primaryEnv":"DASHSCOPE_API_KEY","emoji":"🎬"}}
---

# videogenCN - Chinese Video Generation Skill

## Overview

Generate short video clips using Chinese video models across three providers — Alibaba Cloud Bailian (DashScope), Volcengine Ark (Jimeng/即梦), and MiniMax (海螺 AI).

Four modes, auto-selected from the inputs you provide:

| Mode | Inputs | Default model |
|------|--------|---------------|
| t2v 文生视频 | prompt only | `wan2.7-t2v-2026-04-25` (Bailian) |
| i2v 图生视频 | prompt + `--image` | `wan2.6-i2v-flash` (Bailian) |
| kf2v 首尾帧 | prompt + `--image` + `--last-frame` | `pixverse/pixverse-c1-kf2v` (Bailian) |
| r2v 参考生视频 | prompt + `--ref` (1-7 images) | `pixverse/pixverse-c1-r2v` (Bailian) |

Video generation is **asynchronous**: the script submits a task, polls every 10s (long jobs can take 10-15 minutes), then downloads the MP4. Result URLs expire after 24h, so the script always downloads immediately.

Local images: Wan and HappyHorse accept base64 data URIs directly; PixVerse/Kling/Vidu only accept public URLs, so the script auto-uploads local files to DashScope temporary storage (48h `oss://` URL) before submitting. Jimeng converts local files to base64; MiniMax uploads via its file API.

## When to Use This Skill

- User asks to 生成视频 / 文生视频 / 图生视频 / 首尾帧 / 参考生视频, or to make a video clip from a prompt or image
- User names a Chinese video model: 万相/Wan, 爱诗/PixVerse, 可灵/Kling, Vidu, HappyHorse, 即梦/Jimeng, 海螺/MiniMax
- User needs B-roll, animated stills, character-consistent clips, or transitions between two frames

## Workflow

### Step 0: Prompt Refinement (交互式提示词打磨)

**CRITICAL — always run this step for t2v/i2v generation.** User prompts are often too short, vague, or missing key visual details that video models need. Claude acts as a prompt engineer to polish the prompt before generation.

#### 0.1 Analyze the user's raw input

Extract what's there and what's missing:

| Dimension | Check |
|-----------|-------|
| **Subject** | Who/what is the main focus? Describe appearance, action, expression |
| **Scene** | Where does it take place? Background, environment, atmosphere |
| **Lighting** | Time of day? Light quality? (golden hour, neon, soft diffused, backlit) |
| **Camera** | Shot type? (close-up, wide, aerial, tracking). Movement? (push-in, pan, orbit) |
| **Mood/Style** | Emotional tone? Visual style? (cinematic, anime, documentary, surreal) |
| **Motion** | What moves? How? Speed, direction, dynamics |
| **Temporal** | Any sequence? Beginning→middle→end? |

#### 0.2 Generate three refined variants

Present **3 variants** in a table, each with a different creative direction:

```
| # | 风格方向 | 优化后提示词 | 建议参数 |
|---|---------|-------------|---------|
| 1 | [风格名]  | [完整中文提示词] | 5s / 16:9 / 1080P |
| 2 | [风格名]  | [完整中文提示词] | 8s / 16:9 / 1080P |
| 3 | [风格名]  | [完整中文提示词] | 5s / 9:16 / 1080P |
```

**Variant design principles:**
- **Variant 1**: 忠于原意 — preserve the user's core idea, add rich visual detail, cinematic quality
- **Variant 2**: 创造性发散 — a different artistic interpretation of the same core idea
- **Variant 3**: 实用主义 — optimized for a specific platform format (vertical short-video, loopable clip, etc.)

**Prompt writing rules for video models:**
- Write in Chinese (all supported models optimize for Chinese)
- Front-load the subject and core action (first 20 chars matter most)
- Use concrete visual nouns ("金色麦田") not abstract concepts ("丰收的感觉")
- Describe motion explicitly ("缓缓推近", "随风飘动", "从远到近奔跑")
- Add camera and lighting cues at the end ("电影感镜头", "逆光剪影", "浅景深")
- Keep within 150 characters — video prompts are not novels
- For Wan 2.7 multi-shot: use `第N个镜头[N-Ns]: 描述` format

#### 0.3 User feedback loop

After presenting the three variants, ask the user to choose or give feedback. Accept these modifier keywords:

| User says | Action |
|-----------|--------|
| "用第N个" / "N" | Use variant N as-is |
| "更诗意" / "更浪漫" | Regenerate all three with more poetic/lyrical tone |
| "更简洁" | Strip to essentials, shorter prompts |
| "加动态元素" | Add more motion, action, kinetic energy |
| "改为夜景" / "下雪" / etc | Apply specific scene change to all variants |
| "混合1和3" | Combine subject of 1 with style of 3 |
| "直接用" / "不改了" | Skip refinement, use raw prompt |
| Custom feedback | Apply feedback and regenerate |

**Iterate until the user explicitly approves** a prompt (says "好", "可以", "用这个", "生成吧", etc.), then proceed to Step 1.

#### 0.4 Skip conditions

Skip refinement when:
- User explicitly says "直接生成" / "不用优化" / "skip"
- The prompt is already detailed (>80 chars with visual details already present)
- Mode is kf2v/r2v (reference images are the primary input)

### Step 1: Decide mode and provider

From the approved prompt and any `--image`/`--last-frame`/`--ref` inputs, determine:
- **Mode**: t2v / i2v / kf2v / r2v (same auto-detection as before)
- **Provider**: use `--provider` flag or auto-detect from model name
- **Model**: use `--model` flag, or provider/model defaults
- **Parameters**: duration, resolution, ratio from the variant's suggestion or user override

### Step 2: Confirm and generate

Show the final command and confirm with the user (especially for long/expensive generations). Run the script; it blocks until the task finishes and saves the MP4.

### Step 3: Deliver

Report the output path, file size, and generation time. If no output path was given, save to the current working directory.

**Cost note**: video APIs bill per second of output. For long or many clips, confirm with the user before submitting.

## Providers

### Alibaba Bailian 百炼

One API key (`DASHSCOPE_API_KEY`) covers all five model families. Third-party models (PixVerse/Kling/Vidu/HappyHorse) are **Beijing region (`cn`) only**.

### Volcengine Ark (Jimeng 即梦)

Simple Bearer token auth via `ARK_API_KEY`. Uses the Ark Content Generation API (`https://ark.cn-beijing.volces.com/api/v3`). Supports t2v and i2v with native audio, lip-sync, and camera motion control.

### MiniMax 海螺 AI

Simple Bearer token auth (`MINIMAX_API_KEY`). Three-step async flow (submit → query → retrieve download URL). Supports t2v and i2v.

## Models

### Wan 通义万相 (Alibaba Bailian)

| Model | Mode | Resolution | Duration | Notes |
|-------|------|-----------|----------|-------|
| `wan2.7-t2v-2026-04-25` | t2v | 720P/1080P | ≤15s | t2v default. Multi-shot: `第N个镜头[N-Ns]: ...` |
| `wan2.5-t2v-preview` | t2v | 480P-1080P | 5/10s | Generates audio, `--no-audio` supported |
| `wan2.2-t2v-plus` | t2v | 480P/1080P | 5s | Stable quality |
| `wanx2.1-t2v-turbo` / `-plus` | t2v | 480P-720P | 3-5s | Fast/cheap |
| `wan2.6-i2v-flash` | i2v | 720P/1080P | 2-15s | i2v default, `--no-audio` supported |
| `wan2.6-i2v` | i2v | 720P/1080P | 2-15s | Best i2v quality |
| `wan2.5-i2v-preview` | i2v | 480P-1080P | 5/10s | Audio |
| `wan2.2-i2v-plus` / `-flash` | i2v | 480P-1080P | 5s | Silent |
| `wanx2.1-i2v-turbo` / `-plus` | i2v | 480P-720P | 3-5s | Effect templates |

### PixVerse 爱诗 (Bailian third-party)

`pixverse/pixverse-{c1,v6,v5.6}-{t2v,it2v,kf2v,r2v}` — e.g. `pixverse/pixverse-c1-it2v`

- c1/v6: duration 1-15s, 360P-1080P; v5.6: 5/8/10s (1080P: 5/8s only)
- c1 excels at dynamic scenes/combat/high-speed motion; v5.6 is legacy
- `it2v` = first-frame i2v, `kf2v` = first+last frame, `r2v` = 1-7 reference images with `@ref_name` prompt syntax
- Audio off by default, enable with `--audio`

### Kling 可灵 (Bailian third-party)

`kling/kling-v3-video-generation`, `kling/kling-v3-omni-video-generation`

- One model code covers t2v/i2v/kf2v — the mode is set by which media you attach; omni adds reference images (`--ref`)
- Duration 3-15s; resolution via mode: 1080P→`pro`, else `std` (720P); ratio 16:9/9:16/1:1

### Vidu (Bailian third-party)

`vidu/viduq3-{pro,turbo}_{text2video,img2video,start-end2video}`, `vidu/viduq2*`

- q3: 1-16s, audio supported (`--audio`); q2: 1-10s, no audio
- 540P/720P/1080P; `start-end2video` = first+last frame

### HappyHorse (Bailian third-party)

`happyhorse-1.1-t2v`, `happyhorse-1.0-t2v`, `happyhorse-1.1-i2v`, `happyhorse-1.0-i2v`

- 3-15s, 720P/1080P; t2v supports many ratios; i2v matches input image ratio

### Jimeng 即梦 (Volcengine Ark)

| Model | Mode | Resolution | Duration | Notes |
|-------|------|-----------|----------|-------|
| `doubao-seedance-2-0-260128` | t2v/i2v | up to 2K | ≤15s | **Default**. Audio, lip-sync, camera control |
| `doubao-seedance-2-0-fast-260128` | t2v/i2v | up to 1080P | ≤15s | Fast variant |
| `doubao-seedance-1-5-pro-251215` | t2v/i2v | up to 1080P | smart | Audio, smart duration |
| `doubao-seedance-1-0-pro` | t2v/i2v | up to 1080P | — | Standard v1 |

- Auth: `ARK_API_KEY` (Bearer token)
- API: `https://ark.cn-beijing.volces.com/api/v3`
- Local images auto-encoded as base64 data URIs
- Ratio: 16:9, 9:16, 1:1, 21:9, etc.

### MiniMax 海螺 AI

| Model | Mode | Resolution | Duration | Notes |
|-------|------|-----------|----------|-------|
| `video-01` | t2v/i2v | 720P | 6s | Covers both modes |

- Auth: Bearer token (`MINIMAX_API_KEY`)
- Local images auto-uploaded via MiniMax file API
- Prompt optimizer enabled by default

## Prompt Refinement Examples

These examples show the Step 0 interactive refinement in action.

### Example 1: Vague short prompt

User: "生成视频:一只猫"

Claude responds with:
> 你的原始提示词比较简短，我帮你打磨了三个版本：
>
> | # | 风格方向 | 优化后提示词 | 建议参数 |
> |---|---------|-------------|---------|
> | 1 | 温馨日常 | 一只橘猫蜷缩在窗台上，午后阳光透过纱帘洒在毛发上，猫咪眯着眼睛打盹，微风轻拂窗帘 | 5s / 16:9 |
> | 2 | 灵动活泼 | 一只黑白奶牛猫在花园里追逐蝴蝶，敏捷跳跃，花瓣被带起在空中飞舞，慢动作特写 | 5s / 16:9 |
> | 3 | 赛博朋克 | 一只发光机械猫在霓虹闪烁的雨夜街头行走，全息投影的鱼在它周围游动，科幻电影质感 | 5s / 9:16 |
>
> 你喜欢哪个方向？也可以说"更诗意""改为雪景""混合1和2"等。

### Example 2: Iterative refinement

User: "第二个不错，但是我想改成在森林里"

Claude regenerates variant 2 with forest setting, maybe adjusting all three:

> 好的，以森林为场景重新打磨：
>
> | # | 风格方向 | 优化后提示词 | 建议参数 |
> |---|---------|-------------|---------|
> | 1 | 灵动森林 | 一只黑白毛色的猫咪在晨光森林中轻盈跳跃，透过树叶的阳光形成光束，苔藓和蕨类植物环绕，慢动作 | 5s / 16:9 |
> | 2 | 神秘森林 | 黑猫在迷雾森林中优雅行走，发光的蘑菇照亮小径，萤火虫在空气中浮动，奇幻电影画风 | 8s / 16:9 |
> | 3 | 雨后森林 | 橘白色小猫在雨后的原始森林中探索，叶片上的水珠闪烁，丁达尔光束穿透树冠，微距镜头跟拍 | 5s / 16:9 |
>
> 哪个更接近你想要的？

User: "用第1个，生成吧"

Claude runs the script with the approved prompt.

## Usage

### Text-to-Video

```bash
# Bailian (default)
python scripts/generate_video.py \
  "一只柴犬在樱花树下奔跑,花瓣随风飘落,电影感镜头" shiba.mp4 \
  --duration 5 --resolution 1080P --ratio 16:9

# Jimeng (即梦)
python scripts/generate_video.py "一只柴犬在樱花树下奔跑" shiba.mp4 \
  --provider jimeng --duration 5

# MiniMax (海螺)
python scripts/generate_video.py "一只柴犬在樱花树下奔跑" shiba.mp4 \
  --provider minimax --duration 6
```

### Image-to-Video

```bash
python scripts/generate_video.py "镜头缓缓推近,人物微笑" out.mp4 --image portrait.png
# Or with a third-party model (local file auto-uploaded):
python scripts/generate_video.py "cinematic dolly-in" out.mp4 \
  --image portrait.png -m pixverse/pixverse-c1-it2v
# Jimeng i2v:
python scripts/generate_video.py "镜头缓缓推近" out.mp4 \
  --image portrait.png --provider jimeng
```

### First+Last Frame (kf2v)

```bash
python scripts/generate_video.py "花苞缓缓绽放成盛开的牡丹" bloom.mp4 \
  --image bud.png --last-frame bloom.png
```

### Reference-to-Video (r2v)

```bash
python scripts/generate_video.py "@girl 在 @cafe 里弹吉他" out.mp4 \
  --ref girl=girl.png --ref cafe=cafe.jpg
```

### Resume a Long-Running Task

```bash
python scripts/generate_video.py --task-id <task-id> out.mp4
```

### Options

| Flag | Meaning | Default |
|------|---------|---------|
| `--provider` | `bailian` / `jimeng` / `minimax` | auto-detect |
| `-m/--model` | model name | auto by mode |
| `-i/--image` | first-frame image (path/URL) | — |
| `--last-frame` | last-frame image → kf2v | — |
| `--ref` | reference image `name=path_or_url`, repeatable → r2v | — |
| `-d/--duration` | seconds | 5 |
| `-r/--resolution` | 360P/480P/540P/720P/1080P | 1080P |
| `--ratio` | 16:9 or 9:16 | 16:9 |
| `-s/--size` | exact `W*H` for size-based models | from resolution+ratio |
| `-n/--negative` | negative prompt (Wan only) | — |
| `--no-prompt-extend` | disable prompt rewriting (Wan only) | extend on |
| `--audio` | enable audio on PixVerse/Kling/Vidu | off |
| `--no-audio` | silent output on Wan audio models | audio on |
| `--seed` | reproducibility (not Kling) | random |
| `--task-id` | resume polling an existing task (Bailian) | — |
| `--list-models` | list models and exit | — |

## Requirements

```bash
pip install requests
```

## Environment Variables

| Variable | Required | Provider | Purpose |
|----------|----------|----------|---------|
| `DASHSCOPE_API_KEY` | yes (Bailian) | Bailian | Bailian API key (https://bailian.console.aliyun.com/) |
| `DASHSCOPE_API_BASE` | no | Bailian | `cn` (default) / `sg` / `us` or a full URL |
| `DASHSCOPE_VIDEO_MODEL` | no | Bailian | default model override |
| `ARK_API_KEY` | yes (Jimeng) | Jimeng | Volcengine Ark API key (https://console.volcengine.com/ark/) |
| `MINIMAX_API_KEY` | yes (MiniMax) | MiniMax | MiniMax API key (https://platform.minimax.io) |

Third-party models on Bailian (PixVerse/Kling/Vidu/HappyHorse) are **Beijing region (`cn`) only**.

## Model Selection Guide

| Use case | Model | Provider |
|----------|-------|----------|
| Best quality t2v, multi-shot story | `wan2.7-t2v-2026-04-25` | Bailian |
| Fast action / combat scenes | `pixverse/pixverse-c1-t2v` | Bailian |
| Smart storyboard, native audio-visual | `kling/kling-v3-video-generation` | Bailian |
| Long clips up to 16s with audio | `vidu/viduq3-pro_text2video` | Bailian |
| Douyin/XHS short-video style | `doubao-seedance-2-0-260128` | Jimeng |
| Smooth motion, natural physics | `video-01` | MiniMax |
| Animate an image (default) | `wan2.6-i2v-flash` | Bailian |
| Transition between two frames | `pixverse/pixverse-c1-kf2v` or `vidu/viduq3-pro_start-end2video` | Bailian |
| Character/subject consistency | `pixverse/pixverse-c1-r2v` or `kling/kling-v3-omni-video-generation` | Bailian |
| Cheap drafts | `wanx2.1-t2v-turbo`, `happyhorse-1.0-t2v` | Bailian |

## Examples

```bash
# Vertical short-video clip for Douyin/Xiaohongshu
python scripts/generate_video.py "赛博朋克雨夜街头,霓虹灯倒映在积水中" \
  city.mp4 --ratio 9:16 --resolution 1080P

# Multi-shot 15s narrative (wan2.7)
python scripts/generate_video.py \
  "第1个镜头[0-5s]: 清晨的茶园,雾气缭绕。第2个镜头[5-10s]: 特写采茶人的手。第3个镜头[10-15s]: 茶叶在杯中舒展" \
  tea.mp4 --duration 15

# Kling with audio, 10 seconds
python scripts/generate_video.py "海浪拍打礁石,海鸥鸣叫" sea.mp4 \
  -m kling/kling-v3-video-generation --audio --duration 10

# Character-consistent scene from reference images (PixVerse r2v)
python scripts/generate_video.py "@hero 挥剑劈开 @monster,火花四溅" fight.mp4 \
  --ref hero=hero.png --ref monster=monster.png -m pixverse/pixverse-c1-r2v

# Jimeng t2v, vertical format
python scripts/generate_video.py "城市日落延时摄影,天空由橙变紫" sunset.mp4 \
  --provider jimeng --duration 10 --ratio 9:16

# MiniMax t2v with image animation
python scripts/generate_video.py "细雨中的古镇小巷,青石板路反光" rain.mp4 \
  --provider minimax --duration 6
```
