"""Catalog update, validation and caching.

Workflow (AGENTS.md):
1. Request remote catalog asynchronously
2. Save payload to temp file
3. Parse + strict validate
4. On success replace cache
5. On failure discard temp and keep local

Never destroy valid local cache on network/malformed errors.
"""
from __future__ import annotations

import json
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Optional, Tuple

from app.config import (
    CATALOG_CACHE_PATH,
    CATALOG_TMP_PATH,
    REQUEST_TIMEOUT,
    get_catalog_url,
)
from app.models.catalog import Catalog, CatalogValidationError, validate_catalog, catalog_to_dict
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Callback types
OnSuccess = Callable[[Catalog, Optional[Catalog], str], None]  # new, old, changelog
OnError = Callable[[str], None]  # message
OnOffline = Callable[[Catalog], None]


def _read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_cached_catalog() -> Tuple[Optional[Catalog], Optional[str]]:
    """Load local cached catalog. Returns (Catalog|None, error_msg|None)."""
    if not CATALOG_CACHE_PATH.exists():
        logger.warning("No local catalog cache at %s", CATALOG_CACHE_PATH)
        return None, "Nenhum catálogo local encontrado."
    try:
        raw = _read_json_file(CATALOG_CACHE_PATH)
        cat = validate_catalog(raw)
        return cat, None
    except (json.JSONDecodeError, CatalogValidationError, OSError) as e:
        logger.exception("Failed to load cached catalog: %s", e)
        return None, f"Catálogo local inválido: {e}"


def _fetch_remote(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ResourceHub/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise IOError(f"HTTP {resp.status}")
        return resp.read()


def _atomic_replace(tmp: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(target)


def try_update_sync() -> Tuple[Optional[Catalog], Optional[Catalog], str, Optional[str]]:
    """Synchronous update attempt.

    Returns (new_catalog|None, old_catalog|None, status, error_msg)
    status in: "updated", "up_to_date", "failed", "no_cache"
    """
    old_catalog, _ = load_cached_catalog()

    url = get_catalog_url()
    logger.info("Fetching remote catalog: %s", url)

    # ensure data dir exists
    CATALOG_TMP_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        payload = _fetch_remote(url)
    except Exception as e:
        logger.warning("Network failure fetching catalog: %s", e)
        return None, old_catalog, "failed", f"Falha de rede: {e}"

    # Save to temp file
    try:
        CATALOG_TMP_PATH.write_bytes(payload)
    except OSError as e:
        logger.exception("Failed to write temp catalog: %s", e)
        return None, old_catalog, "failed", f"Erro ao salvar temporário: {e}"

    # Parse & validate
    try:
        raw = json.loads(payload.decode("utf-8"))
        new_catalog = validate_catalog(raw)
    except (json.JSONDecodeError, CatalogValidationError, UnicodeDecodeError) as e:
        logger.warning("Remote catalog validation failed: %s", e)
        # discard temp
        try:
            CATALOG_TMP_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return None, old_catalog, "failed", f"Catálogo remoto inválido: {e}"

    # Success: replace cache
    try:
        _atomic_replace(CATALOG_TMP_PATH, CATALOG_CACHE_PATH)
        logger.info("Catalog cache updated to version %s", new_catalog.catalog_version)
    except OSError as e:
        logger.exception("Failed to replace catalog cache: %s", e)
        return None, old_catalog, "failed", f"Erro ao atualizar cache: {e}"

    # Compare versions
    old_version = old_catalog.catalog_version if old_catalog else ""
    new_version = new_catalog.catalog_version
    if old_version and old_version == new_version:
        return new_catalog, old_catalog, "up_to_date", None
    return new_catalog, old_catalog, "updated", None


def update_async(
    on_success: Optional[OnSuccess] = None,
    on_error: Optional[OnError] = None,
    on_offline: Optional[Callable[[Optional[Catalog]], None]] = None,
) -> threading.Thread:
    """Launch async update in background thread. Returns thread."""

    def _run():
        new_cat, old_cat, status, err = try_update_sync()
        if status in ("updated", "up_to_date"):
            # if updated, notify with changelog
            if on_success and new_cat:
                try:
                    # schedule via on_success; caller may need thread-safe UI dispatch
                    on_success(new_cat, old_cat, new_cat.app.changelog if status == "updated" else "")
                except Exception:
                    logger.exception("on_success callback failed")
        else:
            # failed: fallback to cached
            cached, _ = load_cached_catalog()
            if on_error and err:
                try:
                    on_error(err)
                except Exception:
                    logger.exception("on_error callback failed")
            if on_offline:
                try:
                    on_offline(cached)
                except Exception:
                    logger.exception("on_offline callback failed")

    t = threading.Thread(target=_run, daemon=True, name="catalog-update")
    t.start()
    return t


def save_catalog_dict(raw: dict) -> Catalog:
    """Validate and save raw dict as cache (used for tests/manual)."""
    cat = validate_catalog(raw)
    CATALOG_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(catalog_to_dict(cat), f, ensure_ascii=False, indent=2)
    return cat
