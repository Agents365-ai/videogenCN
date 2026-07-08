"""Tencent Hunyuan (混元) video generation provider via TokenHub API.

Auth: Bearer token via HUNYUAN_API_KEY env var.
API docs: https://cloud.tencent.com/document/product/1823/130081
Flow: POST /v1/api/video/submit -> poll POST /v1/api/video/query -> download.

Models: hy-video-1.5 (t2v/i2v), yt-video-2.0 (i2v), yt-video-fx, yt-video-humanactor.
"""

import base64
import mimetypes
import os
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

from providers.base import VideoProvider


class HunyuanProvider(VideoProvider):
    name = "hunyuan"
    env_var = "HUNYUAN_API_KEY"
    _default_api_base = "https://tokenhub.tencentmaas.com/v1/api/video"

    POLL_DEADLINE = 1800

    @property
    def api_key(self) -> str:
        for var in (self.env_var, "TENCENTCLOUD_SECRET_ID"):
            key = os.environ.get(var, "")
            if key:
                return key
        print(f"Error: {self.env_var} environment variable not set.", file=sys.stderr)
        print("Get a key at: https://console.cloud.tencent.com/hunyuan", file=sys.stderr)
        print(f"Set it with: export {self.env_var}='your-api-key'", file=sys.stderr)
        sys.exit(1)

    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    def default_models(self) -> dict[str, str]:
        return {
            "t2v": "hy-video-1.5",
            "i2v": "hy-video-1.5",
        }

    @property
    def supported_modes(self) -> list[str]:
        return ["t2v", "i2v"]

    def check_mode(self, model: str, mode: str) -> None:
        if mode not in ("t2v", "i2v"):
            print(f"Error: Hunyuan only supports t2v and i2v, not '{mode}'.",
                  file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Media resolution
    # ------------------------------------------------------------------

    def resolve_media(self, path_or_url: str, model: str = "") -> tuple[str, bool]:
        """TokenHub accepts HTTP(S) URLs. Local files encoded as base64 data URIs."""
        if path_or_url.startswith(("http://", "https://", "data:")):
            return path_or_url, False
        if not os.path.exists(path_or_url):
            print(f"Error: image not found: {path_or_url}", file=sys.stderr)
            sys.exit(1)
        mime = mimetypes.guess_type(path_or_url)[0] or "image/png"
        with open(path_or_url, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{data}", False

    # ------------------------------------------------------------------
    # Request body builder
    # ------------------------------------------------------------------

    def build_body(self, model: str, mode: str, args,
                   image_url: Optional[str], last_url: Optional[str],
                   refs: list[tuple[Optional[str], str]]) -> dict:
        body: dict = {
            "model": model,
            "prompt": args.prompt,
        }

        if mode == "i2v" and image_url:
            body["image"] = {"url": image_url}

        return body

    # ------------------------------------------------------------------
    # Async lifecycle
    # ------------------------------------------------------------------

    def submit(self, body: dict) -> str:
        headers = {"Content-Type": "application/json", **self.auth_headers()}
        rsp = requests.post(f"{self.api_base}/submit", headers=headers,
                            json=body, timeout=60)
        data = rsp.json()
        if rsp.status_code != 200:
            print(f"Error: Hunyuan submit failed ({rsp.status_code}): {data}",
                  file=sys.stderr)
            sys.exit(1)
        task_id = data.get("id")
        if not task_id:
            print(f"Error: no task id in Hunyuan response: {data}", file=sys.stderr)
            sys.exit(1)
        return task_id

    def _poll_request(self, task_id: str):
        """TokenHub uses POST for queries (not GET)."""
        headers = {"Content-Type": "application/json", **self.auth_headers()}
        return requests.post(
            f"{self.api_base}/query",
            headers=headers,
            json={"id": task_id},
            timeout=30)

    def _parse_poll_response(self, rsp) -> tuple[str, Optional[str], str]:
        """TokenHub returns: {status, progress, data: {url}}"""
        data = rsp.json()
        status = data.get("status", "unknown")
        if status == "completed":
            video_url = data.get("data", {}).get("url", "")
            if video_url:
                return "SUCCEEDED", video_url, ""
        if status in ("failed", "cancelled"):
            return "FAILED", None, str(data)
        # queued, processing
        progress = data.get("progress", "")
        label = f"{status}" + (f" ({progress}%)" if progress else "")
        return label, None, ""

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models_text(self) -> str:
        lines = [
            "Hunyuan 腾讯混元 (t2v/i2v; TokenHub Bearer token via HUNYUAN_API_KEY):",
            "  hy-video-1.5 (t2v/i2v default; 720p; 5-10s)",
            "  yt-video-2.0 (i2v general; YouTu)",
            "  yt-video-fx (video effects from template)",
            "  yt-video-humanactor (portrait animation/driving)",
            "",
            "Env vars:",
            "  HUNYUAN_API_KEY (required) — https://console.cloud.tencent.com/hunyuan",
            "",
            "Features: Chinese prompts, t2v/i2v, 720p, async with progress tracking",
        ]
        return "\n".join(lines)
