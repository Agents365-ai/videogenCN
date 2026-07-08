"""Abstract base class for video generation providers."""

import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


# Shared (resolution, ratio) -> "W*H" lookup for size-based parameters
SIZE_TABLE: dict[tuple[str, str], str] = {
    ("360P", "16:9"): "640*360", ("360P", "9:16"): "360*640",
    ("480P", "16:9"): "832*480", ("480P", "9:16"): "480*832",
    ("540P", "16:9"): "960*540", ("540P", "9:16"): "540*960",
    ("720P", "16:9"): "1280*720", ("720P", "9:16"): "720*1280",
    ("1080P", "16:9"): "1920*1080", ("1080P", "9:16"): "1080*1920",
}


def pick_size(args, default: str = "1920*1080") -> str:
    """Convert resolution + ratio to a W*H string."""
    return args.size or SIZE_TABLE.get((args.resolution, args.ratio), default)


class VideoProvider:
    """Base class for video generation backends.

    Subclasses must implement at minimum:
      - name, env_var (class attrs or properties)
      - api_key property
      - api_base property (or _default_api_base)
      - auth_headers()
      - default_models
      - supported_modes
      - check_mode(model, mode)
      - build_body(model, mode, args, image_url, last_url, refs)
      - submit(body)
      - poll(task_id)
      - resolve_media(path_or_url, model)
      - list_models_text()
    """

    name: str = "base"
    env_var: str = ""
    model_env_var: str | None = None  # env var for model override (None = not supported)
    _default_api_base: str = ""

    # Subclasses may override these
    POLL_INTERVAL: int = 10
    POLL_DEADLINE: int = 1800  # 30 minutes max

    @property
    def api_key(self) -> str:
        val = os.environ.get(self.env_var)
        if not val:
            print(f"Error: {self.env_var} environment variable not set", file=sys.stderr)
            print(f"Set it with: export {self.env_var}='your-api-key'", file=sys.stderr)
            sys.exit(1)
        return val

    @property
    def api_base(self) -> str:
        return self._default_api_base

    def auth_headers(self) -> dict:
        raise NotImplementedError

    @property
    def default_models(self) -> dict[str, str]:
        raise NotImplementedError

    @property
    def supported_modes(self) -> list[str]:
        raise NotImplementedError

    def check_mode(self, model: str, mode: str) -> None:
        """Validate model supports this mode; exit with hint if not."""
        raise NotImplementedError

    def build_body(self, model: str, mode: str, args,
                   image_url: Optional[str], last_url: Optional[str],
                   refs: list[tuple[Optional[str], str]]) -> dict:
        raise NotImplementedError

    def submit(self, body: dict) -> str:
        raise NotImplementedError

    def poll(self, task_id: str) -> Optional[str]:
        """Poll until completion or deadline. Returns video_url. Exits on failure."""
        deadline = time.time() + self.POLL_DEADLINE
        while True:
            rsp = self._poll_request(task_id)
            status, video_url, err_msg = self._parse_poll_response(rsp)
            if status == "SUCCEEDED":
                return video_url
            if status in ("FAILED", "CANCELED", "UNKNOWN"):
                print(f"Error: task {task_id} ended with status {status}: {err_msg}",
                      file=sys.stderr)
                sys.exit(1)
            if time.time() > deadline:
                print(f"Error: task {task_id} still {status} after "
                      f"{self.POLL_DEADLINE // 60} minutes.", file=sys.stderr)
                print(f"Resume later with: --task-id {task_id}", file=sys.stderr)
                sys.exit(1)
            print(f"Status: {status}, waiting {self.POLL_INTERVAL}s...")
            time.sleep(self.POLL_INTERVAL)

    def _poll_request(self, task_id: str):
        """Make a single poll request. Override for provider-specific endpoint."""
        raise NotImplementedError

    def _parse_poll_response(self, rsp) -> tuple[str, Optional[str], str]:
        """Parse poll response -> (status, video_url_or_None, error_message)."""
        raise NotImplementedError

    def resolve_media(self, path_or_url: str, model: str = "") -> tuple[str, bool]:
        """Turn a path/URL into something the API accepts.

        Returns (resolved_value, needs_extra_header).
        """
        raise NotImplementedError

    def list_models_text(self) -> str:
        """Pretty-printed model list string."""
        raise NotImplementedError
