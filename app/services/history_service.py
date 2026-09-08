"""Histórico de changelogs via GitHub commits + raw SHA."""
from __future__ import annotations

import json
import threading
import urllib.request
import urllib.error
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable
from pathlib import Path

from app.config import HISTORY_CACHE_PATH, GITHUB_API_URL, REQUEST_TIMEOUT
from app.models.catalog import validate_catalog, Catalog
from app.utils.logger import get_logger

logger = get_logger(__name__)

RAW_URL = "https://raw.githubusercontent.com/Samukiniaco/resource-hub/{sha}/data/catalog.json"
CDN_URL = "https://cdn.jsdelivr.net/gh/Samukiniaco/resource-hub@{sha}/data/catalog.json"
COMMITS_URL = GITHUB_API_URL + "?path=data/catalog.json&per_page=40"

@dataclass
class HistoryEntry:
    sha: str
    short_sha: str
    catalog_version: str
    changelog: str
    date: str
    message: str
    raw_url: str
    catalog: Optional[Catalog] = None
    author: str = ""

def _fetch_json(url: str, timeout=REQUEST_TIMEOUT) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "ResourceHub/1.0", "Accept": "application/vnd.github.v3+json"})
    # opcional PAT para rate limit
    import os
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise IOError(f"HTTP {r.status}")
        return json.loads(r.read().decode("utf-8"))

def _fetch_catalog_at_sha(sha: str) -> Optional[Catalog]:
    for url in (RAW_URL.format(sha=sha), CDN_URL.format(sha=sha)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ResourceHub/1.0"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                if r.status != 200:
                    continue
                raw = json.loads(r.read().decode("utf-8"))
                return validate_catalog(raw)
        except Exception as e:
            logger.debug("fetch at %s failed: %s", sha[:7], e)
            continue
    return None

def fetch_history_sync(limit: int = 20) -> List[HistoryEntry]:
    # 1. busca commits
    try:
        commits = _fetch_json(COMMITS_URL)
    except Exception as e:
        logger.warning("GitHub API failed: %s", e)
        # tenta cache
        cached = load_history_cache()
        if cached:
            return cached[:limit]
        raise

    entries: List[HistoryEntry] = []
    for c in commits[:limit]:
        sha = c.get("sha", "")
        short = sha[:7]
        commit = c.get("commit", {})
        msg = commit.get("message", "").split("\n")[0][:120]
        date = commit.get("committer", {}).get("date", "") or commit.get("author", {}).get("date", "")
        author = commit.get("author", {}).get("name", "") or c.get("author", {}).get("login", "")
        # busca catalog nesse sha
        cat = _fetch_catalog_at_sha(sha)
        if not cat:
            # tenta pegar changelog do commit message se falhar
            continue
        entries.append(HistoryEntry(
            sha=sha,
            short_sha=short,
            catalog_version=cat.catalog_version,
            changelog=cat.app.changelog or msg,
            date=date[:10] if date else "",
            message=msg,
            raw_url=RAW_URL.format(sha=sha),
            catalog=cat,
            author=author,
        ))
    # cache
    try:
        save_history_cache(entries)
    except Exception:
        pass
    return entries

def load_history_cache() -> List[HistoryEntry]:
    if not HISTORY_CACHE_PATH.exists():
        return []
    try:
        raw = json.loads(HISTORY_CACHE_PATH.read_text(encoding="utf-8"))
        out = []
        for d in raw:
            # catalog não serializado completo, só metadados
            out.append(HistoryEntry(
                sha=d.get("sha",""),
                short_sha=d.get("short_sha","") or d.get("sha","")[:7],
                catalog_version=d.get("catalog_version",""),
                changelog=d.get("changelog",""),
                date=d.get("date",""),
                message=d.get("message",""),
                raw_url=d.get("raw_url",""),
                catalog=None,
                author=d.get("author",""),
            ))
        return out
    except Exception as e:
        logger.debug("history cache load failed: %s", e)
        return []

def save_history_cache(entries: List[HistoryEntry]) -> None:
    HISTORY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "sha": e.sha,
            "short_sha": e.short_sha,
            "catalog_version": e.catalog_version,
            "changelog": e.changelog,
            "date": e.date,
            "message": e.message,
            "raw_url": e.raw_url,
            "author": e.author,
        } for e in entries
    ]
    HISTORY_CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def fetch_history_async(on_success: Callable[[List[HistoryEntry]], None], on_error: Callable[[str], None], limit: int = 20):
    def _run():
        try:
            entries = fetch_history_sync(limit=limit)
            on_success(entries)
        except Exception as e:
            logger.warning("history async failed: %s", e)
            # tenta cache mesmo com erro
            cached = load_history_cache()
            if cached:
                on_success(cached)
            else:
                on_error(str(e))
    t = threading.Thread(target=_run, daemon=True, name="history-fetch")
    t.start()
    return t
