from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from .core import request_json, safe_download, write_json


def import_modrinth_pack(archive: Path, root: Path, name: str, report=lambda _: None) -> Path:
    """Install a Modrinth .mrpack into an isolated instance directory."""
    base = root / "instances" / name
    base.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        try:
            manifest = json.loads(zf.read("modrinth.index.json"))
        except (KeyError, json.JSONDecodeError) as exc:
            raise ValueError("Das Archiv enthält kein gültiges Modrinth-Modpack.") from exc
        if manifest.get("formatVersion") != 1:
            raise ValueError("Nicht unterstützte Modrinth-Modpack-Version.")
        for info in zf.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in info.filename or ":" in info.filename or "\x00" in info.filename:
                raise ValueError("Unsicherer Pfad im Modpack-Archiv.")
            if p.parts and p.parts[0] == "overrides":
                dest = base.joinpath(*p.parts[1:])
                if info.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, dest.open("wb") as out:
                        shutil.copyfileobj(src, out)
    files = manifest.get("files", [])
    for i, item in enumerate(files, 1):
        path = PurePosixPath(item.get("path", ""))
        if path.is_absolute() or ".." in path.parts or "\\" in item.get("path", "") or ":" in item.get("path", ""):
            raise ValueError("Ungültiger Datei-Pfad im Modpack-Manifest.")
        dest = base.joinpath(*path.parts)
        env = item.get("env", {})
        if env.get("client") == "unsupported":
            continue
        if item.get("downloads"):
            url = item["downloads"][0]
        elif item.get("fileSize", 0) == 0:
            continue
        else:
            raise ValueError(f"Kein zulässiger Downloadlink für {path}.")
        hashes = item.get("hashes", {})
        safe_download(url, dest, hashes.get("sha1"))
        if i % 10 == 0 or i == len(files):
            report(f"Modpack-Dateien: {i}/{len(files)}")
    # Keep the runtime metadata with the installation so the launcher can identify it.
    write_json(base / "modrinth.index.json", manifest)
    return base


def export_modrinth_pack(instance: Path, dest: Path, name: str, version: str) -> None:
    mods = instance / "mods"
    files = []
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in instance.rglob("*"):
            if not path.is_file() or "natives" in path.parts:
                continue
            rel = path.relative_to(instance).as_posix()
            if rel.startswith("mods/"):
                files.append({"path": rel, "hashes": {}, "env": {"client": "required", "server": "required"},
                              "downloads": [], "fileSize": path.stat().st_size})
            elif rel != "modrinth.index.json":
                zf.write(path, "overrides/" + rel)
        manifest = {"formatVersion": 1, "game": "minecraft", "versionId": version,
                    "name": name, "summary": "Exported with Block Launcher", "files": files,
                    "dependencies": {"minecraft": version}}
        zf.writestr("modrinth.index.json", json.dumps(manifest, indent=2))

