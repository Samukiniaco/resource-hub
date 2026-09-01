"""Catalog data models and strict validation.

Treats all incoming remote data as untrusted input.
Never hard-codes resource entries; all validated and sanitized here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.config import SCHEMA_VERSION

URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class CatalogValidationError(ValueError):
    pass


def _is_valid_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _str(v: Any, default: str = "") -> str:
    if isinstance(v, str):
        return v.strip()
    if v is None:
        return default
    return str(v).strip()


@dataclass
class AppMeta:
    catalog_version: str = "0.0.0"
    changelog: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "AppMeta":
        if not isinstance(data, dict):
            return cls()
        return cls(
            catalog_version=_str(data.get("catalog_version", "0.0.0")) or "0.0.0",
            changelog=_str(data.get("changelog", "")),
        )


@dataclass
class MinecraftVersion:
    id: str
    name: str
    description: str = ""
    banner: str = ""
    link: str = ""
    warning: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "MinecraftVersion":
        if not isinstance(data, dict):
            raise CatalogValidationError("Minecraft version must be an object")
        vid = _str(data.get("id"))
        name = _str(data.get("name"))
        link = _str(data.get("link"))
        if not vid:
            raise CatalogValidationError("Minecraft version missing 'id'")
        if not name:
            raise CatalogValidationError(f"Minecraft version {vid!r} missing 'name'")
        if link and not _is_valid_url(link):
            raise CatalogValidationError(f"Minecraft version {vid!r} has invalid link")
        banner = _str(data.get("banner", ""))
        if banner and not _is_valid_url(banner):
            # treat invalid banner as empty (graceful) rather than fail
            banner = ""
        return cls(
            id=vid,
            name=name,
            description=_str(data.get("description", "")),
            banner=banner,
            link=link,
            warning=_str(data.get("warning", "")),
        )


@dataclass
class JavaResource:
    version: str
    name: str
    description: str = ""
    link: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "JavaResource":
        if not isinstance(data, dict):
            raise CatalogValidationError("Java entry must be an object")
        version = _str(data.get("version"))
        name = _str(data.get("name"))
        link = _str(data.get("link"))
        if not version:
            raise CatalogValidationError("Java entry missing 'version'")
        if not name:
            raise CatalogValidationError(f"Java {version!r} missing 'name'")
        if link and not _is_valid_url(link):
            raise CatalogValidationError(f"Java {version!r} has invalid link")
        return cls(
            version=version,
            name=name,
            description=_str(data.get("description", "")),
            link=link,
        )


@dataclass
class OtherResource:
    name: str
    description: str = ""
    category: str = "other"
    link: str = ""
    banner: str = ""
    warning: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "OtherResource":
        if not isinstance(data, dict):
            raise CatalogValidationError("Other resource must be an object")
        name = _str(data.get("name"))
        if not name:
            raise CatalogValidationError("Other resource missing 'name'")
        link = _str(data.get("link", ""))
        if link and not _is_valid_url(link):
            raise CatalogValidationError(f"Other resource {name!r} has invalid link")
        banner = _str(data.get("banner", ""))
        if banner and not _is_valid_url(banner):
            banner = ""
        return cls(
            name=name,
            description=_str(data.get("description", "")),
            category=_str(data.get("category", "other")) or "other",
            link=link,
            banner=banner,
            warning=_str(data.get("warning", "")),
        )


@dataclass
class Catalog:
    schema_version: int
    app: AppMeta = field(default_factory=AppMeta)
    minecraft_versions: List[MinecraftVersion] = field(default_factory=list)
    libraries: Dict[str, Any] = field(default_factory=dict)
    java: List[JavaResource] = field(default_factory=list)
    launcher: Dict[str, Any] = field(default_factory=dict)
    other: List[OtherResource] = field(default_factory=list)

    @property
    def catalog_version(self) -> str:
        return self.app.catalog_version


def _validate_libraries(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise CatalogValidationError("'libraries' must be an object")
    # sanitize: allow any keys but validate URLs if present
    result: Dict[str, Any] = {}
    for k, v in data.items():
        key = _str(k)
        if not key:
            continue
        if isinstance(v, str) and v.strip() and k.lower() in ("link", "url", "banner"):
            if not _is_valid_url(v):
                raise CatalogValidationError(f"libraries.{k} has invalid URL")
            result[key] = v.strip()
        else:
            result[key] = v
    # If libraries has a link/url field, validate
    for url_key in ("link", "url"):
        if url_key in result and isinstance(result[url_key], str) and result[url_key]:
            if not _is_valid_url(result[url_key]):
                raise CatalogValidationError("libraries link is invalid")
    return result


def _validate_launcher(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise CatalogValidationError("'launcher' must be an object")
    result: Dict[str, Any] = {}
    for k, v in data.items():
        result[_str(k) or k] = v
    # validate link if present
    if "link" in result and isinstance(result["link"], str) and result["link"].strip():
        if not _is_valid_url(result["link"]):
            raise CatalogValidationError("launcher.link is invalid")
    return result


def validate_catalog(raw: Any) -> Catalog:
    """Strictly validate raw dict and return Catalog.

    Raises CatalogValidationError on any schema mismatch.
    """
    if not isinstance(raw, dict):
        raise CatalogValidationError("Catalog must be a JSON object")
    sv = raw.get("schema_version")
    if sv != SCHEMA_VERSION:
        raise CatalogValidationError(
            f"Unsupported schema_version {sv!r}, expected {SCHEMA_VERSION}"
        )
    app = AppMeta.from_dict(raw.get("app", {}))

    # minecraft: { versions: [] }
    minecraft_raw = raw.get("minecraft", {})
    if not isinstance(minecraft_raw, dict):
        raise CatalogValidationError("'minecraft' must be an object")
    versions_raw = minecraft_raw.get("versions", [])
    if not isinstance(versions_raw, list):
        raise CatalogValidationError("'minecraft.versions' must be an array")
    mc_versions: List[MinecraftVersion] = []
    for item in versions_raw:
        mc_versions.append(MinecraftVersion.from_dict(item))

    # libraries
    libraries = _validate_libraries(raw.get("libraries", {}))

    # java
    java_raw = raw.get("java", [])
    if not isinstance(java_raw, list):
        raise CatalogValidationError("'java' must be an array")
    java_list: List[JavaResource] = []
    for item in java_raw:
        java_list.append(JavaResource.from_dict(item))

    # launcher
    launcher = _validate_launcher(raw.get("launcher", {}))

    # other
    other_raw = raw.get("other", [])
    if not isinstance(other_raw, list):
        raise CatalogValidationError("'other' must be an array")
    other_list: List[OtherResource] = []
    for item in other_raw:
        other_list.append(OtherResource.from_dict(item))

    return Catalog(
        schema_version=SCHEMA_VERSION,
        app=app,
        minecraft_versions=mc_versions,
        libraries=libraries,
        java=java_list,
        launcher=launcher,
        other=other_list,
    )


def catalog_to_dict(catalog: Catalog) -> Dict[str, Any]:
    """Serialize catalog back to dict (for caching)."""
    return {
        "schema_version": catalog.schema_version,
        "app": {
            "catalog_version": catalog.app.catalog_version,
            "changelog": catalog.app.changelog,
        },
        "minecraft": {
            "versions": [
                {
                    "id": v.id,
                    "name": v.name,
                    "description": v.description,
                    "banner": v.banner,
                    "link": v.link,
                    "warning": v.warning,
                }
                for v in catalog.minecraft_versions
            ]
        },
        "libraries": catalog.libraries,
        "java": [
            {"version": j.version, "name": j.name, "description": j.description, "link": j.link}
            for j in catalog.java
        ],
        "launcher": catalog.launcher,
        "other": [
            {
                "name": o.name,
                "description": o.description,
                "category": o.category,
                "link": o.link,
                "banner": o.banner,
                "warning": o.warning,
            }
            for o in catalog.other
        ],
    }
