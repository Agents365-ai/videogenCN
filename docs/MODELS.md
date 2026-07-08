# videogenCN — Model Reference

> Auto-generated from [models.json](models.json) · Last updated: 2026-07-08
> Prices are approximate (USD per second of output). Actual pricing depends on resolution and region. Check provider consoles for current rates.

## Quick Reference

| Use case | Model | Provider | Price |
|----------|-------|----------|-------|
| 最佳画质文生视频，多镜头故事 | `wan2.7-t2v-2026-04-25` | Bailian 百炼 | $0.07–0.14/s |
| 默认图生视频，让静态图动起来 | `wan2.6-i2v-flash` | Bailian 百炼 | $0.05–0.10/s |
| 默认首尾帧过渡动画 | `pixverse-c1-kf2v` | Bailian 百炼 | $0.05–0.12/s |
| 默认角色一致性，多参考图生成 | `pixverse-c1-r2v` | Bailian 百炼 | $0.05–0.12/s |
| 抖音/小红书短视频风格，需要镜头运动 | `doubao-seedance-2-0-260128` | Jimeng 即梦 | $0.06–0.14/s |
| 流畅运动、自然物理效果 | `video-01` | MiniMax 海螺 AI | $0.03–0.06/s |
| 腾讯基础设施上的中文文生/图生视频 | `hy-video-1.5` | Hunyuan 混元 | $0.03–0.06/s |

---

## Bailian 百炼 — Alibaba Cloud Bailian (DashScope)

Five model families under one API key. Largest selection of models and modes.

