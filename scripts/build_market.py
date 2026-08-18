from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from theme_package import load_and_validate_theme_package, require


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
THEMES_ROOT = REPOSITORY_ROOT / "themes"
SCHEMAS_ROOT = REPOSITORY_ROOT / "schemas"
DIST_ROOT = REPOSITORY_ROOT / "dist"


def main() -> None:
    theme_roots = sorted(path for path in THEMES_ROOT.iterdir() if path.is_dir())
    require(bool(theme_roots), "themes 目录中没有可发布主题。")
    _reset_dist()
    entries = [_build_theme(theme_root) for theme_root in theme_roots]
    shutil.copytree(SCHEMAS_ROOT, DIST_ROOT / "schemas", dirs_exist_ok=True)
    _write_json(
        DIST_ROOT / "index.json",
        {
            "schemaVersion": 1,
            "kind": "tiance-theme-market",
            "name": "Tiance Themes",
            "updatedAt": datetime.now(UTC).isoformat(),
            "themes": entries,
        },
    )
    print(f"市场构建完成：{len(entries)} 个主题。")


def _build_theme(theme_root: Path) -> dict[str, object]:
    theme, manifest = load_and_validate_theme_package(theme_root)
    theme_id = theme_root.name
    version = str(manifest["version"])
    preview_source = theme_root / str(manifest["preview"])
    preview_name = f"{theme_id}{preview_source.suffix.lower()}"
    preview_target = DIST_ROOT / "previews" / preview_name
    preview_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(preview_source, preview_target)

    package_name = f"{theme_id}-{version}.zip"
    package_target = DIST_ROOT / "packages" / package_name
    package_target.parent.mkdir(parents=True, exist_ok=True)
    _write_package(theme_root, package_target)

    return {
        "id": theme_id,
        "name": str(theme["registrationName"]),
        "mode": str(theme["mode"]),
        "version": version,
        "author": str(manifest["author"]["name"]),
        "summary": str(manifest["summary"]),
        "license": str(manifest["license"]),
        "baseColors": manifest["baseColors"],
        "previewUrl": f"previews/{preview_name}",
        "packageUrl": f"packages/{package_name}",
        "sha256": _sha256(package_target),
        "size": package_target.stat().st_size,
        "compatibility": manifest["compatibility"],
    }


def _write_package(theme_root: Path, target: Path) -> None:
    with ZipFile(target, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in theme_root.rglob("*") if item.is_file()):
            relative = path.relative_to(theme_root)
            archive.write(
                path,
                (PurePosixPath(theme_root.name) / PurePosixPath(relative.as_posix())).as_posix(),
            )


def _reset_dist() -> None:
    resolved = DIST_ROOT.resolve()
    require(resolved.parent == REPOSITORY_ROOT.resolve(), "dist 目录越界。")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
