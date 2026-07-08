"""Alibaba Cloud Bailian (DashScope) video generation provider.

Supports five model families through the unified DashScope API gateway:
Wan (通义万相), PixVerse (爱诗), Kling (可灵), Vidu, HappyHorse.
"""

import base64
import mimetypes
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

from providers.base import VideoProvider, pick_size

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_ENDPOINTS = {
    "cn": "https://dashscope.aliyuncs.com/api/v1",
    "sg": "https://dashscope-intl.aliyuncs.com/api/v1",
    "us": "https://dashscope-us.aliyuncs.com/api/v1",
}
DEFAULT_API_BASE = API_ENDPOINTS["cn"]
SUBMIT_PATH = "/services/aigc/video-generation/video-synthesis"

DEFAULT_MODELS: dict[str, str] = {
    "t2v": "wan2.7-t2v-2026-04-25",
    "i2v": "wan2.6-i2v-flash",
    "kf2v": "pixverse/pixverse-c1-kf2v",
    "r2v": "pixverse/pixverse-c1-r2v",
}

# Wan family
WAN_T2V_RATIO = {"wan2.7-t2v-2026-04-25"}
WAN_T2V_SIZE = {"wan2.5-t2v-preview", "wan2.2-t2v-plus",
                "wanx2.1-t2v-turbo", "wanx2.1-t2v-plus"}
WAN_I2V = {"wan2.6-i2v-flash", "wan2.6-i2v", "wan2.5-i2v-preview",
           "wan2.2-i2v-plus", "wan2.2-i2v-flash",
           "wanx2.1-i2v-turbo", "wanx2.1-i2v-plus"}
WAN_AUDIO_TOGGLE = {"wan2.6-i2v-flash", "wan2.5-t2v-preview", "wan2.5-i2v-preview"}

