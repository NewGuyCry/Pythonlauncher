from __future__ import annotations

import json
import urllib.parse
import urllib.request
from urllib.parse import urlparse
from pathlib import Path

from .core import safe_download

API = "https://api.modrinth.com/v2"
USER_AGENT = "BlockLauncher/0.2 (local Minecraft launcher)"


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as res:
        return json.loads(res.read().decode("utf-8"))


def search_mods(query: str, game_version: str, loader: str, limit: int = 30) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    facets = [["project_type:mod"], [f"versions:{game_version}"]]
    if loader and loader != "any":
        facets.append([f"categories:{loader}"])
    params = urllib.parse.urlencode({"query": query, "facets": json.dumps(facets), "limit": min(50, max(1, limit)), "index": "relevance"})
    return _get_json(f"{API}/search?{params}").get("hits", [])


def _compatible_versions(project_id: str, game_version: str, loader: str) -> list[dict]:
    params = {"game_versions": json.dumps([game_version])}
    if loader and loader != "any":
        params["loaders"] = json.dumps([loader])
    url = f"{API}/project/{urllib.parse.quote(project_id, safe='')}/version?{urllib.parse.urlencode(params)}"
    versions = _get_json(url)
    return [v for v in versions if game_version in v.get("game_versions", []) and (loader == "any" or loader in v.get("loaders", []))]


def install_mod(project_id: str, game_version: str, loader: str, mods_dir: Path,
                progress=lambda _: None) -> list[str]:
    """Install the latest matching release and its required Modrinth dependencies."""
    mods_dir.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    seen_projects: set[str] = set()
    seen_versions: set[str] = set()

    def install_project(current_id: str, pinned_version: str | None = None):
        if current_id in seen_projects:
            return
        if len(seen_projects) >= 20:
            raise ValueError("Mod hat mehr als 20 erforderliche Abhängigkeiten; Installation abgebrochen.")
        seen_projects.add(current_id)
        candidates = _compatible_versions(current_id, game_version, loader)
        if pinned_version:
            candidates = [v for v in candidates if v.get("id") == pinned_version]
        if not candidates:
            raise ValueError(f"Keine kompatible Version für {current_id} ({game_version}, {loader}).")
        version = candidates[0]
        if version.get("version_type") not in ("release", "beta") or version.get("status") not in (None, "listed"):
            release = next((v for v in candidates if v.get("version_type") == "release" and v.get("status") in (None, "listed")), None)
            version = release or version
        for dependency in version.get("dependencies", []):
            if dependency.get("dependency_type") != "required":
                continue
            dep_id = dependency.get("project_id")
            dep_version = dependency.get("version_id")
            if dep_id:
                install_project(dep_id, dep_version)
            elif dep_version and dep_version not in seen_versions:
                dep = _get_json(f"{API}/version/{urllib.parse.quote(dep_version, safe='')}")
                _install_version(dep, mods_dir, installed, progress)
        _install_version(version, mods_dir, installed, progress)

    def _install_version(version, target, installed_names, report):
        version_id = version.get("id")
        if not version_id or version_id in seen_versions:
            return
        seen_versions.add(version_id)
        files = version.get("files", [])
        primary = next((f for f in files if f.get("primary")), files[0] if files else None)
        if not primary:
            raise ValueError(f"Modrinth-Version {version.get('name', version_id)} enthält keine Datei.")
        filename = primary.get("filename", "")
        url = primary.get("url", "")
        hashes = primary.get("hashes", {})
        if not filename.lower().endswith(".jar") or Path(filename).name != filename:
            raise ValueError(f"Ungültiger Mod-Dateiname: {filename}")
        if urlparse(url).scheme != "https" or not (hashes.get("sha1") or hashes.get("sha512")):
            raise ValueError("Modrinth-Datei hat keinen sicheren HTTPS-Link oder keine Prüfsumme.")
        dest = target / filename
        report(f"Lade {filename} …")
        safe_download(url, dest, hashes.get("sha1"), sha512=hashes.get("sha512"))
        installed_names.append(filename)

    install_project(project_id)
    return installed

