"""MiniMax (海螺 AI) video generation provider.

API docs: https://platform.minimax.io/docs
Auth: Bearer token via MINIMAX_API_KEY env var.
Flow: POST /video_generation -> poll GET /query/video_generation
      -> GET /files/retrieve for download URL.
"""

import os
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

from providers.base import VideoProvider


class MiniMaxProvider(VideoProvider):
    name = "minimax"
    env_var = "MINIMAX_API_KEY"
    _default_api_base = "https://api.minimax.chat/v1"

    # MiniMax jobs usually complete within 5-10 minutes
    POLL_DEADLINE = 1200

    @property
    def api_key(self) -> str:
        key = os.environ.get(self.env_var, "")
        if not key:
            print(f"Error: {self.env_var} environment variable not set.", file=sys.stderr)
            print("Get a key at: https://platform.minimax.io", file=sys.stderr)
            print(f"Set it with: export {self.env_var}='your-api-key'", file=sys.stderr)
            sys.exit(1)
        return key

    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    def default_models(self) -> dict[str, str]:
        return {
            "t2v": "video-01",
            "i2v": "video-01",
        }

    @property
    def supported_modes(self) -> list[str]:
        return ["t2v", "i2v"]

    def check_mode(self, model: str, mode: str) -> None:
        if mode not in ("t2v", "i2v"):
            print(f"Error: MiniMax only supports t2v and i2v, not '{mode}'.",
                  file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Media resolution
    # ------------------------------------------------------------------

    def resolve_media(self, path_or_url: str, model: str = "") -> tuple[str, bool]:
        """MiniMax accepts HTTP(S) URLs directly. Local files are uploaded."""
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url, False
        if not os.path.exists(path_or_url):
            print(f"Error: image not found: {path_or_url}", file=sys.stderr)
            sys.exit(1)
        # Upload local file to MiniMax, get file_id back
        file_id = self._upload_file(path_or_url)
        return file_id, False

    def _upload_file(self, path: str) -> str:
        """Upload a local file via MiniMax's file upload API. Returns file_id."""
        fname = os.path.basename(path)
        with open(path, "rb") as f:
            rsp = requests.post(
                f"{self.api_base}/files/upload",
                headers=self.auth_headers(),
                files={"file": (fname, f)},
                data={"purpose": "video_generation"},
                timeout=60)
        rsp.raise_for_status()
        data = rsp.json()
        file_id = data.get("file", {}).get("file_id")
        if not file_id:
            print(f"Error: MiniMax file upload failed: {data}", file=sys.stderr)
            sys.exit(1)
        print(f"Uploaded {path} -> MiniMax (file_id: {file_id})")
        return file_id

    # ------------------------------------------------------------------
    # Request body builder
    # ------------------------------------------------------------------

    def build_body(self, model: str, mode: str, args,
                   image_url: Optional[str], last_url: Optional[str],
                   refs: list[tuple[Optional[str], str]]) -> dict:
        body: dict = {
            "model": model,
            "prompt": args.prompt,
            "duration": args.duration,
            "prompt_optimizer": True,
        }

        if mode == "i2v" and image_url:
            # image_url may be an http(s) URL or a file_id from upload
            if image_url.startswith(("http://", "https://")):
                body["first_frame_image"] = image_url
            else:
                body["first_frame_image"] = f"file_id:{image_url}"

        return body

    # ------------------------------------------------------------------
    # Async lifecycle
    # ------------------------------------------------------------------

    def submit(self, body: dict) -> str:
        headers = {"Content-Type": "application/json", **self.auth_headers()}
        rsp = requests.post(f"{self.api_base}/video_generation",
                            headers=headers, json=body, timeout=60)
        data = rsp.json()
        if rsp.status_code != 200:
            err = data.get("base_resp", {})
            print(f"Error: MiniMax submit failed ({rsp.status_code}): "
                  f"{err.get('status_code')} {err.get('status_msg')}", file=sys.stderr)
            sys.exit(1)
        task_id = data.get("task_id")
        if not task_id:
            print(f"Error: no task_id in MiniMax response: {data}", file=sys.stderr)
            sys.exit(1)
        return task_id

    def _poll_request(self, task_id: str):
        headers = self.auth_headers()
        return requests.get(
            f"{self.api_base}/query/video_generation",
            params={"task_id": task_id},
            headers=headers, timeout=30)

    def _parse_poll_response(self, rsp) -> tuple[str, Optional[str], str]:
        data = rsp.json()
        status = data.get("status", "UNKNOWN")
        if status == "Success":
            file_id = data.get("file_id", "")
            if file_id:
                # Fetch download URL
                dl_rsp = requests.get(
                    f"{self.api_base}/files/retrieve",
                    params={"file_id": file_id},
                    headers=self.auth_headers(), timeout=30)
                dl_data = dl_rsp.json()
                video_url = dl_data.get("file", {}).get("download_url", "")
                return "SUCCEEDED", video_url, ""
            return "SUCCEEDED", None, "no file_id"
        err = data.get("base_resp", {})
        return status, None, f"{err.get('status_code', '')} {err.get('status_msg', '')}"

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models_text(self) -> str:
        lines = [
            "MiniMax 海螺 AI (t2v/i2v; Bearer token auth via MINIMAX_API_KEY):",
            "  video-01 (t2v/i2v default; 6s, 720P)",
            "",
            "Env vars:",
            f"  {self.env_var} (required) — https://platform.minimax.io",
        ]
        return "\n".join(lines)
