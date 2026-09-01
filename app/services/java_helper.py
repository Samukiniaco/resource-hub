"""JavaPath helper for vortex_launcher.conf.

Spec:
- prompt user to select Java install dir
- recursively search for java.exe
- single -> auto select, multiple -> selection dialog
- locate vortex_launcher.conf relative to execution root
- update only JavaPath = ... preserve other lines
- abort if no java.exe or conf missing
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import VORTEX_CONF_NAME, PROJECT_ROOT
from app.utils.logger import get_logger

logger = get_logger(__name__)


def find_java_exes(search_root: Path) -> List[Path]:
    """Recursively search for java.exe under search_root."""
    result: List[Path] = []
    if not search_root.exists() or not search_root.is_dir():
        return result
    # use rglob, handle permission errors gracefully
    try:
        for p in search_root.rglob("java.exe"):
            if p.is_file():
                result.append(p.resolve())
    except Exception as e:
        logger.warning("Search failed in %s: %s", search_root, e)
        # fallback walk
        for dirpath, _dirnames, filenames in os.walk(search_root, onerror=lambda e: None):
            if "java.exe" in filenames:
                candidate = Path(dirpath) / "java.exe"
                try:
                    if candidate.is_file():
                        result.append(candidate.resolve())
                except OSError:
                    continue
    # dedupe
    seen = set()
    uniq: List[Path] = []
    for p in result:
        s = str(p).lower()
        if s not in seen:
            seen.add(s)
            uniq.append(p)
    return sorted(uniq)


def locate_vortex_conf(execution_root: Optional[Path] = None) -> Optional[Path]:
    """Locate vortex_launcher.conf relative to execution root.

    Search order:
    1) execution_root / vortex_launcher.conf
    2) cwd / vortex_launcher.conf
    3) PROJECT_ROOT / vortex_launcher.conf
    4) parent dirs up to 3 levels from execution_root
    """
    candidates: List[Path] = []
    if execution_root:
        candidates.append(execution_root / VORTEX_CONF_NAME)
        # parents
        cur = execution_root
        for _ in range(3):
            cur = cur.parent
            candidates.append(cur / VORTEX_CONF_NAME)
    candidates.append(Path.cwd() / VORTEX_CONF_NAME)
    candidates.append(PROJECT_ROOT / VORTEX_CONF_NAME)
    candidates.append(PROJECT_ROOT.parent / VORTEX_CONF_NAME)

    for c in candidates:
        if c.is_file():
            logger.info("Found vortex_launcher.conf at %s", c)
            return c.resolve()
    logger.warning("vortex_launcher.conf not found in candidates: %s", candidates)
    return None


def update_java_path(conf_path: Path, new_java_path: Path) -> Tuple[bool, str]:
    """Update only JavaPath entry, preserve all other lines.

    Returns (success, message).
    """
    if not conf_path.exists() or not conf_path.is_file():
        return False, f"Arquivo não encontrado: {conf_path}"
    if not new_java_path.exists():
        return False, f"java.exe não encontrado: {new_java_path}"

    try:
        content = conf_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # try fallback encodings
        try:
            content = conf_path.read_text(encoding="latin-1")
        except Exception as e:
            logger.exception("Failed to read conf: %s", e)
            return False, f"Erro ao ler {conf_path}: {e}"
    except OSError as e:
        return False, f"Erro ao ler {conf_path}: {e}"

    lines = content.splitlines()
    found = False
    new_lines: List[str] = []
    new_value = str(new_java_path)
    for line in lines:
        stripped = line.strip()
        # detect JavaPath key ignoring case and spaces around =
        if stripped.lower().startswith("javapath"):
            # check if it looks like key = value
            if "=" in line:
                # preserve? spec says target and update only that entry
                # we write canonical: JavaPath = <path>
                # keep minimal formatting
                new_lines.append(f"JavaPath = {new_value}")
                found = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not found:
        return False, "Entrada 'JavaPath =' não encontrada no arquivo. Nenhuma alteração feita."

    # write back preserving newline style
    # detect original newline?
    try:
        # Use \n, file will be normalized; preserve original if needed
        conf_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        logger.info("Updated JavaPath to %s in %s", new_value, conf_path)
        return True, f"JavaPath atualizado para:\n{new_value}"
    except OSError as e:
        logger.exception("Failed to write conf: %s", e)
        return False, f"Erro ao escrever {conf_path}: {e}"


def validate_java_path(java_path: Path) -> bool:
    return java_path.is_file() and java_path.name.lower() == "java.exe"
