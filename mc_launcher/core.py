from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import uuid
import zipfile
from hashlib import md5
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Any

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
USER_AGENT = "BlockLauncher/0.2 (Python Minecraft launcher)"


def default_root() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / ".minecraft" / "PythonLauncher"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/minecraft"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "minecraft"


def read_json(path: Path, fallback: Any) -> Any:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def request_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_download(url: str, dest: Path, sha1: str | None = None,
                  sha512: str | None = None,
                  progress: Callable[[int, int], None] | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        valid = True
        if sha1:
            valid = file_sha1(dest).lower() == sha1.lower()
        if sha512:
            valid = valid and file_sha512(dest).lower() == sha512.lower()
        if valid:
            return
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    temp = dest.with_name(dest.name + ".part")
    digest = hashlib.sha1()
    digest512 = hashlib.sha512() if sha512 else None
    received = 0
    try:
        with urllib.request.urlopen(req, timeout=60) as response, temp.open("wb") as out:
            total = int(response.headers.get("Content-Length", 0))
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                if digest512:
                    digest512.update(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)
        if sha1 and digest.hexdigest().lower() != sha1.lower():
            raise ValueError(f"SHA-1-Prüfung fehlgeschlagen: {dest.name}")
        if sha512 and digest512.hexdigest().lower() != sha512.lower():
            raise ValueError(f"SHA-512-Prüfung fehlgeschlagen: {dest.name}")
        temp.replace(dest)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def file_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_sha512(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def os_name() -> str:
    return {"Windows": "windows", "Linux": "linux", "Darwin": "osx"}.get(platform.system(), "linux")


def rule_allowed(rules: list[dict] | None) -> bool:
    if not rules:
        return True
    allowed = False
    for rule in rules:
        os_rule = rule.get("os", {})
        # We do not advertise launcher-only features (demo mode, custom resolution,
        # quick-play capability) unless the UI explicitly implements them.
        if any(bool(value) for value in rule.get("features", {}).values()):
            continue
        if os_rule.get("name") and os_rule["name"] != os_name():
            continue
        if os_rule.get("arch") and os_rule["arch"] not in platform.machine().lower():
            continue
        allowed = rule.get("action") == "allow"
    return allowed


def offline_uuid(username: str) -> str:
    raw = bytearray(md5(("OfflinePlayer:" + username).encode("utf-8")).digest())
    raw[6] = (raw[6] & 0x0F) | 0x30
    raw[8] = (raw[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(raw)))


class Minecraft:
    def __init__(self, root: Path, workers: int = 8):
        self.root = root
        self.workers = max(1, min(32, workers))
        self.versions_dir = root / "versions"
        self.libraries_dir = root / "libraries"
        self.assets_dir = root / "assets"

    def version_manifest(self, refresh: bool = False) -> dict:
        cache = self.root / "cache" / "version_manifest_v2.json"
        if cache.exists() and not refresh:
            data = read_json(cache, None)
            if data:
                return data
        data = request_json(MANIFEST_URL)
        write_json(cache, data)
        return data

    def version_metadata(self, version_id: str) -> dict:
        path = self.versions_dir / version_id / f"{version_id}.json"
        if path.exists():
            data = read_json(path, None)
            if data:
                return data
        entry = next((v for v in self.version_manifest()["versions"] if v["id"] == version_id), None)
        if not entry:
            raise ValueError(f"Version nicht im Mojang-Manifest gefunden: {version_id}")
        data = request_json(entry["url"])
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, data)
        return data

    def install(self, version_id: str, report: Callable[[str], None] = lambda _: None) -> None:
        metadata = self.version_metadata(version_id)
        version_dir = self.versions_dir / version_id
        version_dir.mkdir(parents=True, exist_ok=True)
        downloads = metadata.get("downloads", {})
        client = downloads.get("client")
        if not client:
            raise ValueError("Diese Version enthält keinen offiziellen Client-Download.")
        report(f"Lade Minecraft {version_id} herunter …")
        safe_download(client["url"], version_dir / f"{version_id}.jar", client.get("sha1"))
        write_json(version_dir / f"{version_id}.json", metadata)
        jobs: list[tuple[str, Path, str | None]] = []
        for lib in metadata.get("libraries", []):
            if not rule_allowed(lib.get("rules")):
                continue
            downloads_data = lib.get("downloads", {})
            artifact = downloads_data.get("artifact")
            if artifact:
                jobs.append((artifact["url"], self.libraries_dir / artifact["path"], artifact.get("sha1")))
            classifier = lib.get("natives", {}).get(os_name())
            if classifier:
                classifier = classifier.replace("${arch}", "64" if platform.machine().endswith("64") else "32")
                native = downloads_data.get("classifiers", {}).get(classifier)
                if native:
                    jobs.append((native["url"], self.libraries_dir / native["path"], native.get("sha1")))
            elif "classifiers" in downloads_data:
                continue
            elif not artifact:
                # Legacy library metadata only supplies Maven coordinates.
                coord = lib.get("name", "").split(":")
                if len(coord) >= 3:
                    group, name, ver = coord[:3]
                    rel = "/".join(group.split(".")) + f"/{name}/{ver}/{name}-{ver}.jar"
                    base = lib.get("url", "https://libraries.minecraft.net/")
                    jobs.append((base.rstrip("/") + "/" + rel, self.libraries_dir / rel, None))
        self._download_jobs(jobs, report)
        asset_index = metadata.get("assetIndex")
        if asset_index:
            index_path = self.assets_dir / "indexes" / f"{asset_index['id']}.json"
            safe_download(asset_index["url"], index_path, asset_index.get("sha1"))
            index = read_json(index_path, {})
            objects = index.get("objects", {})
            asset_jobs = []
            for obj in objects.values():
                h = obj["hash"]
                asset_jobs.append((f"https://resources.download.minecraft.net/{h[:2]}/{h}",
                                   self.assets_dir / "objects" / h[:2] / h, h))
            report(f"Prüfe und lade {len(asset_jobs)} Assets …")
            self._download_jobs(asset_jobs, report)
        report(f"Minecraft {version_id} ist installiert.")

    def _download_jobs(self, jobs: list[tuple[str, Path, str | None]], report: Callable[[str], None]) -> None:
        errors = []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(safe_download, url, path, sha): path for url, path, sha in jobs}
            count = 0
            for future in as_completed(futures):
                count += 1
                try:
                    future.result()
                except Exception as exc:
                    errors.append(f"{futures[future].name}: {exc}")
                if count % 20 == 0 or count == len(jobs):
                    report(f"Dateien: {count}/{len(jobs)}")
        if errors:
            raise RuntimeError("Downloadfehler:\n" + "\n".join(errors[:8]))

    def launch(self, version_id: str, username: str, ram_gb: int, java_path: str | None = None,
               game_dir: Path | None = None) -> subprocess.Popen:
        metadata = self.version_metadata(version_id)
        version_dir = self.versions_dir / version_id
        jar = version_dir / f"{version_id}.jar"
        if not jar.exists():
            raise FileNotFoundError("Diese Version ist noch nicht installiert.")
        java = java_path or shutil.which("java")
        if not java:
            raise FileNotFoundError("Java wurde nicht gefunden. Installiere Java oder wähle den Java-Pfad in Einstellungen.")
        game_dir = game_dir or (self.root / "instances" / version_id)
        game_dir.mkdir(parents=True, exist_ok=True)
        natives_dir = game_dir / "natives"
        natives_dir.mkdir(exist_ok=True)
        classpath = [str(jar)]
        for lib in metadata.get("libraries", []):
            if not rule_allowed(lib.get("rules")):
                continue
            artifact = lib.get("downloads", {}).get("artifact")
            if artifact:
                p = self.libraries_dir / artifact["path"]
                if p.exists():
                    classpath.append(str(p))
            classifier = lib.get("natives", {}).get(os_name())
            if classifier:
                classifier = classifier.replace("${arch}", "64" if platform.machine().endswith("64") else "32")
                native = lib.get("downloads", {}).get("classifiers", {}).get(classifier)
                if native:
                    p = self.libraries_dir / native["path"]
                    if p.exists():
                        with zipfile.ZipFile(p) as zf:
                            for member in zf.namelist():
                                if member.endswith("/") or member.upper().startswith("META-INF/"):
                                    continue
                                zf.extract(member, natives_dir)
        version_info = metadata.get("javaVersion", {}).get("majorVersion", 8)
        assets = metadata.get("assets", "legacy")
        uid = offline_uuid(username)
        values = {
            "auth_player_name": username, "version_name": version_id, "game_directory": str(game_dir),
            "assets_root": str(self.assets_dir), "assets_index_name": metadata.get("assetIndex", {}).get("id", assets),
            "auth_uuid": uid.replace("-", ""), "auth_access_token": "0", "clientid": "0", "auth_xuid": "0",
            "user_type": "legacy", "version_type": metadata.get("type", "release"),
            "natives_directory": str(natives_dir), "launcher_name": "BlockLauncher",
            "launcher_version": "0.1", "classpath": os.pathsep.join(classpath),
            "classpath_separator": os.pathsep, "library_directory": str(self.libraries_dir),
            "resolution_width": "1280", "resolution_height": "720", "quickPlayPath": "",
            "quickPlaySingleplayer": "", "quickPlayMultiplayer": "", "quickPlayRealms": "",
        }
        try:
            version_result = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=10)
            version_text = version_result.stderr + version_result.stdout
            match = re.search(r'"(?:1\.)?(\d+)', version_text)
            if match and int(match.group(1)) < version_info:
                raise RuntimeError(f"Minecraft {version_id} benötigt Java {version_info} oder neuer; gefunden: Java {match.group(1)}.")
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Die Java-Version konnte nicht geprüft werden (Zeitüberschreitung).") from exc
        cmd = [java, "-Xms512M", f"-Xmx{max(1, int(ram_gb))}G"]
        cmd += self._expand_args(metadata.get("arguments", {}).get("jvm", ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]), values)
        cmd.append(metadata["mainClass"])
        if "arguments" in metadata:
            cmd += self._expand_args(metadata["arguments"].get("game", []), values)
        else:
            cmd += ["--username", username, "--version", version_id, "--gameDir", str(game_dir),
                    "--assetsDir", str(self.assets_dir), "--assetIndex", values["assets_index_name"],
                    "--uuid", uid.replace("-", ""), "--accessToken", "0", "--userType", "legacy"]
        log_path = self.root / "logs" / "latest-game.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as out:
            return subprocess.Popen(cmd, cwd=game_dir, stdout=out, stderr=subprocess.STDOUT)

    @staticmethod
    def _expand_args(args: list, values: dict[str, str]) -> list[str]:
        result = []
        for item in args:
            if isinstance(item, dict):
                if rule_allowed(item.get("rules")):
                    value = item.get("value", [])
                    result.extend(Minecraft._expand_args(value if isinstance(value, list) else [value], values))
            else:
                result.append(re.sub(r"\$\{([^}]+)}", lambda m: values.get(m.group(1), m.group(0)), str(item)))
        return result


class Profiles:
    def __init__(self, root: Path):
        self.path = root / "config" / "profiles.json"

    def all(self) -> list[dict]:
        return read_json(self.path, [])

    def save(self, profiles: list[dict]) -> None:
        write_json(self.path, profiles)


def discover_java() -> list[tuple[str, str]]:
    candidates = []
    found = shutil.which("java")
    if found:
        candidates.append((found, "PATH"))
    for home in [Path(os.environ.get("JAVA_HOME", "")), Path("C:/Program Files/Java"), Path("C:/Program Files/Eclipse Adoptium")]:
        if not str(home) or not home.exists():
            continue
        for path in home.glob("**/bin/java.exe" if os.name == "nt" else "**/bin/java"):
            candidates.append((str(path), str(home)))
    unique = {}
    for path, source in candidates:
        unique[path] = source
    return list(unique.items())


def available_ram_gb() -> int | None:
    try:
        if os.name == "nt":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return max(1, int(status.ullTotalPhys / (1024 ** 3)))
        else:
            page_size = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            return max(1, int(page_size * pages / (1024 ** 3)))
    except (AttributeError, OSError, ValueError):
        pass
    return None