- **API Key**: `DASHSCOPE_API_KEY` → [Get Key](https://bailian.console.aliyun.com/)
- **Region**: cn / sg / us
- ⚠️ Third-party models (PixVerse/Kling/Vidu/HappyHorse) are cn region only.

| Model | Family | Modes | Resolution | Duration | Audio | Camera | Multi-shot | Price | Use Case |
|-------|--------|-------|------------|----------|-------|--------|------------|-------|----------|
| `wan2.7-t2v-2026-04-25 ⭐` | Wan 通义万相 | 文生视频 | 720P / 1080P | ≤ 15s | — | — | ✅ | $0.07–0.14/s | 最佳画质文生视频，多镜头故事 |
| `wan2.5-t2v-preview` | Wan 通义万相 | 文生视频 | 480P – 1080P | 5 / 10s | ✅ | — | — | $0.05–0.10/s | 需要音频的文生视频 |
| `wan2.2-t2v-plus` | Wan 通义万相 | 文生视频 | 480P / 1080P | 5s | — | — | — | $0.04–0.08/s | 稳定可靠的短片段 |
| `wanx2.1-t2v-turbo` | Wan 通义万相 | 文生视频 | 480P – 720P | 3–5s | — | — | — | $0.02–0.04/s | 快速草稿 / 低成本批量 |
| `wan2.6-i2v-flash ⭐` | Wan 通义万相 | 图生视频 | 720P / 1080P | 2–15s | — | — | — | $0.05–0.10/s | 默认图生视频，让静态图动起来 |
| `wan2.6-i2v` | Wan 通义万相 | 图生视频 | 720P / 1080P | 2–15s | — | — | — | $0.07–0.12/s | 最高画质的图生视频 |
| `pixverse-c1-t2v` | PixVerse 爱诗 | 文生视频 | 360P – 1080P | 1–15s | 🔘 可选 | — | — | $0.04–0.10/s | 快速动作 / 打斗场景 |
| `pixverse-c1-it2v` | PixVerse 爱诗 | 图生视频 | 360P – 1080P | 1–15s | 🔘 可选 | — | — | $0.04–0.10/s | 首帧图生视频 |
| `pixverse-c1-kf2v ⭐` | PixVerse 爱诗 | 首尾帧 | 360P – 1080P | 1–15s | 🔘 可选 | — | — | $0.05–0.12/s | 默认首尾帧过渡动画 |
| `pixverse-c1-r2v ⭐` | PixVerse 爱诗 | 参考生视频 | 360P – 1080P | 1–15s | 🔘 可选 | — | — | $0.05–0.12/s | 默认角色一致性，多参考图生成 |
| `kling-v3` | Kling 可灵 | 文生视频, 图生视频, 首尾帧 | 720P (std) / 1080P (pro) | 3–15s | 🔘 可选 | — | — | $0.06–0.14/s | 智能分镜 + 原生音画同步 |
| `kling-v3-omni` | Kling 可灵 | 文生视频, 图生视频, 首尾帧, 参考生视频 | 720P (std) / 1080P (pro) | 3–15s | 🔘 可选 | — | — | $0.08–0.14/s | 需要参考图的全模式生成 |
| `viduq3-pro` | Vidu | 文生视频, 图生视频, 首尾帧 | 540P – 1080P | 1–16s | ✅ | — | — | $0.06–0.12/s | 超长片段 + 音频 |
| `happyhorse-1.1-t2v` | HappyHorse | 文生视频 | 720P / 1080P | 3–15s | — | — | — | $0.03–0.06/s | 多比例文生视频 |
| `happyhorse-1.1-i2v` | HappyHorse | 图生视频 | 720P / 1080P | 3–15s | — | — | — | $0.03–0.06/s | 图生视频，自动匹配输入比例 |

## Jimeng 即梦 — Volcengine Ark (Jimeng / 即梦)

ByteDance's video model. Strong at short-video style, native audio, camera motion control.

- **API Key**: `ARK_API_KEY` → [Get Key](https://console.volcengine.com/ark/)
- **Region**: cn-beijing

| Model | Family | Modes | Resolution | Duration | Audio | Camera | Multi-shot | Price | Use Case |
|-------|--------|-------|------------|----------|-------|--------|------------|-------|----------|
| `doubao-seedance-2-0-260128 ⭐` | Seedance 2.0 | 文生视频, 图生视频 | up to 2K | ≤ 15s | ✅ | ✅ | — | $0.06–0.14/s | 抖音/小红书短视频风格，需要镜头运动 |
| `doubao-seedance-2-0-fast-260128` | Seedance 2.0 | 文生视频, 图生视频 | up to 1080P | ≤ 15s | ✅ | ✅ | — | $0.04–0.08/s | 快速生成，短视频批量 |
| `doubao-seedance-1-5-pro-251215` | Seedance 1.5 | 文生视频, 图生视频 | up to 1080P | smart | ✅ | — | — | $0.04–0.08/s | 智能时长 + 音频 |

## MiniMax 海螺 AI — MiniMax (Hailuo AI)

Simple API, smooth motion, natural physics. Prompt optimizer built in.

- **API Key**: `MINIMAX_API_KEY` → [Get Key](https://platform.minimax.io)
- **Region**: global

| Model | Family | Modes | Resolution | Duration | Audio | Camera | Multi-shot | Price | Use Case |
|-------|--------|-------|------------|----------|-------|--------|------------|-------|----------|
| `video-01 ⭐` | Hailuo | 文生视频, 图生视频 | 720P | 6s | — | — | — | $0.03–0.06/s | 流畅运动、自然物理效果 |

## Hunyuan 混元 — Tencent Hunyuan (混元)

Tencent's video model. Chinese-native, with experimental portrait animation and effects models.

- **API Key**: `HUNYUAN_API_KEY` → [Get Key](https://console.cloud.tencent.com/hunyuan)
- **Region**: cn

| Model | Family | Modes | Resolution | Duration | Audio | Camera | Multi-shot | Price | Use Case |
|-------|--------|-------|------------|----------|-------|--------|------------|-------|----------|
| `hy-video-1.5 ⭐` | Hunyuan | 文生视频, 图生视频 | 720P | 5–10s | — | — | — | $0.03–0.06/s | 腾讯基础设施上的中文文生/图生视频 |
| `yt-video-2.0 ⚠️` | YouTu (实验性) | 图生视频 | — | — | — | — | — | — | 通用图生视频 (实验性) |
| `yt-video-fx ⚠️` | YouTu (实验性) | 图生视频 | — | — | — | — | — | — | 视频特效 (实验性) |
| `yt-video-humanactor ⚠️` | YouTu (实验性) | 图生视频 | — | — | — | — | — | — | 人像动画/驱动 (实验性) |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ⭐ | Default model for this mode |
| ✅ | Supported |
| — | Not supported |
| 🔘 | Optional (enable with flag) |
| ⚠️ | Experimental — API may change, limited param support |

- **audio**: 内置音频生成或可选音频轨道
- **camera_control**: 镜头运动控制 (推拉摇移跟)
- **multi_shot**: 多镜头分段描述 (Wan 2.7 专有)
- **experimental**: 实验性功能，API可能变更，参数支持有限