# Third-party families (model code -> mode via suffix)
PIXVERSE_VERSIONS = ("c1", "v6", "v5.6")
VIDU_MODELS: dict[str, list[str]] = {
    "t2v": ["vidu/viduq3-pro_text2video", "vidu/viduq3-turbo_text2video",
            "vidu/viduq2_text2video"],
    "i2v": ["vidu/viduq3-pro_img2video", "vidu/viduq3-turbo_img2video",
            "vidu/viduq2-pro_img2video", "vidu/viduq2-pro-fast_img2video",
            "vidu/viduq2-turbo_img2video"],
    "kf2v": ["vidu/viduq3-pro_start-end2video", "vidu/viduq3-turbo_start-end2video",
             "vidu/viduq2-pro_start-end2video", "vidu/viduq2-turbo_start-end2video"],
}
KLING_MODELS = ["kling/kling-v3-video-generation", "kling/kling-v3-omni-video-generation"]
HAPPYHORSE_MODELS: dict[str, list[str]] = {
    "t2v": ["happyhorse-1.1-t2v", "happyhorse-1.0-t2v"],
    "i2v": ["happyhorse-1.1-i2v", "happyhorse-1.0-i2v"],
}


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class BailianProvider(VideoProvider):
    name = "bailian"
    env_var = "DASHSCOPE_API_KEY"
    model_env_var = "DASHSCOPE_VIDEO_MODEL"

    @property
    def api_base(self) -> str:
        base = os.environ.get("DASHSCOPE_API_BASE", DEFAULT_API_BASE)
        return API_ENDPOINTS.get(base, base)

    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    def default_models(self) -> dict[str, str]:
        return DEFAULT_MODELS

    @property
    def supported_modes(self) -> list[str]:
        return ["t2v", "i2v", "kf2v", "r2v"]

    # ------------------------------------------------------------------
    # Family dispatch
    # ------------------------------------------------------------------

    @staticmethod
    def _family(model: str) -> str:
        if model.startswith("pixverse/"):
            return "pixverse"
        if model.startswith("kling/"):
            return "kling"
        if model.startswith("vidu/"):
            return "vidu"
        if model.startswith("happyhorse"):
            return "happyhorse"
        return "wan"

    # ------------------------------------------------------------------
    # Media resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_image(path: str) -> str:
        """Encode a local image file as a base64 data URI (Wan/HappyHorse only)."""
        p = Path(path)
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        data = base64.b64encode(p.read_bytes()).decode()
        return f"data:{mime};base64,{data}"

    def _upload_file(self, model: str, path: str) -> str:
        """Upload a local file to DashScope temporary storage, return oss:// URL.

        Needed for families that only accept public URLs (PixVerse, Kling, Vidu).
        The oss:// URL requires the X-DashScope-OssResourceResolve header on submit.
        """
        api_key = self.api_key
        rsp = requests.get(
            f"{self.api_base}/uploads",
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

    def resolve_media(self, path_or_url: str, model: str = "") -> tuple[str, bool]:
        """Turn a path/URL into something the target model accepts.

        Returns (resolved_value, needs_oss_header).
        """
        if path_or_url.startswith(("http://", "https://", "data:")):
            return path_or_url, False
        if path_or_url.startswith("oss://"):
            return path_or_url, True
        if not os.path.exists(path_or_url):
            print(f"Error: image not found: {path_or_url}", file=sys.stderr)
            sys.exit(1)
        family = self._family(model) if model else "wan"
        if family in ("wan", "happyhorse"):
            return self._encode_image(path_or_url), False
        return self._upload_file(model, path_or_url), True

    # ------------------------------------------------------------------
    # Mode validation
    # ------------------------------------------------------------------

    def check_mode(self, model: str, mode: str) -> None:
        """Verify the model variant matches the requested mode; exit with hint if not."""
        family = self._family(model)
        ok, hint = True, None
        if family == "wan":
            if mode == "i2v":
                ok = model in WAN_I2V or "i2v" in model
            elif mode == "t2v":
                ok = "t2v" in model
            else:
                ok, hint = False, (f"Wan models here support t2v/i2v only; use e.g. "
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

    # ------------------------------------------------------------------
    # Request body builder
    # ------------------------------------------------------------------

    def build_body(self, model: str, mode: str, args,
                   image_url: Optional[str], last_url: Optional[str],
                   refs: list[tuple[Optional[str], str]]) -> dict:
        family = self._family(model)
        inp: dict = {"prompt": args.prompt}
        params: dict = {"duration": args.duration, "watermark": False}

        if model.startswith("wanx2.1") and mode == "t2v":
            del params["duration"]  # wanx2.1 t2v does not support custom duration
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
                    item: dict = {"type": "image_url", "url": url}
                    if name:
                        item["ref_name"] = name
                    media.append(item)
                inp["media"] = media
                params["size"] = pick_size(args)

        elif family == "kling":
            params["mode"] = "pro" if args.resolution == "1080P" else "std"
            params["aspect_ratio"] = args.ratio
            params["audio"] = args.audio
            media: list = []
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

    # ------------------------------------------------------------------
    # Async lifecycle: submit / poll / download
    # ------------------------------------------------------------------

    def submit(self, body: dict, oss_used: bool = False) -> str:
        headers = {
            "Content-Type": "application/json",
            **self.auth_headers(),
            "X-DashScope-Async": "enable",
        }
        if oss_used:
            headers["X-DashScope-OssResourceResolve"] = "enable"
        rsp = requests.post(self.api_base + SUBMIT_PATH, headers=headers,
                            json=body, timeout=60)
        data = rsp.json()
        task_id = data.get("output", {}).get("task_id")
        if rsp.status_code != 200 or not task_id:
            print(f"Error: submit failed ({rsp.status_code}): "
                  f"{data.get('code')} {data.get('message')}", file=sys.stderr)
            sys.exit(1)
        return task_id

    def _poll_request(self, task_id: str):
        headers = self.auth_headers()
        return requests.get(f"{self.api_base}/tasks/{task_id}",
                            headers=headers, timeout=30)

    def _parse_poll_response(self, rsp) -> tuple[str, Optional[str], str]:
        output = rsp.json().get("output", {})
        status = output.get("task_status", "UNKNOWN")
        video_url = output.get("video_url")
        err = f"{output.get('code', '')} {output.get('message', '')}"
        return status, video_url, err

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models_text(self) -> str:
        lines = []
        lines.append("Wan 通义万相 (t2v/i2v; local images via base64):")
        lines.append(f"  {DEFAULT_MODELS['t2v']} (t2v default; multi-shot, up to 15s)")
        for m in sorted(WAN_T2V_SIZE):
            lines.append(f"  {m}")
        lines.append(f"  {DEFAULT_MODELS['i2v']} (i2v default)")
        for m in sorted(WAN_I2V - {DEFAULT_MODELS['i2v']}):
            lines.append(f"  {m}")
        lines.append("\nPixVerse 爱诗 (t2v/it2v/kf2v/r2v; 1-15s, up to 1080P):")
        for v in PIXVERSE_VERSIONS:
            lines.append(f"  pixverse/pixverse-{v}-{{t2v,it2v,kf2v,r2v}}")
        lines.append("\nKling 可灵 (one model covers t2v/i2v/kf2v; omni adds references):")
        for m in KLING_MODELS:
            lines.append(f"  {m}")
        lines.append("\nVidu (q3: 1-16s + audio; q2: 1-10s):")
        for models in VIDU_MODELS.values():
            for m in models:
                lines.append(f"  {m}")
        lines.append("\nHappyHorse (t2v/i2v; 3-15s, local images via base64):")
        for models in HAPPYHORSE_MODELS.values():
            for m in models:
                lines.append(f"  {m}")
        lines.append(f"\nMode defaults: "
                      f"{', '.join(f'{k}={v}' for k, v in DEFAULT_MODELS.items())}")
        lines.append("Endpoints (DASHSCOPE_API_BASE): " + ", ".join(API_ENDPOINTS)
                      + " (third-party models: cn only)")
        return "\n".join(lines)
