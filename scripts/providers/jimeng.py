"""Jimeng (即梦) video generation provider via Volcengine Ark API.

Auth: Bearer token via ARK_API_KEY env var.
API docs: https://www.volcengine.com/docs/82379 (Ark Content Generation)
Flow: POST /api/v3/contents/generations/tasks -> poll GET .../tasks/{id} -> download.
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


class JimengProvider(VideoProvider):
    name = "jimeng"
    env_var = "ARK_API_KEY"
    _default_api_base = "https://ark.cn-beijing.volces.com/api/v3"

    POLL_DEADLINE = 1800  # up to 15 minutes

    @property
    def api_key(self) -> str:
        # Primary: ARK_API_KEY; fallback: VOLCENGINE_ACCESS_KEY (legacy)
        for var in ("ARK_API_KEY", "VOLCENGINE_ACCESS_KEY"):
            key = os.environ.get(var, "")
            if key:
                return key
        print("Error: ARK_API_KEY environment variable not set.", file=sys.stderr)
        print("Set it with: export ARK_API_KEY='your-api-key'", file=sys.stderr)
        print("Get a key at: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey",
              file=sys.stderr)
        sys.exit(1)

    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    def default_models(self) -> dict[str, str]:
        return {
            "t2v": "doubao-seedance-2-0-260128",
            "i2v": "doubao-seedance-2-0-260128",
        }

    @property
    def supported_modes(self) -> list[str]:
        return ["t2v", "i2v"]

    def check_mode(self, model: str, mode: str) -> None:
        if mode not in ("t2v", "i2v"):
            print(f"Error: Jimeng provider only supports t2v and i2v, not '{mode}'.",
                  file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Media resolution
    # ------------------------------------------------------------------

    def resolve_media(self, path_or_url: str, model: str = "") -> tuple[str, bool]:
        """Jimeng Ark API accepts HTTP(S) URLs. Local files are base64-encoded."""
        if path_or_url.startswith(("http://", "https://")):
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
        # Build content array (Ark API uses content blocks)
        content: list[dict] = []
        if mode == "i2v" and image_url:
            if image_url.startswith(("http://", "https://")):
                content.append({"type": "image_url", "image_url": image_url})
            else:
                # base64 data URI
                content.append({"type": "image_url", "image_url": image_url})
        content.append({"type": "text", "text": args.prompt})

        body: dict = {
            "model": model,
            "content": content,
            "duration": args.duration,
            "resolution": args.resolution.lower().rstrip("p") + "p",
            "ratio": args.ratio,
            "watermark": False,
        }

        if args.seed is not None:
            body["seed"] = args.seed

        return body

    # ------------------------------------------------------------------
    # Async lifecycle
    # ------------------------------------------------------------------

    def submit(self, body: dict) -> str:
        headers = {"Content-Type": "application/json", **self.auth_headers()}
        rsp = requests.post(
            f"{self.api_base}/contents/generations/tasks",
            headers=headers, json=body, timeout=60)
        data = rsp.json()
        if rsp.status_code != 200:
            print(f"Error: Jimeng submit failed ({rsp.status_code}): "
                  f"{data.get('error', data)}", file=sys.stderr)
            sys.exit(1)
        task_id = data.get("id")
        if not task_id:
            print(f"Error: no task id in Jimeng response: {data}", file=sys.stderr)
            sys.exit(1)
        return task_id

    def _poll_request(self, task_id: str):
        headers = self.auth_headers()
        return requests.get(
            f"{self.api_base}/contents/generations/tasks/{task_id}",
            headers=headers, timeout=30)

    def _parse_poll_response(self, rsp) -> tuple[str, Optional[str], str]:
        """Ark API returns: {id, status, content: {video_url}, ...}"""
        data = rsp.json()
        status = data.get("status", "unknown")
        if status == "succeeded":
            video_url = data.get("content", {}).get("video_url", "")
            return "SUCCEEDED", video_url, ""
        if status in ("failed", "expired", "cancelled"):
            err = data.get("error", {}).get("message", str(data))
            return "FAILED", None, err
        # queued / running / pending
        return status, None, ""

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models_text(self) -> str:
        lines = [
            "Jimeng 即梦 / Seedance (t2v/i2v; Volcengine Ark Bearer token auth):",
            "  doubao-seedance-2-0-260128 (t2v/i2v default; up to 15s, 2K, audio)",
            "  doubao-seedance-2-0-fast-260128 (fast variant)",
            "  doubao-seedance-1-5-pro-251215 (1.5 Pro; audio, smart duration)",
            "  doubao-seedance-1-0-pro (1.0 standard)",
            "",
            "Env vars:",
            "  ARK_API_KEY (required) — https://console.volcengine.com/ark/region:ark+cn-beijing/apikey",
            "",
            "Features: t2v/i2v, native audio, up to 15s, 1080p/2K, lip-sync, camera control",
        ]
        return "\n".join(lines)
