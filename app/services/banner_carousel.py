"""Carrossel de banners — até 15 imagens, random sem repetir seguidas, busca por tema."""
from __future__ import annotations

import json
import random
import hashlib
from pathlib import Path
from typing import List
from urllib.parse import quote

from app.config import DATA_DIR
from app.utils.logger import get_logger

logger = get_logger(__name__)

CAROUSEL_PATH = DATA_DIR / "banner_carousel.json"
MAX_IMAGES = 15

# Imagens padrão (anime light) — picsum com seed + waifu fallback, sem API key
DEFAULT_CAROUSEL = [
    "https://picsum.photos/seed/kobayashi/620/170",
    "https://picsum.photos/seed/nichijou/620/170",
    "https://picsum.photos/seed/azumanga/620/170",
    "https://picsum.photos/seed/kon/620/170",
    "https://picsum.photos/seed/bocchi/620/170",
]

_last_pick: str | None = None

def load_carousel() -> List[str]:
    if CAROUSEL_PATH.exists():
        try:
            data = json.loads(CAROUSEL_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # filtra só strings https e max 15
                lst = [str(u).strip() for u in data if isinstance(u, str) and u.strip().startswith("http")][:MAX_IMAGES]
                if lst:
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
    # escolhe random sem repetir o último
    choices = [u for u in lst if u != _last_pick]
    pick = random.choice(choices) if choices else random.choice(lst)
    _last_pick = pick
    return pick

def search_image_urls(query: str, count: int = 6) -> List[str]:
    """Gera URLs buscáveis — compatível com anime via Unsplash Source + picsum."""
    q = (query or "").strip()
    if not q:
        q = "anime"
    # limpa para URL
    safe = quote(q)
    # Unsplash Source (sem key, redirect) + picsum seed
    # Para anime, waifu picsum é genérico mas funciona; Unsplash dá fotos reais
    urls = []
    # 3 via picsum com seed por query (determinístico + cacheável)
    base_hash = hashlib.sha256(q.encode("utf-8")).hexdigest()[:6]
    for i in range(min(3, count)):
        urls.append(f"https://picsum.photos/seed/{base_hash}{i}/620/170")
    # 3 via unsplash source com query (anime, minecraft, etc)
    for i in range(min(3, count - len(urls))):
        # unsplash source retorna redirect 302 para imagem real — image_service segue redirect
        urls.append(f"https://source.unsplash.com/620x170/?{safe}&sig={i}")
    # se ainda faltar, completa com picsum random
    while len(urls) < count:
        urls.append(f"https://picsum.photos/620/170?random={random.randint(1,9999)}")
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
