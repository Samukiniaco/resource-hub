"""Carrossel de banners — até 15 imagens, random sem repetir seguidas.

Sem picsum stock: padrão é vazio (banner procedural temático).
Busca usa waifu.im (anime, LANDSCAPE, SFW, sem key) com fallback.
Google Imagens não tem API — cole o 'copiar endereço da imagem' manualmente.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List
import urllib.request
import urllib.error
from urllib.parse import quote

from app.config import DATA_DIR, REQUEST_TIMEOUT
from app.utils.logger import get_logger

logger = get_logger(__name__)

CAROUSEL_PATH = DATA_DIR / "banner_carousel.json"
MAX_IMAGES = 15

# Padrão vazio — sem foto bizarra. Procedural cobre.
DEFAULT_CAROUSEL: List[str] = []

_last_pick: str | None = None

THEME_TAGS = {
    "kobayashi": ["maid", "uniform"],
    "kobayashi_dark": ["maid", "uniform"],
    "nichijou": ["uniform", "school"],
    "nichijou_dark": ["uniform", "school"],
    "azumanga": ["uniform", "school"],
    "azumanga_dark": ["uniform", "school"],
    "k_on": ["uniform"],
    "k_on_dark": ["uniform"],
    "bocchi": ["uniform"],
    "bocchi_dark": ["uniform"],
    "minecraft": ["waifu"],
    "minecraft_light": ["waifu"],
    "dark": ["waifu"],
    "light": ["waifu"],
}

def load_carousel() -> List[str]:
    if CAROUSEL_PATH.exists():
        try:
            data = json.loads(CAROUSEL_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                lst = [str(u).strip() for u in data if isinstance(u, str) and u.strip().startswith("http")][:MAX_IMAGES]
                return lst
        except Exception as e:
            logger.debug("carousel load failed: %s", e)
    return list(DEFAULT_CAROUSEL)

def save_carousel(urls: List[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean = [u.strip() for u in urls if isinstance(u, str) and u.strip().startswith("http")][:MAX_IMAGES]
    CAROUSEL_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    global _last_pick
    _last_pick = None

def get_next_banner_url() -> str | None:
    lst = load_carousel()
    if not lst:
        return None
    if len(lst) == 1:
        return lst[0]
    global _last_pick
    choices = [u for u in lst if u != _last_pick]
    pick = random.choice(choices) if choices else random.choice(lst)
    _last_pick = pick
    return pick

def _waifu_search(tags: List[str], count: int) -> List[str]:
    """waifu.im — tenta browser UA (Cloudflare bloqueia python UA)."""
    out: List[str] = []
    tag_q = "&".join([f"included_tags={quote(t)}" for t in tags[:2]]) if tags else "included_tags=waifu"
    # many=true retorna várias de uma vez
    urls_to_try = [
        f"https://api.waifu.im/search/?{tag_q}&is_nsfw=false&orientation=LANDSCAPE&many=true",
        f"https://api.waifu.im/search?{tag_q}",
    ]
    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                if r.status != 200:
                    continue
                data = json.loads(r.read().decode("utf-8"))
                imgs = data.get("images", [])
                for im in imgs[:count]:
                    u = im.get("url", "")
                    if u and u.startswith("http"):
                        out.append(u)
                if out:
                    return out[:count]
        except Exception as e:
            logger.debug("waifu.im failed %s: %s", url, e)
            continue
    return out

def search_image_urls(query: str, count: int = 6) -> List[str]:
    """Busca anime: waifu.im por tags do tema; fallback vazio (sem stock)."""
    q = (query or "").strip().lower() or "anime"
    # mapeia query para tags waifu.im
    tags: List[str] = ["waifu"]
    for key, t in THEME_TAGS.items():
        if key in q.replace(" ", "_") or any(w in q for w in t):
            tags = t
            break
    # palavras-chave simples
    if "maid" in q or "kobayashi" in q:
        tags = ["maid", "uniform"]
    elif "school" in q or "nichijou" in q or "azumanga" in q or "k-on" in q or "kon" in q or "bocchi" in q:
        tags = ["uniform"]
    elif "minecraft" in q:
        tags = ["waifu"]

    urls = _waifu_search(tags, count)
    # sem fallback picsum — retorna o que achou (pode ser vazio, UI mostra aviso)
    return urls[:count]

def add_to_carousel(url: str) -> bool:
    lst = load_carousel()
    if url in lst:
        return False
    if len(lst) >= MAX_IMAGES:
        return False
    lst.append(url)
    save_carousel(lst)
    return True

def remove_from_carousel(url: str) -> None:
    lst = load_carousel()
    if url in lst:
        lst.remove(url)
        save_carousel(lst)
