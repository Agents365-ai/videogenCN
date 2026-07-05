# Videogen-Wan 🎬

[English](README.md)

一个 Claude Code / OpenClaw 技能,通过阿里云百炼(DashScope)API 调用国产视频大模型生成视频片段 —— 一个 API Key 通吃通义万相(Wan)、爱诗(PixVerse)、可灵(Kling)、Vidu、HappyHorse。

## 为什么选择这个技能

| | 原生 Claude Code | Videogen-Wan |
|---|---|---|
| 文生视频 | ❌ | ✅ 万相、爱诗、可灵、Vidu、HappyHorse |
| 图生视频 | ❌ | ✅ 让任意静态图片动起来 |
| 首尾帧生视频 | ❌ | ✅ PixVerse / Kling / Vidu |
| 参考生视频(角色一致性) | ❌ | ✅ PixVerse r2v / Kling omni |
| 中文提示词 | — | ✅ 原生支持 |
| 异步任务处理 | — | ✅ 提交 → 轮询 → 下载,可断点续接 |
| 竖屏(9:16)视频 | — | ✅ 适配抖音 / 小红书 / Shorts |

## 特性

- **一个脚本四种模式**:提示词 → 文生视频;`--image` → 图生视频;再加 `--last-frame` → 首尾帧;`--ref 名字=图片` → 参考生视频
- **五大模型家族**:万相 + 第三方爱诗(c1/v6/v5.6)、可灵 v3、Vidu(q3/q2)、HappyHorse
- **本地图片直接用**:万相/HappyHorse 走 base64;爱诗/可灵/Vidu 自动上传到 DashScope 临时存储换取公网 URL
- **多镜头叙事**:`wan2.7-t2v` 支持最长 15 秒、按镜头分段描述
- **音频控制**:第三方模型用 `--audio` 开启,万相用 `--no-audio` 关闭
- **可续接**:长任务会打印 task id,用 `--task-id` 恢复轮询

## 安装技能

**Claude Code(全局):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git ~/.claude/skills/videogen-wan
```

**Claude Code(项目级):**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git .claude/skills/videogen-wan
```

**OpenClaw:**

```bash
git clone https://github.com/Agents365-ai/videogenCN.git ~/.openclaw/skills/videogen-wan
```

## 系统要求

- Python 3.8+
- `pip install requests`
- 百炼 API Key:https://bailian.console.aliyun.com/

```bash
export DASHSCOPE_API_KEY='your-api-key'
```

可选环境变量:

| 变量 | 用途 |
|------|------|
| `DASHSCOPE_API_BASE` | `cn`(默认)/ `sg` / `us` 或完整 URL |
| `DASHSCOPE_VIDEO_MODEL` | 覆盖默认模型 |

## 快速开始

**自然语言**(在 Claude Code 中):

> 用万相生成一段 5 秒的视频:一只柴犬在樱花树下奔跑

**命令行:**

```bash
# 文生视频
python scripts/generate_video.py "一只柴犬在樱花树下奔跑,花瓣随风飘落" out.mp4

# 图生视频(让静态图动起来)
python scripts/generate_video.py "镜头缓缓推近" out.mp4 --image photo.png

# 竖屏短视频素材
python scripts/generate_video.py "赛博朋克雨夜街头" city.mp4 --ratio 9:16
```

## 模型

| 家族 | 模型 | 模式 | 时长 |
|------|------|------|------|
| 通义万相 | `wan2.7-t2v-*`(文生视频默认)、`wan2.6-i2v-flash`(图生视频默认)、`wan2.5/2.2/wanx2.1` 系列 | 文生、图生 | 最长 15s |
| 爱诗 PixVerse | `pixverse/pixverse-{c1,v6,v5.6}-{t2v,it2v,kf2v,r2v}` | 全部四种 | 1–15s |
| 可灵 Kling | `kling/kling-v3-video-generation`、`kling/kling-v3-omni-video-generation` | 文生、图生、首尾帧(omni 加参考生) | 3–15s |
| Vidu | `vidu/viduq3-{pro,turbo}_{text2video,img2video,start-end2video}`、`viduq2*` | 文生、图生、首尾帧 | q3: 1–16s |
| HappyHorse | `happyhorse-{1.1,1.0}-{t2v,i2v}` | 文生、图生 | 3–15s |

运行 `python scripts/generate_video.py --list-models` 查看当前列表。第三方模型仅限北京(`cn`)地域。

> **费用提示**:视频生成按输出秒数计费(视模型和分辨率约 $0.04–0.14/秒)。结果 URL 24 小时后过期 —— 脚本会立即下载。

## 许可证

MIT

## 作者

**Agents365-ai** — [GitHub](https://github.com/Agents365-ai)
