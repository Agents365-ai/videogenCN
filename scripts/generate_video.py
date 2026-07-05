#!/usr/bin/env python3
"""Generate video clips via Alibaba Cloud Bailian (DashScope) video models.

Model families: Wan (通义万相), PixVerse (爱诗), Kling (可灵), Vidu, HappyHorse.
Modes: text-to-video (t2v), image-to-video (i2v), first+last frame (kf2v),
reference-to-video (r2v). Tasks are async: submit -> poll /tasks/{id} -> download.

Usage:
  python generate_video.py "prompt" [output.mp4] [options]
  python generate_video.py "prompt" out.mp4 --image first.png              # i2v
  python generate_video.py "prompt" out.mp4 --image a.png --last-frame b.png  # kf2v
  python generate_video.py "@girl dancing" out.mp4 --ref girl=girl.png     # r2v
  python generate_video.py --task-id <id> out.mp4                          # resume
  python generate_video.py --list-models
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

API_ENDPOINTS = {
    "cn": "https://dashscope.aliyuncs.com/api/v1",
    "sg": "https://dashscope-intl.aliyuncs.com/api/v1",
    "us": "https://dashscope-us.aliyuncs.com/api/v1",
}
DEFAULT_API_BASE = API_ENDPOINTS["cn"]
SUBMIT_PATH = "/services/aigc/video-generation/video-synthesis"

DEFAULT_MODELS = {
    "t2v": "wan2.7-t2v-2026-04-25",
    "i2v": "wan2.6-i2v-flash",
    "kf2v": "pixverse/pixverse-c1-kf2v",
    "r2v": "pixverse/pixverse-c1-r2v",
}

# Wan family
WAN_T2V_RATIO = {"wan2.7-t2v-2026-04-25"}  # takes resolution + ratio
WAN_T2V_SIZE = {"wan2.5-t2v-preview", "wan2.2-t2v-plus",
                "wanx2.1-t2v-turbo", "wanx2.1-t2v-plus"}
WAN_I2V = {"wan2.6-i2v-flash", "wan2.6-i2v", "wan2.5-i2v-preview",
           "wan2.2-i2v-plus", "wan2.2-i2v-flash",
           "wanx2.1-i2v-turbo", "wanx2.1-i2v-plus"}
WAN_AUDIO_TOGGLE = {"wan2.6-i2v-flash", "wan2.5-t2v-preview", "wan2.5-i2v-preview"}

# Third-party families (model code -> mode via suffix)
PIXVERSE_VERSIONS = ("c1", "v6", "v5.6")
VIDU_MODELS = {
    "t2v": ["vidu/viduq3-pro_text2video", "vidu/viduq3-turbo_text2video",
            "vidu/viduq2_text2video"],
    "i2v": ["vidu/viduq3-pro_img2video", "vidu/viduq3-turbo_img2video",
            "vidu/viduq2-pro_img2video", "vidu/viduq2-pro-fast_img2video",
            "vidu/viduq2-turbo_img2video"],
    "kf2v": ["vidu/viduq3-pro_start-end2video", "vidu/viduq3-turbo_start-end2video",
             "vidu/viduq2-pro_start-end2video", "vidu/viduq2-turbo_start-end2video"],
}
KLING_MODELS = ["kling/kling-v3-video-generation", "kling/kling-v3-omni-video-generation"]
HAPPYHORSE_MODELS = {
    "t2v": ["happyhorse-1.1-t2v", "happyhorse-1.0-t2v"],
    "i2v": ["happyhorse-1.1-i2v", "happyhorse-1.0-i2v"],
}

# (resolution, ratio) -> "W*H" for size-based parameters
SIZE_TABLE = {
    ("360P", "16:9"): "640*360", ("360P", "9:16"): "360*640",
    ("480P", "16:9"): "832*480", ("480P", "9:16"): "480*832",
    ("540P", "16:9"): "960*540", ("540P", "9:16"): "540*960",
    ("720P", "16:9"): "1280*720", ("720P", "9:16"): "720*1280",
    ("1080P", "16:9"): "1920*1080", ("1080P", "9:16"): "1080*1920",
}

POLL_INTERVAL = 10
POLL_DEADLINE = 1800  # long jobs can legitimately run 10-15 minutes


def get_api_key():
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("Error: DASHSCOPE_API_KEY environment variable not set", file=sys.stderr)
        print("Set it with: export DASHSCOPE_API_KEY='your-api-key'", file=sys.stderr)
        print("Get a key at: https://bailian.console.aliyun.com/", file=sys.stderr)
        sys.exit(1)
    return api_key


def get_api_base():
    base = os.environ.get("DASHSCOPE_API_BASE", DEFAULT_API_BASE)
    return API_ENDPOINTS.get(base, base)


def model_family(model):
    if model.startswith("pixverse/"):
        return "pixverse"
    if model.startswith("kling/"):
        return "kling"
    if model.startswith("vidu/"):
        return "vidu"
    if model.startswith("happyhorse"):
        return "happyhorse"
    return "wan"


def encode_image(path):
    """Encode a local image file as a base64 data URI (Wan/HappyHorse only)."""
    p = Path(path)
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def upload_file(api_key, model, path):
    """Upload a local file to DashScope temporary storage, return oss:// URL.

    Needed for families that only accept public URLs (PixVerse, Kling, Vidu).
    The oss:// URL requires the X-DashScope-OssResourceResolve header on submit.
    """
    rsp = requests.get(
        f"{get_api_base()}/uploads",
        params={"action": "getPolicy", "model": model},
        headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    rsp.raise_for_status()
    data = rsp.json()["data"]
    key = f"{data['upload_dir']}/{Path(path).name}"
    form = {
        "OSSAccessKeyId": data["oss_access_key_id"],
        "Signature": data["signature"],
        "policy": data["policy"],
        "x-oss-object-acl": data["x_oss_object_acl"],
        "x-oss-forbid-overwrite": data["x_oss_forbid_overwrite"],
        "key": key,
        "success_action_status": "200",
    }
    with open(path, "rb") as f:
        up = requests.post(data["upload_host"], data=form,
                           files={"file": (Path(path).name, f)}, timeout=120)
    up.raise_for_status()
    print(f"Uploaded {path} -> oss (48h temporary URL)")
    return f"oss://{key}"


def resolve_media(value, api_key, model, family, state):
    """Turn a path/URL into something the target model accepts."""
    if value.startswith(("http://", "https://", "data:")):
        return value
    if value.startswith("oss://"):
        state["oss"] = True
        return value
    if not os.path.exists(value):
        print(f"Error: image not found: {value}", file=sys.stderr)
        sys.exit(1)
    if family in ("wan", "happyhorse"):
        return encode_image(value)
    state["oss"] = True
    return upload_file(api_key, model, value)


def parse_ref(ref):
    """Parse --ref 'name=path_or_url' or plain 'path_or_url' -> (name, value)."""
    if "=" in ref and "://" not in ref.split("=", 1)[0] and not os.path.exists(ref):
        name, value = ref.split("=", 1)
        return name, value
    return None, ref


def pick_size(args, default="1920*1080"):
    return args.size or SIZE_TABLE.get((args.resolution, args.ratio), default)


def build_body(model, family, mode, args, image_url, last_url, refs):
    inp = {"prompt": args.prompt}
    params = {"duration": args.duration, "watermark": False}
    if model.startswith("wanx2.1") and mode == "t2v":
        del params["duration"]  # wanx2.1 t2v: "duration customization is not supported"
    if args.seed is not None and family != "kling":
        params["seed"] = args.seed

    if family == "wan":
        if args.negative:
            inp["negative_prompt"] = args.negative
        params["prompt_extend"] = not args.no_prompt_extend
        if mode == "i2v":
            inp["img_url"] = image_url
            params["resolution"] = args.resolution
        elif model in WAN_T2V_RATIO:
            params["resolution"] = args.resolution
            params["ratio"] = args.ratio
        else:
            params["size"] = pick_size(args)
        if args.no_audio and model in WAN_AUDIO_TOGGLE:
            params["audio"] = False

    elif family == "pixverse":
        params["audio"] = args.audio
        if mode == "t2v":
            params["size"] = pick_size(args)
        elif mode == "i2v":
            inp["media"] = [{"type": "image_url", "url": image_url}]
            params["resolution"] = args.resolution
        elif mode == "kf2v":
            inp["media"] = [{"type": "first_frame", "url": image_url},
                            {"type": "last_frame", "url": last_url}]
            params["resolution"] = args.resolution
        else:  # r2v: reference prompt uses "@ref_name " syntax
            media = []
            for name, url in refs:
                item = {"type": "image_url", "url": url}
                if name:
                    item["ref_name"] = name
                media.append(item)
            inp["media"] = media
            params["size"] = pick_size(args)

    elif family == "kling":
        params["mode"] = "pro" if args.resolution == "1080P" else "std"
        params["aspect_ratio"] = args.ratio
        params["audio"] = args.audio
        media = []
        if image_url:
            media.append({"type": "first_frame", "url": image_url})
        if last_url:
            media.append({"type": "last_frame", "url": last_url})
        media.extend({"type": "refer", "url": url} for _, url in refs)
        if media:
            inp["media"] = media

    elif family == "vidu":
        params["resolution"] = args.resolution
        if args.audio:
            params["audio"] = True  # viduq3 only
        if mode == "i2v":
            inp["media"] = [{"type": "image", "url": image_url}]
        elif mode == "kf2v":  # first array element = opening frame, second = closing
            inp["media"] = [{"type": "image", "url": image_url},
                            {"type": "image", "url": last_url}]

    else:  # happyhorse
        params["resolution"] = args.resolution
        if mode == "t2v":
            params["ratio"] = args.ratio
        else:
            inp["media"] = [{"type": "first_frame", "url": image_url}]

    return {"model": model, "input": inp, "parameters": params}


def check_mode(model, family, mode):
    """Verify the model variant matches the requested mode; exit with hint if not."""
    ok, hint = True, None
    if family == "wan":
        if mode == "i2v":
            ok = model in WAN_I2V or "i2v" in model
        elif mode == "t2v":
            ok = "t2v" in model
        else:
            ok, hint = False, ("Wan models here support t2v/i2v only; use e.g. "
                               f"'{DEFAULT_MODELS[mode]}' for {mode}")
    elif family == "pixverse":
        suffix = {"t2v": "-t2v", "i2v": "-it2v", "kf2v": "-kf2v", "r2v": "-r2v"}[mode]
        ok = model.endswith(suffix)
        hint = f"PixVerse {mode} needs a model ending in '{suffix}'"
    elif family == "vidu":
        suffix = {"t2v": "_text2video", "i2v": "_img2video",
                  "kf2v": "_start-end2video"}.get(mode)
        ok = suffix is not None and model.endswith(suffix)
        hint = (f"Vidu {mode} needs a model ending in '{suffix}'" if suffix
                else "Vidu has no r2v variant here; use PixVerse or Kling omni")
    elif family == "kling":
        if mode == "r2v":
            ok = model.endswith("omni-video-generation")
            hint = "Kling reference generation needs kling/kling-v3-omni-video-generation"
    else:  # happyhorse
        suffix = {"t2v": "-t2v", "i2v": "-i2v"}.get(mode)
        ok = suffix is not None and model.endswith(suffix)
        hint = (f"HappyHorse {mode} needs a model ending in '{suffix}'" if suffix
                else "HappyHorse here supports t2v/i2v only")
    if not ok:
        print(f"Error: model '{model}' does not match mode '{mode}'. {hint}",
              file=sys.stderr)
        sys.exit(1)


def submit_task(api_key, api_base, body, oss_used):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable",
    }
    if oss_used:
        headers["X-DashScope-OssResourceResolve"] = "enable"
    rsp = requests.post(api_base + SUBMIT_PATH, headers=headers, json=body, timeout=60)
    data = rsp.json()
    task_id = data.get("output", {}).get("task_id")
    if rsp.status_code != 200 or not task_id:
        print(f"Error: submit failed ({rsp.status_code}): "
              f"{data.get('code')} {data.get('message')}", file=sys.stderr)
        sys.exit(1)
    return task_id


def poll_task(api_key, api_base, task_id):
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + POLL_DEADLINE
    while True:
        rsp = requests.get(f"{api_base}/tasks/{task_id}", headers=headers, timeout=30)
        output = rsp.json().get("output", {})
        status = output.get("task_status", "UNKNOWN")
        if status == "SUCCEEDED":
            return output.get("video_url")
        if status in ("FAILED", "CANCELED", "UNKNOWN"):
            print(f"Error: task {task_id} ended with status {status}: "
                  f"{output.get('code')} {output.get('message')}", file=sys.stderr)
            sys.exit(1)
        if time.time() > deadline:
            print(f"Error: task {task_id} still {status} after 30 minutes.",
                  file=sys.stderr)
            print(f"Resume later with: --task-id {task_id}", file=sys.stderr)
            sys.exit(1)
        print(f"Status: {status}, waiting {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)


def download_video(url, output_path):
    rsp = requests.get(url, timeout=300)
    rsp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rsp.content)
    return len(rsp.content)


def list_models():
    print("Wan 通义万相 (t2v/i2v; local images via base64):")
    print(f"  {DEFAULT_MODELS['t2v']} (t2v default; multi-shot, up to 15s)")
    for m in sorted(WAN_T2V_SIZE):
        print(f"  {m}")
    print(f"  {DEFAULT_MODELS['i2v']} (i2v default)")
    for m in sorted(WAN_I2V - {DEFAULT_MODELS['i2v']}):
        print(f"  {m}")
    print("\nPixVerse 爱诗 (t2v/it2v/kf2v/r2v; 1-15s, up to 1080P):")
    for v in PIXVERSE_VERSIONS:
        print(f"  pixverse/pixverse-{v}-{{t2v,it2v,kf2v,r2v}}")
    print("\nKling 可灵 (one model covers t2v/i2v/kf2v; omni adds references):")
    for m in KLING_MODELS:
        print(f"  {m}")
    print("\nVidu (q3: 1-16s + audio; q2: 1-10s):")
    for models in VIDU_MODELS.values():
        for m in models:
            print(f"  {m}")
    print("\nHappyHorse (t2v/i2v; 3-15s, local images via base64):")
    for models in HAPPYHORSE_MODELS.values():
        for m in models:
            print(f"  {m}")
    print("\nMode defaults: " + ", ".join(f"{k}={v}" for k, v in DEFAULT_MODELS.items()))
    print("Endpoints (DASHSCOPE_API_BASE): " + ", ".join(API_ENDPOINTS)
          + " (third-party models: cn only)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate video via Alibaba Cloud Bailian video models "
                    "(Wan/PixVerse/Kling/Vidu/HappyHorse)")
    parser.add_argument("prompt", nargs="?", help="video description")
    parser.add_argument("output", nargs="?", default="./generated-video.mp4",
                        help="output MP4 path (default: ./generated-video.mp4)")
    parser.add_argument("-m", "--model", help="model name (default: auto by mode)")
    parser.add_argument("-i", "--image", help="first-frame image (path or URL) -> i2v")
    parser.add_argument("--last-frame", help="last-frame image (with --image) -> kf2v")
    parser.add_argument("--ref", action="append", default=[],
                        help="reference image 'name=path_or_url' (repeatable) -> r2v; "
                             "mention as '@name ' in the prompt")
    parser.add_argument("-d", "--duration", type=int, default=5,
                        help="duration in seconds (default: 5)")
    parser.add_argument("-r", "--resolution", default="1080P",
                        choices=["360P", "480P", "540P", "720P", "1080P"],
                        help="output resolution (default: 1080P)")
    parser.add_argument("--ratio", default="16:9", choices=["16:9", "9:16"],
                        help="aspect ratio (default: 16:9)")
    parser.add_argument("-s", "--size", help="exact size 'W*H' for size-based models")
    parser.add_argument("-n", "--negative", help="negative prompt (Wan only)")
    parser.add_argument("--no-prompt-extend", action="store_true",
                        help="disable automatic prompt rewriting (Wan only)")
    parser.add_argument("--audio", action="store_true",
                        help="enable audio on PixVerse/Kling/Vidu (their default is off)")
    parser.add_argument("--no-audio", action="store_true",
                        help="silent output on Wan models that default to audio")
    parser.add_argument("--seed", type=int, help="random seed for reproducibility")
    parser.add_argument("--task-id", help="resume polling an existing task")
    parser.add_argument("--list-models", action="store_true", help="list models and exit")
    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    api_key = get_api_key()
    api_base = get_api_base()
    output_path = Path(args.output)

    if args.task_id:
        video_url = poll_task(api_key, api_base, args.task_id)
    else:
        if not args.prompt:
            parser.error("prompt is required (or use --task-id / --list-models)")
        if args.last_frame and not args.image:
            parser.error("--last-frame requires --image (the first frame)")

        if args.ref:
            mode = "r2v"
        elif args.image and args.last_frame:
            mode = "kf2v"
        elif args.image:
            mode = "i2v"
        else:
            mode = "t2v"

        model = args.model or os.environ.get("DASHSCOPE_VIDEO_MODEL") \
            or DEFAULT_MODELS[mode]
        family = model_family(model)
        check_mode(model, family, mode)

        state = {"oss": False}
        image_url = last_url = None
        if args.image:
            image_url = resolve_media(args.image, api_key, model, family, state)
        if args.last_frame:
            last_url = resolve_media(args.last_frame, api_key, model, family, state)
        refs = []
        for ref in args.ref:
            name, value = parse_ref(ref)
            refs.append((name, resolve_media(value, api_key, model, family, state)))

        body = build_body(model, family, mode, args, image_url, last_url, refs)
        print(f"Model: {model} ({family}, {mode})")
        task_id = submit_task(api_key, api_base, body, state["oss"])
        print(f"Task submitted: {task_id}")
        video_url = poll_task(api_key, api_base, task_id)

    if not video_url:
        print("Error: task succeeded but no video_url in response", file=sys.stderr)
        sys.exit(1)
    print("Downloading video (result URLs expire after 24h)...")
    size = download_video(video_url, output_path)
    print(f"Saved: {output_path} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
