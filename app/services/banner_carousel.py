"""Carrossel de banners — até 15 imagens, random sem repetir seguidas.

Padrão vazio (procedural temático, sem foto bizarra).
Busca usa API reversa própria (NekosAPI safe + Safebooru) — anime de verdade.
Google Imagens não tem API — cole o 'copiar endereço da imagem' manualmente.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List

from app.config import DATA_DIR
from app.utils.logger import get_logger

logger = get_logger(__name__)

CAROUSEL_PATH = DATA_DIR / "banner_carousel.json"
MAX_IMAGES = 15

DEFAULT_CAROUSEL: List[str] = []

_last_pick: str | None = None

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

def search_image_urls(query: str, count: int = 6) -> List[str]:
    """Compat: retorna só URLs (theme_editor antigo). Usa API anime real."""
    try:
        from app.services.anime_images import search_anime
        results = search_anime(query, count=count)
        return [r["url"] for r in results][:count]
    except Exception as e:
        logger.debug("search failed: %s", e)
        return []

def search_image_detailed(query: str, count: int = 6):
    """Nova: retorna [{url, dominant, source}] para mostrar cor no editor."""
    try:
        from app.services.anime_images import search_anime
        return search_anime(query, count=count)
    except Exception:
        return []

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
