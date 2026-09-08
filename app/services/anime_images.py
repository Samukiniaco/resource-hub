"""API reversa própria — anime SFW sem key, para banners.

Fontes (nesta ordem):
1. NekosAPI v4 (rating=safe, retorna url + color_dominant)
2. Safebooru (json=1, rating general, retorna file_url/sample_url)

Google Imagens não tem API — cole manual no carrossel.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from urllib.parse import quote
from typing import List, Dict, Any

from app.config import REQUEST_TIMEOUT
from app.utils.logger import get_logger

logger = get_logger(__name__)

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

# query do tema -> tags de cada fonte
QUERY_TAGS = {
    "kobayashi": ["maid"],
    "maid": ["maid"],
    "nichijou": ["school_uniform"],
    "azumanga": ["school_uniform"],
    "school": ["school_uniform"],
    "uniform": ["school_uniform"],
    "k-on": ["school_uniform"],
    "kon": ["school_uniform"],
    "bocchi": ["school_uniform"],
    "music": ["school_uniform"],
    "minecraft": [],
    "game": [],
}

def _rgb_to_hex(rgb) -> str | None:
    try:
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None

def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        if r.status != 200:
            raise IOError(f"HTTP {r.status}")
        return json.loads(r.read().decode("utf-8"))

def _tags_for(query: str) -> List[str]:
    q = (query or "").lower()
    for key, tags in QUERY_TAGS.items():
        if key in q:
            return tags
    return []

def _nekosapi(tags: List[str], count: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    # tenta com tags, depois sem tags
    tag_param = ""
    if tags:
        # nekosapi usa tags separadas por vírgula? testa primeira tag
        tag_param = f"&tags={quote(tags[0])}"
    for url in (
        f"https://api.nekosapi.com/v4/images/random?rating=safe&limit={count}{tag_param}",
        f"https://api.nekosapi.com/v4/images/random?rating=safe&limit={count}",
    ):
        try:
            data = _get_json(url)
            if not isinstance(data, list):
                continue
            for im in data:
                u = im.get("url", "")
                if not u or not u.startswith("http"):
                    continue
                if im.get("rating", "safe") != "safe":
                    continue
                out.append({
                    "url": u,
                    "dominant": _rgb_to_hex(im.get("color_dominant")) or "",
                    "width": 0,
                    "height": 0,
                    "source": "nekosapi",
                })
                if len(out) >= count:
                    return out[:count]
            if out:
                return out[:count]
        except Exception as e:
            logger.debug("nekosapi failed %s: %s", url[:80], e)
            continue
    return out

def _safebooru(tags: List[str], count: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    tag_str = "+".join([quote(t) for t in tags]) if tags else "1girl"
    # pede mais para filtrar landscape depois
    url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit={max(count*3, 10)}&tags={tag_str}"
    try:
        data = _get_json(url)
        if not isinstance(data, list):
            return out
        for p in data:
            # prefere sample (menor) para banner 620x170
            file_url = p.get("sample_url") or p.get("file_url") or ""
            if not file_url.startswith("http"):
                continue
            if p.get("rating", "s") not in ("s", "general", "safe"):
                # safebooru rating: s=safe
                if p.get("rating") not in ("s",):
                    continue
            w = int(p.get("width") or 0)
            h = int(p.get("height") or 0)
            # prefere landscape para banner
            if w and h and w < h:
                continue
            out.append({
                "url": file_url,
                "dominant": "",
                "width": w,
                "height": h,
                "source": "safebooru",
            })
            if len(out) >= count:
                break
    except Exception as e:
        logger.debug("safebooru failed: %s", e)
    return out[:count]

def search_anime(query: str, count: int = 6) -> List[Dict[str, Any]]:
    """Busca anime SFW landscape. Sempre retorna lista (pode ser vazia, sem stock)."""
    tags = _tags_for(query)
    out: List[Dict[str, Any]] = []
    # 1. nekosapi (já filtra safe + tem dominant color)
    try:
        out.extend(_nekosapi(tags, count))
    except Exception as e:
        logger.debug("nekosapi search failed: %s", e)
    # 2. completa com safebooru
    if len(out) < count:
        try:
            out.extend(_safebooru(tags, count - len(out)))
        except Exception as e:
            logger.debug("safebooru search failed: %s", e)
    # dedupe por url
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for im in out:
        if im["url"] not in seen:
            seen.add(im["url"])
            uniq.append(im)
    return uniq[:count]
