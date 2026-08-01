from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


THEME_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
)
PACKAGE_FILES = {"manifest.json", "theme.json"}
FORBIDDEN_NAMES = {".Tiance", "catalog.json", "theme-settings.json"}
ALLOWED_ASSET_SUFFIXES = {".avif", ".jpeg", ".jpg", ".png", ".webp"}


class MarketBuildError(RuntimeError):
    pass


def load_and_validate_theme_package(
    theme_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    theme_id = theme_root.name
    require(THEME_ID_PATTERN.fullmatch(theme_id) is not None, f"非法主题目录名：{theme_id}")
    _validate_package_tree(theme_root)
    theme = _read_object(theme_root / "theme.json")
    manifest = _read_object(theme_root / "manifest.json")
    _validate_theme(theme_id, theme, theme_root)
    _validate_manifest(theme_id, manifest, theme_root)
    return theme, manifest


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MarketBuildError(message)


def _validate_package_tree(theme_root: Path) -> None:
    top_level_names = {path.name for path in theme_root.iterdir()}
    missing = PACKAGE_FILES - top_level_names
    require(not missing, f"{theme_root.name} 缺少文件：{', '.join(sorted(missing))}")
    require(not (top_level_names & FORBIDDEN_NAMES), f"{theme_root.name} 包含本地状态文件。")

    for path in theme_root.rglob("*"):
        require(not path.is_symlink(), f"{theme_root.name} 不允许符号链接：{path.name}")
        require(path.name not in FORBIDDEN_NAMES, f"{theme_root.name} 包含禁止文件：{path.name}")
        if path.is_file() and "assets" in path.relative_to(theme_root).parts:
            require(
                path.suffix.lower() in ALLOWED_ASSET_SUFFIXES,
                f"{theme_root.name} 包含不支持的资源：{path.name}",
            )


def _validate_theme(theme_id: str, theme: dict[str, Any], theme_root: Path) -> None:
    require(theme.get("schemaVersion") == 2, f"{theme_id} 只支持 theme schemaVersion 2。")
    require(theme.get("id") == theme_id, f"{theme_id} 的 theme.json.id 与目录名不一致。")
    require(isinstance(theme.get("name"), str) and theme["name"].strip(), f"{theme_id} 缺少名称。")
    require(theme.get("mode") in {"dark", "light"}, f"{theme_id} 的 mode 非法。")

    tokens = theme.get("tokens")
    require(isinstance(tokens, dict), f"{theme_id} 缺少 tokens。")
    background = tokens.get("background") or {}
    require(isinstance(background, dict), f"{theme_id} 的 background 非法。")
    image = str(background.get("image") or "").strip()
    if image:
        require(_is_safe_relative_path(image), f"{theme_id} 的背景路径非法。")
        require(image.startswith("assets/"), f"{theme_id} 的背景必须位于 assets/。")
        require((theme_root / image).is_file(), f"{theme_id} 的背景文件不存在：{image}")


def _validate_manifest(theme_id: str, manifest: dict[str, Any], theme_root: Path) -> None:
    expected_keys = {
        "schemaVersion", "version", "author", "summary", "license", "preview", "compatibility"
    }
    require(set(manifest) == expected_keys, f"{theme_id} 的 manifest 字段不完整或存在多余字段。")
    require(manifest["schemaVersion"] == 1, f"{theme_id} 只支持 manifest schemaVersion 1。")
    require(SEMVER_PATTERN.fullmatch(str(manifest["version"])) is not None, f"{theme_id} 的版本号非法。")
    author = manifest["author"]
    require(isinstance(author, dict) and set(author) == {"name"}, f"{theme_id} 的 author 非法。")
    require(isinstance(author["name"], str) and author["name"].strip(), f"{theme_id} 缺少作者。")
    require(isinstance(manifest["summary"], str) and manifest["summary"].strip(), f"{theme_id} 缺少简介。")
    require(isinstance(manifest["license"], str) and manifest["license"].strip(), f"{theme_id} 缺少许可证。")

    preview = str(manifest["preview"])
    require(_is_safe_relative_path(preview), f"{theme_id} 的预览图路径非法。")
    require((theme_root / preview).is_file(), f"{theme_id} 的预览图不存在。")
    compatibility = manifest["compatibility"]
    require(
        isinstance(compatibility, dict)
        and set(compatibility) == {"themeSchemaVersion", "minTianceVersion"},
        f"{theme_id} 的兼容信息非法。",
    )
    require(compatibility["themeSchemaVersion"] == 2, f"{theme_id} 的主题合同版本非法。")
    require(
        SEMVER_PATTERN.fullmatch(str(compatibility["minTianceVersion"])) is not None,
        f"{theme_id} 的最低天策版本非法。",
    )


def _read_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MarketBuildError(f"无法读取 JSON：{path}") from exc
    require(isinstance(payload, dict), f"JSON 顶层必须是对象：{path}")
    return payload


def _is_safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return bool(value) and not path.is_absolute() and ".." not in path.parts
