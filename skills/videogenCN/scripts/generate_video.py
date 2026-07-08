#!/usr/bin/env python3
"""Generate video clips via multiple Chinese video generation providers.

Providers: Alibaba Bailian (Wan/PixVerse/Kling/Vidu/HappyHorse),
           Jimeng (Volcengine Ark), MiniMax (Hailuo).
Modes: text-to-video (t2v), image-to-video (i2v), first+last frame (kf2v),
reference-to-video (r2v). Tasks are async: submit -> poll -> download.

Usage:
  python generate_video.py "prompt" [output.mp4] [options]
  python generate_video.py "prompt" out.mp4 --image first.png              # i2v
  python generate_video.py "prompt" out.mp4 --image a.png --last-frame b.png  # kf2v
  python generate_video.py "@girl dancing" out.mp4 --ref girl=girl.png     # r2v
  python generate_video.py --task-id <id> out.mp4                          # resume
  python generate_video.py --list-models
"""

import argparse
import os
import sys
from pathlib import Path

# Allow imports from the providers package next to this script
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

from providers import get_provider, detect_provider, list_providers, register_providers


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def download_video(url: str, output_path: Path) -> int:
    """Download a video from URL, write to output_path, return byte count."""
    rsp = requests.get(url, timeout=300)
    rsp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rsp.content)
    return len(rsp.content)


def parse_ref(ref: str) -> tuple[str | None, str]:
    """Parse --ref 'name=path_or_url' or plain 'path_or_url' -> (name, value)."""
    if "=" in ref and "://" not in ref.split("=", 1)[0] and not os.path.exists(ref):
        name, value = ref.split("=", 1)
        return name, value
    return None, ref


def detect_mode(args) -> str:
    """Determine generation mode from input arguments."""
    if args.ref:
        return "r2v"
    if args.image and args.last_frame:
        return "kf2v"
    if args.image:
        return "i2v"
    return "t2v"


def _detect_provider_from_task(task_id: str):
    """Detect provider from task ID format. Falls back to Bailian."""
    # Ark task IDs: cgt-YYYYMMDDhhmmss-xxxxx
    if task_id.startswith("cgt-"):
        return get_provider("jimeng")
    # MiniMax task IDs: pure numeric (e.g. "417527150997914")
    if task_id.isdigit():
        return get_provider("minimax")
    # Default: Bailian
    return get_provider("bailian")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    register_providers()
    available = list_providers()

    parser = argparse.ArgumentParser(
        description="Generate video via Chinese video models "
                    "(Bailian Wan/PixVerse/Kling/Vidu/HappyHorse, Jimeng, MiniMax)")
    parser.add_argument("prompt", nargs="?", help="video description")
    parser.add_argument("output", nargs="?", default="./generated-video.mp4",
                        help="output MP4 path (default: ./generated-video.mp4)")
    parser.add_argument("-m", "--model", help="model name (default: auto by mode)")
    parser.add_argument("--provider", choices=available,
                        help=f"provider backend (default: auto-detect; available: {', '.join(available)})")
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
                        help="enable audio on PixVerse/Kling/Vidu/Jimeng (default off for third-party)")
    parser.add_argument("--no-audio", action="store_true",
                        help="silent output on Wan models that default to audio")
    parser.add_argument("--camera-motion",
                        help="camera motion description (Jimeng Seedance 2.0; e.g. 'slow push-in, orbit right')")
    parser.add_argument("--seed", type=int, help="random seed for reproducibility")
    parser.add_argument("--task-id", help="resume polling an existing task (auto-detect provider from ID)")
    parser.add_argument("--list-models", action="store_true", help="list all models and exit")
    args = parser.parse_args()

    # --list-models: print from selected provider(s)
    if args.list_models:
        names = [args.provider] if args.provider else available
        for name in names:
            p = get_provider(name)
            print(f"=== {name} ===")
            print(p.list_models_text())
            print()
        return

    # --task-id resume
    if args.task_id:
        if args.provider:
            provider = get_provider(args.provider)
        else:
            provider = _detect_provider_from_task(args.task_id)
        print(f"Resuming task {args.task_id} via provider: {provider.name}")
        video_url = provider.poll(args.task_id)
        if not video_url:
            print("Error: task succeeded but no video_url in response", file=sys.stderr)
            sys.exit(1)
        output_path = Path(args.output)
        print("Downloading video (result URLs expire after 24h)...")
        size = download_video(video_url, output_path)
        print(f"Saved: {output_path} ({size / 1024 / 1024:.1f} MB)")
        return

    # Normal generation flow
    if not args.prompt:
        parser.error("prompt is required (or use --task-id / --list-models)")
    if args.last_frame and not args.image:
        parser.error("--last-frame requires --image (the first frame)")

    # Provider selection
    if args.provider:
        provider = get_provider(args.provider)
    else:
        provider = detect_provider(args.model)

    # Mode detection
    mode = detect_mode(args)
    if mode not in provider.supported_modes:
        print(f"Error: provider '{provider.name}' does not support mode '{mode}'. "
              f"Supported: {', '.join(provider.supported_modes)}", file=sys.stderr)
        sys.exit(1)

    # Model selection
    model_env = provider.model_env_var
    model = (args.model
             or (os.environ.get(model_env) if model_env else None)
             or provider.default_models[mode])
    provider.check_mode(model, mode)

    # Resolve media
    oss_used = False
    image_url = last_url = None
    if args.image:
        image_url, oss = provider.resolve_media(args.image, model)
        oss_used = oss_used or oss
    if args.last_frame:
        last_url, oss = provider.resolve_media(args.last_frame, model)
        oss_used = oss_used or oss
    refs = []
    for ref in args.ref:
        name, value = parse_ref(ref)
        resolved, oss = provider.resolve_media(value, model)
        refs.append((name, resolved))
        oss_used = oss_used or oss

    # Build body, submit, poll
    body = provider.build_body(model, mode, args, image_url, last_url, refs)
    print(f"Model: {model} (provider: {provider.name}, mode: {mode})")

    # Bailian submit() accepts oss_used flag; other providers ignore it
    import inspect
    sig = inspect.signature(provider.submit)
    if "oss_used" in sig.parameters:
        task_id = provider.submit(body, oss_used=oss_used)
    else:
        task_id = provider.submit(body)

    print(f"Task submitted: {task_id}")
    video_url = provider.poll(task_id)

    if not video_url:
        print("Error: task succeeded but no video_url in response", file=sys.stderr)
        sys.exit(1)
    print("Downloading video (result URLs expire after 24h)...")
    output_path = Path(args.output)
    size = download_video(video_url, output_path)
    print(f"Saved: {output_path} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
