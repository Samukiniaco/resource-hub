"""Checa se há nova versão do app no GitHub Releases."""
from __future__ import annotations

import json
import threading
import urllib.request
import urllib.error
from typing import Callable, Optional, Tuple

from app import __version__ as CURRENT_VERSION
from app.config import REQUEST_TIMEOUT
from app.utils.logger import get_logger

logger = get_logger(__name__)

API_LATEST = "https://api.github.com/repos/Samukiniaco/resource-hub/releases/latest"
REPO_URL = "https://github.com/Samukiniaco/resource-hub/releases"

def _parse_version(v: str) -> tuple[int, ...]:
    v = v.strip().lstrip("vV").strip()
    parts = []
    for p in v.split("."):
        num = "".join(c for c in p if c.isdigit())
        try:
            parts.append(int(num) if num else 0)
        except ValueError:
            parts.append(0)
    # pad to 3
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def _fetch_latest() -> tuple[str, str, str]:
    """Retorna (tag, html_url, body) do release mais recente."""
    req = urllib.request.Request(API_LATEST, headers={"User-Agent": "ResourceHub/1.0", "Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        if r.status != 200:
            raise IOError(f"HTTP {r.status}")
        data = json.loads(r.read().decode("utf-8"))
        return data.get("tag_name", ""), data.get("html_url", REPO_URL), data.get("body", "")

def check_app_update_sync() -> tuple[bool, str, str, str]:
    """Síncrono: (has_update, latest_tag, url, body)."""
    try:
        tag, url, body = _fetch_latest()
        if not tag:
            return False, "", url, body
        cur = _parse_version(CURRENT_VERSION)
        latest = _parse_version(tag)
        has_update = latest > cur
        logger.info("App version check: %s -> %s (%s)", CURRENT_VERSION, tag, "update" if has_update else "ok")
        return has_update, tag, url, body
    except Exception as e:
        logger.debug("App update check failed: %s", e)
        return False, "", REPO_URL, ""

def check_app_update_async(on_result: Callable[[bool, str, str, str], None]):
    """Async: chama on_result(has_update, tag, url, body) na thread de fundo (caller deve usar after)."""
    def _run():
        has_update, tag, url, body = check_app_update_sync()
        try:
            on_result(has_update, tag, url, body)
        except Exception:
            logger.exception("on_result failed")
    t = threading.Thread(target=_run, daemon=True, name="app-update-check")
    t.start()
    return t
