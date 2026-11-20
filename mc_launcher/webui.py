"""Loopback-only desktop fallback for Python builds without Tcl/Tk runtime files."""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import Minecraft, Profiles, default_root, read_json, write_json
from .modrinth import install_mod, search_mods

PAGE = r'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Block Launcher</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#11151b;color:#edf2f7;font:15px 'Segoe UI',Arial,sans-serif;display:flex;min-height:100vh}aside{width:220px;background:#0c1015;padding:26px 14px;flex:none}aside h2{color:#73d393;margin:0 12px 4px}aside small{color:#9aa8b5;margin-left:14px}aside button{display:block;width:100%;text-align:left;margin-top:20px}main{padding:34px;max-width:1100px;flex:1}h1{font-size:29px;margin:0}p,.muted{color:#9aa8b5}.card{background:#1b222b;border-radius:12px;padding:22px;margin-top:20px}button,select,input{border:0;border-radius:7px;padding:11px 14px;background:#29343e;color:#edf2f7;font-size:14px}button{cursor:pointer}button:hover{background:#3a4b58}.play{background:#45b879;color:#0b1a11;font-weight:bold;font-size:16px;padding:14px 25px}select,input{margin:6px}label{display:inline-block;margin:8px}table{width:100%;border-collapse:collapse;margin-top:16px}td,th{text-align:left;padding:10px;border-bottom:1px solid #303943}.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.hidden{display:none}.status{position:fixed;bottom:0;left:0;right:0;background:#0c1015;padding:9px 24px;color:#9aa8b5}
</style><style>@media(max-width:760px){body{display:block}aside{width:100%;padding:12px 14px}aside h2,aside small{display:inline-block;margin:4px 8px}aside button{display:inline-block;width:auto;margin:7px 3px;padding:9px}main{padding:14px}.card{padding:15px}table{display:block;overflow-x:auto}input,select{max-width:100%}}</style><body><aside><h2>⬢ BLOCK</h2><small>MINECRAFT JAVA</small><div id="nav"></div></aside><main><h1 id="title">Dein Spielplatz</h1><p id="sub">Minecraft Java starten und Installationen verwalten.</p><section id="home" class="card"><small class="muted">MINECRAFT JAVA EDITION</small><h2>Zeit für ein neues Abenteuer.</h2><div class="row"><label>Version <select id="version"></select></label><label>Offline-Profil <select id="profile"></select></label><button class="play" onclick="act('launch')">▶ SPIELEN</button></div><p id="homeInfo"></p></section>
<section id="versions" class="card hidden"><h2>Offizielle Versionen</h2><input id="search" placeholder="Version suchen" oninput="renderVersions()"><button onclick="refresh()">Aktualisieren</button><table><thead><tr><th>Version</th><th>Typ</th><th>Datum</th><th></th></tr></thead><tbody id="versionRows"></tbody></table></section>
<section id="accounts" class="card hidden"><h2>Lokale Offline-Profile</h2><p>Nur für Einzelspieler oder Server ohne Online-Authentifizierung.</p><div id="profiles"></div><input id="newProfile" placeholder="Spielername"><button onclick="act('add_profile')">Profil hinzufügen</button><button onclick="act('remove_profile')">Ausgewähltes Profil löschen</button></section>
<section id="settings" class="card hidden"><h2>Einstellungen</h2><label>Minecraft-Ordner <input id="rootPath" style="width:420px"></label><br><label>Java-Pfad <input id="javaPath" style="width:420px" placeholder="leer = automatisch"></label><br><label>RAM (GB) <input id="ram" type="number" min="2" max="16"></label><button onclick="act('settings')">Speichern</button></section>
<section id="mods" class="card hidden"><h2>Mods aus Modrinth installieren</h2><p>Suche nach einer kompatiblen Modrinth-Version und installiere sie inklusive erforderlicher Abhängigkeiten.</p><div class="row"><input id="modQuery" placeholder="Mod suchen, z. B. Sodium" style="flex:1;min-width:180px"><select id="modVersion"></select><select id="modLoader"><option>fabric</option><option>forge</option><option>neoforge</option><option>quilt</option></select><button onclick="modSearch()">Suchen</button></div><div id="modResults"></div><p id="modStatus" class="muted">Wähle den Loader, der bereits in deiner Minecraft-Installation eingerichtet ist.</p><hr><h3>Lokale Mods</h3><p>JAR-Dateien manuell verwalten.</p><input id="modPath" placeholder="Voller Pfad zur .jar-Datei" style="width:min(400px,100%)"><button onclick="act('add_mod')">JAR hinzufügen</button><input id="removeMod" placeholder="Dateiname zum Entfernen"><button onclick="act('remove_mod')">Entfernen</button></section>
<div class="status" id="status">Verbinde …</div></main><script>
let S={};let page='home';const pages={home:['Dein Spielplatz','Minecraft Java starten und Installationen verwalten.'],versions:['Versionen','Releases, Snapshots und ältere Versionen direkt aus dem Mojang-Manifest.'],accounts:['Spielerprofile','Lokale Offline-Profile verwalten.'],settings:['Einstellungen','Minecraft-Ordner, Java-Pfad und RAM.'],mods:['Mods','Mod-Dateien pro Installation verwalten.']};function nav(){document.getElementById('nav').innerHTML=Object.keys(pages).map(p=>`<button onclick="show('${p}')">${pages[p][0]}</button>`).join('')}function show(p){page=p;document.getElementById('title').textContent=pages[p][0];document.getElementById('sub').textContent=pages[p][1];for(const k of Object.keys(pages))document.getElementById(k).classList.toggle('hidden',k!==p)}async function api(path,body){let r=await fetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});return await r.json()}function setStatus(s){document.getElementById('status').textContent=s}async function refresh(){try{S=await api('state');draw()}catch(e){setStatus('Fehler: '+e)}}function draw(){let vs=S.versions||[],latest=S.latest||{};let opts=[`latest release (${latest.release||'…'})`,`latest snapshot (${latest.snapshot||'…'})`,...vs.map(v=>v.id)];for(let id of ['version','modVersion']){let el=document.getElementById(id),old=el.value;el.innerHTML=opts.map(x=>`<option>${x}</option>`).join('');el.value=opts.includes(old)?old:(id==='version'?S.selectedVersion||opts[0]:vs[0]?.id||'')}let ps=S.profiles||[];document.getElementById('profile').innerHTML=ps.map(x=>`<option>${x.name}</option>`).join('');document.getElementById('profile').value=S.profile||ps[0]?.name;document.getElementById('profiles').innerHTML=ps.map(x=>`<label><input type="radio" name="pick" value="${x.name}" ${x.name===S.profile?'checked':''}>${x.name}</label>`).join('');document.getElementById('rootPath').value=S.root;document.getElementById('javaPath').value=S.java||'';document.getElementById('ram').value=S.ram||4;renderVersions();document.getElementById('homeInfo').textContent=S.error||`${vs.length} Versionen verfügbar · ${S.installed?.length||0} installiert`;setStatus(S.status||'Bereit')}function renderVersions(){let q=(document.getElementById('search').value||'').toLowerCase();document.getElementById('versionRows').innerHTML=(S.versions||[]).filter(v=>v.id.toLowerCase().includes(q)||v.type.includes(q)).slice(0,250).map(v=>`<tr><td>${v.id}</td><td>${v.type}</td><td>${(v.releaseTime||'').slice(0,10)}</td><td><button onclick="act('install',{version:'${v.id}'})">Installieren</button></td></tr>`).join('')}async function act(action,extra={}){let data={action,...extra};if(action==='launch')data.version=document.getElementById('version').value;if(action==='add_profile')data.name=document.getElementById('newProfile').value;if(action==='remove_profile')data.name=document.querySelector('input[name=pick]:checked')?.value;if(action==='settings'){data.root=document.getElementById('rootPath').value;data.java=document.getElementById('javaPath').value;data.ram=document.getElementById('ram').value}if(action==='add_mod'){data.version=document.getElementById('modVersion').value;data.path=document.getElementById('modPath').value}if(action==='remove_mod'){data.version=document.getElementById('modVersion').value;data.name=document.getElementById('removeMod').value}try{let r=await api('action',data);setStatus(r.status||r.error);refresh()}catch(e){setStatus('Fehler: '+e)}}nav();show('home');refresh();setInterval(refresh,5000);
</script><script>
const drawBase=draw;draw=function(){drawBase();let e=document.getElementById('modVersion'),old=e.value,vs=S.versions||[];e.innerHTML=vs.map(v=>`<option>${esc(v.id)}</option>`).join('');e.value=vs.some(v=>v.id===old)?old:(vs[0]?.id||'');let ms=document.getElementById('modStatus');if(ms&&S.status?.startsWith('Modrinth'))ms.textContent=S.status};
async function modSearch(){let query=document.getElementById('modQuery').value.trim(),version=document.getElementById('modVersion').value,loader=document.getElementById('modLoader').value;let status=document.getElementById('modStatus'),results=document.getElementById('modResults');if(!query){status.textContent='Gib zuerst einen Modnamen ein.';return}status.textContent='Suche auf Modrinth …';results.innerHTML='';try{let r=await api('action',{action:'search_modrinth',query,version,loader});if(r.error)throw Error(r.error);results.innerHTML=(r.results||[]).map(p=>`<article class="card"><b>${esc(p.title)}</b> · ${esc(p.author)}<p>${esc(p.description||'')}</p><button onclick="installMod('${esc(p.project_id)}','${esc(p.title)}')">⬇ Mit einem Klick installieren</button></article>`).join('');status.textContent=`${(r.results||[]).length} passende Mods für ${version} / ${loader}`;if(!r.results?.length)results.innerHTML='<p>Keine passenden Mods gefunden.</p>'}catch(e){status.textContent='Suche fehlgeschlagen: '+e.message}}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function installMod(project,title){let version=document.getElementById('modVersion').value,loader=document.getElementById('modLoader').value;let status=document.getElementById('modStatus');status.textContent=`Installiere ${title} samt erforderlichen Abhängigkeiten …`;try{let r=await api('action',{action:'install_modrinth',project,version,loader});if(r.error)throw Error(r.error);status.textContent=r.status;refresh()}catch(e){status.textContent='Installation fehlgeschlagen: '+e.message}}
</script></body></html>'''


def run_webui() -> None:
    config_path = Path.home() / ".block-launcher" / "settings.json"
    config = read_json(config_path, {})
    state = {"status": "Bereit", "error": None}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _send(self, obj, kind="application/json; charset=utf-8"):
            body = obj.encode() if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self._send(PAGE, "text/html; charset=utf-8")
                return
            if self.path != "/api/state":
                self.send_error(404)
                return
            root = Path(config.get("minecraft_dir") or default_root())
            mc = Minecraft(root)
            profiles = Profiles(root).all() or [{"name": "Spieler", "uuid": None}]
            result = {"root": str(root), "java": config.get("java_path", ""), "ram": config.get("ram_gb", 4),
                      "profile": config.get("profile", profiles[0]["name"]), "selectedVersion": config.get("version", "latest release"),
                      "profiles": profiles, "status": state["status"], "error": state["error"]}
            try:
                manifest = mc.version_manifest()
                result.update({"versions": manifest.get("versions", []), "latest": manifest.get("latest", {})})
                result["installed"] = [p.name for p in (root / "versions").iterdir() if p.is_dir() and (p / f"{p.name}.jar").exists()] if (root / "versions").exists() else []
            except Exception as exc:
                result.update({"versions": [], "latest": {}, "error": f"Mojang-Manifest nicht erreichbar: {exc}"})
            self._send(result)

        def do_POST(self):
            if self.path != "/api/action":
                self.send_error(404)
                return
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                root = Path(config.get("minecraft_dir") or default_root())
                action = data.get("action")
                if action == "settings":
                    root = Path(data.get("root", "")).expanduser()
                    if not str(root):
                        raise ValueError("Minecraft-Ordner fehlt.")
                    root.mkdir(parents=True, exist_ok=True)
                    config.update({"minecraft_dir": str(root), "java_path": data.get("java", "").strip(), "ram_gb": max(2, min(16, int(data.get("ram", 4))))})
                    write_json(config_path, config)
                    response = "Einstellungen gespeichert."
                elif action == "search_modrinth":
                    version, loader = data.get("version", ""), data.get("loader", "")
                    if version not in {v.get("id") for v in Minecraft(root).version_manifest().get("versions", [])}:
                        raise ValueError("Minecraft-Version nicht erkannt.")
                    if loader not in {"fabric", "forge", "neoforge", "quilt"}:
                        raise ValueError("Ungültiger Modloader.")
                    results = search_mods(data.get("query", ""), version, loader)
                    self._send({"results": results})
                    return
                elif action == "install_modrinth":
                    version, loader, project = data.get("version", ""), data.get("loader", ""), data.get("project", "")
                    if not version or not version.replace(".", "").replace("-", "").isalnum():
                        raise ValueError("Ungültige Minecraft-Version.")
                    if loader not in {"fabric", "forge", "neoforge", "quilt"} or not project.isalnum():
                        raise ValueError("Ungültiger Loader oder Projektbezeichner.")
                    mods_dir = root / "instances" / version / "mods"
                    threading.Thread(target=self._install_modrinth, args=(project, version, loader, mods_dir), daemon=True).start()
                    response = "Modrinth-Installation gestartet."
                elif action == "add_profile":
                    name = data.get("name", "")
                    import re
                    if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", name):
                        raise ValueError("Name muss 3–16 Zeichen (Buchstaben, Zahlen, _) enthalten.")
                    profiles = Profiles(root)
                    items = profiles.all()
                    if any(x["name"].lower() == name.lower() for x in items):
                        raise ValueError("Dieses Profil existiert bereits.")
                    items.append({"name": name, "uuid": None})
                    profiles.save(items)
                    response = f"Profil {name} angelegt."
                elif action == "remove_profile":
                    name = data.get("name")
                    profiles = Profiles(root)
                    items = [x for x in profiles.all() if x["name"] != name]
                    if not items:
                        raise ValueError("Mindestens ein Offline-Profil muss bestehen bleiben.")
                    profiles.save(items)
                    response = f"Profil {name} entfernt."
                elif action == "install":
                    version = data.get("version", "")
                    threading.Thread(target=self._install, args=(root, version), daemon=True).start()
                    response = f"Installation {version} gestartet."
                elif action == "launch":
                    mc = Minecraft(root)
                    manifest = mc.version_manifest()
                    version = data.get("version", "")
                    if version.startswith("latest release"):
                        version = manifest.get("latest", {}).get("release")
                    elif version.startswith("latest snapshot"):
                        version = manifest.get("latest", {}).get("snapshot")
                    username = config.get("profile", "Spieler")
                    mc.launch(version, username, int(config.get("ram_gb", 4)), config.get("java_path") or None)
                    response = f"Minecraft {version} gestartet als {username}."
                elif action in ("add_mod", "remove_mod"):
                    version, mods = data.get("version", ""), root / "instances" / data.get("version", "") / "mods"
                    mods.mkdir(parents=True, exist_ok=True)
                    if action == "add_mod":
                        source = Path(data.get("path", "")).expanduser()
                        if source.suffix.lower() != ".jar" or not source.is_file() or source.stat().st_size > 250 * 1024 * 1024:
                            raise ValueError("Bitte einen lesbaren JAR-Pfad bis 250 MB angeben.")
                        import shutil
                        shutil.copy2(source, mods / source.name)
                        response = f"{source.name} hinzugefügt."
                    else:
                        name = Path(data.get("name", "")).name
                        if not name.endswith(".jar"):
                            raise ValueError("Ungültiger Mod-Dateiname.")
                        (mods / name).unlink(missing_ok=True)
                        response = f"{name} entfernt."
                else:
                    raise ValueError("Unbekannte Aktion.")
                self._send({"status": response})
            except Exception as exc:
                self._send({"error": str(exc), "status": f"Fehler: {exc}"})

        @staticmethod
        def _install(root, version):
            try:
                with lock:
                    state["status"] = f"Installiere {version} …"
                Minecraft(root).install(version, lambda s: state.update(status=s))
                state["status"] = f"Minecraft {version} ist installiert."
            except Exception as exc:
                state["status"] = f"Installationsfehler: {exc}"

        @staticmethod
        def _install_modrinth(project, version, loader, mods_dir):
            try:
                state["status"] = f"Installiere Mod für Minecraft {version} …"
                names = install_mod(project, version, loader, mods_dir, lambda msg: state.update(status=msg))
                state["status"] = "Modrinth-Installation fertig: " + (", ".join(names) or "bereits installiert")
            except Exception as exc:
                state["status"] = f"Modrinth-Fehler: {exc}"

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"
    print(f"Block Launcher läuft im Browser: {url}")
    webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()

