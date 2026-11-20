"""Loopback-only desktop fallback for Python builds without Tcl/Tk runtime files."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import Minecraft, Profiles, default_root, read_json, write_json
from .modrinth import install_mod, search_mods

PAGE = r'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Block Launcher</title>
<style>
:root{color-scheme:dark;--bg:#0b1016;--surface:#121a23;--card:#17222d;--raised:#1d2a36;--line:#2a3946;--text:#eff6f5;--muted:#9aabb8;--green:#79e0a1;--green2:#35bf78;--blue:#7ab8ff;--shadow:0 18px 50px #0005}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 78% -5%,#17382c 0,transparent 32%),var(--bg);color:var(--text);font:15px/1.55 Inter,'Segoe UI',system-ui,sans-serif;display:flex}aside{width:250px;min-height:100vh;position:sticky;top:0;align-self:flex-start;padding:30px 18px;background:#0d151cf2;border-right:1px solid #ffffff0c;flex:none}aside h2{font-size:22px;letter-spacing:.08em;color:var(--green);margin:0 12px}aside small{display:block;color:var(--muted);font-size:10px;letter-spacing:.15em;margin:0 13px 30px}#nav{display:grid;gap:7px}#nav button{width:100%;text-align:left;background:transparent;color:#b4c1cb;padding:12px 14px;border:1px solid transparent}#nav button:hover,#nav button:focus-visible{background:#ffffff0a;color:var(--text);border-color:#ffffff10}main{width:min(1100px,100%);padding:42px clamp(20px,5vw,64px) 84px;margin:auto}h1{font-size:clamp(28px,4vw,38px);letter-spacing:-.035em;line-height:1.15;margin:0}h2{font-size:23px;letter-spacing:-.02em;margin:8px 0 12px}h3{margin:0 0 8px}p,.muted{color:var(--muted)}main>#sub{margin:10px 0 28px}.card{background:linear-gradient(145deg,#192631,#141d27);border:1px solid #ffffff10;border-radius:18px;padding:clamp(20px,3vw,30px);margin:18px 0;box-shadow:var(--shadow);animation:enter .32s ease both}.card[ id="home"]{min-height:260px;background:radial-gradient(ellipse at 90% 0,#24553c55,transparent 45%),linear-gradient(145deg,#1a2a32,#141d27);padding-top:30px}#home>small{letter-spacing:.14em;color:var(--green)}button,select,input{font:inherit;color:var(--text);background:#202d39;border:1px solid #ffffff13;border-radius:10px;padding:11px 14px;transition:background .18s,border-color .18s,transform .18s,box-shadow .18s;max-width:100%}button{cursor:pointer;font-weight:600}button:hover{background:#2a3a47;border-color:#ffffff2a;transform:translateY(-1px)}button:active{transform:translateY(0)}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--green);outline-offset:2px}input::placeholder{color:#8293a0}input:focus,select:focus{border-color:#79e0a188;box-shadow:0 0 0 3px #79e0a118}.play{background:linear-gradient(135deg,var(--green),var(--green2));border:0;color:#07160e;font-weight:800;letter-spacing:.05em;font-size:15px;padding:14px 24px;box-shadow:0 8px 24px #35bf7833}.play:hover{background:linear-gradient(135deg,#9af0b8,#49d38a)}label{display:inline-grid;gap:5px;color:#c2cdd4;font-size:13px;font-weight:600}.row{display:flex;align-items:end;gap:12px;flex-wrap:wrap;margin:18px 0}.row input{flex:1;min-width:min(220px,100%)}select,input{min-width:140px}table{width:100%;border-collapse:collapse;margin-top:18px}td,th{text-align:left;padding:13px 11px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}tbody tr:hover{background:#ffffff06}.hidden{display:none!important}.status{position:fixed;z-index:4;bottom:14px;left:calc(250px + 50%);transform:translateX(-50%);width:min(800px,calc(100% - 280px));padding:11px 17px;border:1px solid #ffffff14;border-radius:12px;background:#101820ed;color:#c5d1d9;box-shadow:0 8px 30px #0006;backdrop-filter:blur(14px);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#modResults{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr));gap:12px;margin-top:14px}#modResults .card{margin:0;padding:18px;animation:enter .25s ease both}hr{border:0;border-top:1px solid var(--line);margin:28px 0}#profiles{display:grid;gap:8px;margin:16px 0}#profiles label{display:flex;align-items:center;gap:8px}.status:empty{display:none}@keyframes enter{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@media(max-width:820px){body{display:block}aside{position:relative;width:100%;min-height:0;padding:15px 18px;border-right:0;border-bottom:1px solid #ffffff10}aside h2{display:inline-block;margin:0 8px 0 0}aside small{display:inline-block;margin:0}#nav{display:flex;overflow-x:auto;gap:5px;margin-top:12px;padding-bottom:3px}#nav button{width:auto;white-space:nowrap;padding:9px 12px}main{padding:26px 18px 86px}.status{left:50%;width:calc(100% - 28px);bottom:10px}}@media(max-width:520px){main{padding:22px 13px 82px}.card{border-radius:14px;padding:18px}.row{align-items:stretch;gap:8px}.row>*{min-width:0}.row label{flex:1 1 145px}.row input{flex:1 1 100%}.row button{flex:1 1 auto}table{display:block;overflow-x:auto;white-space:nowrap}#settings input{width:100%!important;margin-left:0}.play{width:100%}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style><body><aside><h2>⬢ BLOCK</h2><small>MINECRAFT JAVA</small><div id="nav"></div></aside><main><h1 id="title">Dein Spielplatz</h1><p id="sub">Minecraft Java starten und Installationen verwalten.</p><section id="home" class="card"><small class="muted">MINECRAFT JAVA EDITION</small><h2>Zeit für ein neues Abenteuer.</h2><div class="row"><label>Version <select id="version"></select></label><label>Offline-Profil <select id="profile"></select></label><button class="play" onclick="act('launch')">▶ SPIELEN</button></div><p id="homeInfo"></p></section>
<section id="versions" class="card hidden"><h2>Offizielle Versionen</h2><input id="search" placeholder="Version suchen" oninput="renderVersions()"><button onclick="refresh()">Aktualisieren</button><table><thead><tr><th>Version</th><th>Typ</th><th>Datum</th><th></th></tr></thead><tbody id="versionRows"></tbody></table></section>
<section id="accounts" class="card hidden"><h2>Lokale Offline-Profile</h2><p>Nur für Einzelspieler oder Server ohne Online-Authentifizierung.</p><div id="profiles"></div><input id="newProfile" placeholder="Spielername"><button onclick="act('add_profile')">Profil hinzufügen</button><button onclick="act('remove_profile')">Ausgewähltes Profil löschen</button></section>
<section id="settings" class="card hidden"><h2>Einstellungen</h2><label>Minecraft-Ordner <input id="rootPath" style="width:420px"></label><br><label>Java-Pfad <input id="javaPath" style="width:420px" placeholder="leer = automatisch"></label><br><label>RAM (GB) <input id="ram" type="number" min="2" max="16"></label><button onclick="act('settings')">Speichern</button></section>
<section id="mods" class="card hidden"><h2>Mods aus Modrinth installieren</h2><p>Der Launcher richtet Fabric oder Quilt ein, installiert den Mod und erforderliche Abhängigkeiten und wählt das Mod-Profil zum Starten aus.</p><div class="row"><input id="modQuery" placeholder="Mod suchen, z. B. Sodium" style="flex:1;min-width:180px"><select id="modVersion"></select><select id="modLoader"><option>fabric</option><option>quilt</option></select><button onclick="modSearch()">Suchen</button></div><div id="modResults"></div><p id="modStatus" class="muted">Wähle Minecraft-Version und Loader. Forge/NeoForge werden hier noch nicht unterstützt.</p><hr><h3>Lokale Mods</h3><p>JAR-Dateien manuell verwalten.</p><input id="modPath" placeholder="Voller Pfad zur .jar-Datei" style="width:min(400px,100%)"><button onclick="act('add_mod')">JAR hinzufügen</button><input id="removeMod" placeholder="Dateiname zum Entfernen"><button onclick="act('remove_mod')">Entfernen</button></section>
<div class="status" id="status">Verbinde …</div></main><script>
let S={};let page='home';const pages={home:['Dein Spielplatz','Minecraft Java starten und Installationen verwalten.'],versions:['Versionen','Releases, Snapshots und ältere Versionen direkt aus dem Mojang-Manifest.'],accounts:['Spielerprofile','Lokale Offline-Profile verwalten.'],settings:['Einstellungen','Minecraft-Ordner, Java-Pfad und RAM.'],mods:['Mods','Mod-Dateien pro Installation verwalten.']};function nav(){document.getElementById('nav').innerHTML=Object.keys(pages).map(p=>`<button onclick="show('${p}')">${pages[p][0]}</button>`).join('')}function show(p){page=p;document.getElementById('title').textContent=pages[p][0];document.getElementById('sub').textContent=pages[p][1];for(const k of Object.keys(pages))document.getElementById(k).classList.toggle('hidden',k!==p);document.querySelectorAll('#nav button').forEach((b,i)=>{b.style.background=Object.keys(pages)[i]===p?'#ffffff0d':'';b.style.color=Object.keys(pages)[i]===p?'#eff6f5':''})}async function api(path,body){let r=await fetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});return await r.json()}function setStatus(s){document.getElementById('status').textContent=s}async function refresh(){try{S=await api('state');draw()}catch(e){setStatus('Fehler: '+e)}}function draw(){let vs=S.versions||[],latest=S.latest||{};let opts=[`latest release (${latest.release||'…'})`,`latest snapshot (${latest.snapshot||'…'})`,...vs.map(v=>v.id)];for(let id of ['version','modVersion']){let el=document.getElementById(id),old=el.value;el.innerHTML=opts.map(x=>`<option>${x}</option>`).join('');el.value=opts.includes(old)?old:(id==='version'?S.selectedVersion||opts[0]:vs[0]?.id||'')}let ps=S.profiles||[];document.getElementById('profile').innerHTML=ps.map(x=>`<option>${x.name}</option>`).join('');document.getElementById('profile').value=S.profile||ps[0]?.name;document.getElementById('profiles').innerHTML=ps.map(x=>`<label><input type="radio" name="pick" value="${x.name}" ${x.name===S.profile?'checked':''}>${x.name}</label>`).join('');document.getElementById('rootPath').value=S.root;document.getElementById('javaPath').value=S.java||'';document.getElementById('ram').value=S.ram||4;renderVersions();document.getElementById('homeInfo').textContent=S.error||`${vs.length} Versionen verfügbar · ${S.installed?.length||0} installiert`;setStatus(S.status||'Bereit')}function renderVersions(){let q=(document.getElementById('search').value||'').toLowerCase();document.getElementById('versionRows').innerHTML=(S.versions||[]).filter(v=>v.id.toLowerCase().includes(q)||v.type.includes(q)).slice(0,250).map(v=>`<tr><td>${v.id}</td><td>${v.type}</td><td>${(v.releaseTime||'').slice(0,10)}</td><td><button onclick="act('install',{version:'${v.id}'})">Installieren</button></td></tr>`).join('')}async function act(action,extra={}){let data={action,...extra};if(action==='launch')data.version=document.getElementById('version').value;if(action==='add_profile')data.name=document.getElementById('newProfile').value;if(action==='remove_profile')data.name=document.querySelector('input[name=pick]:checked')?.value;if(action==='settings'){data.root=document.getElementById('rootPath').value;data.java=document.getElementById('javaPath').value;data.ram=document.getElementById('ram').value}if(action==='add_mod'){data.version=document.getElementById('modVersion').value;data.path=document.getElementById('modPath').value}if(action==='remove_mod'){data.version=document.getElementById('modVersion').value;data.name=document.getElementById('removeMod').value}try{let r=await api('action',data);setStatus(r.status||r.error);refresh()}catch(e){setStatus('Fehler: '+e)}}nav();show('home');refresh();setInterval(refresh,5000);
</script><script>
let lastConfiguredVersion=null;const drawBase=draw;draw=function(){drawBase();let vs=S.versions||[],aliases=[`latest release (${S.latest?.release||'…'})`,`latest snapshot (${S.latest?.snapshot||'…'})`],profiles=(S.loaderProfiles||[]).map(x=>x.id),v=document.getElementById('version'),old=v.value,all=[...aliases,...vs.map(x=>x.id),...profiles],changed=S.selectedVersion&&S.selectedVersion!==lastConfiguredVersion;lastConfiguredVersion=S.selectedVersion||lastConfiguredVersion;v.innerHTML=all.map(x=>`<option>${esc(x)}</option>`).join('');let selected=changed?S.selectedVersion:(all.includes(old)?old:S.selectedVersion);v.value=all.includes(selected)?selected:(aliases[0]||'');let e=document.getElementById('modVersion'),oldMod=e.value;e.innerHTML=vs.map(x=>`<option>${esc(x.id)}</option>`).join('');e.value=vs.some(x=>x.id===oldMod)?oldMod:(vs[0]?.id||'');let ms=document.getElementById('modStatus');if(ms&&S.status?.startsWith('Modrinth'))ms.textContent=S.status};
async function modSearch(){let query=document.getElementById('modQuery').value.trim(),version=document.getElementById('modVersion').value,loader=document.getElementById('modLoader').value;let status=document.getElementById('modStatus'),results=document.getElementById('modResults');if(!query){status.textContent='Gib zuerst einen Modnamen ein.';return}status.textContent='Suche auf Modrinth …';results.innerHTML='';try{let r=await api('action',{action:'search_modrinth',query,version,loader});if(r.error)throw Error(r.error);results.innerHTML=(r.results||[]).map(p=>`<article class="card"><b>${esc(p.title)}</b> · ${esc(p.author)}<p>${esc(p.description||'')}</p><button onclick="installMod('${esc(p.project_id)}','${esc(p.title)}')">⬇ Mit einem Klick installieren</button></article>`).join('');status.textContent=`${(r.results||[]).length} passende Mods für ${version} / ${loader}`;if(!r.results?.length)results.innerHTML='<p>Keine passenden Mods gefunden.</p>'}catch(e){status.textContent='Suche fehlgeschlagen: '+e.message}}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function installMod(project,title){let version=document.getElementById('modVersion').value,loader=document.getElementById('modLoader').value;let status=document.getElementById('modStatus');status.textContent=`Installiere ${title} samt erforderlichen Abhängigkeiten …`;try{let r=await api('action',{action:'install_modrinth',project,version,loader});if(r.error)throw Error(r.error);status.textContent=r.status;refresh()}catch(e){status.textContent='Installation fehlgeschlagen: '+e.message}}
</script></body></html>'''


def run_webui() -> None:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("Das eingebettete Fenster benötigt pywebview. Starte start.bat, um es einzurichten.") from exc

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
                result["loaderProfiles"] = []
                for profile_file in mc.versions_dir.glob("*/*.json") if mc.versions_dir.exists() else []:
                    profile = read_json(profile_file, {})
                    if profile.get("id") == profile_file.parent.name and profile.get("inheritsFrom") and mc.is_installed(profile_file.parent.name):
                        result["loaderProfiles"].append({"id": profile_file.parent.name, "gameVersion": profile["inheritsFrom"]})
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
                    if loader not in {"fabric", "quilt"}:
                        raise ValueError("Ungültiger Modloader.")
                    results = search_mods(data.get("query", ""), version, loader)
                    self._send({"results": results})
                    return
                elif action == "install_modrinth":
                    version, loader, project = data.get("version", ""), data.get("loader", ""), data.get("project", "")
                    if not version or not version.replace(".", "").replace("-", "").isalnum():
                        raise ValueError("Ungültige Minecraft-Version.")
                    if loader not in {"fabric", "quilt"} or not project.isalnum():
                        raise ValueError("Ungültiger Loader oder Projektbezeichner.")
                    threading.Thread(target=self._install_modrinth, args=(root, project, version, loader), daemon=True).start()
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
                    version = data.get("version", "")
                    active_version = config.get("version", "")
                    active_metadata = read_json(root / "versions" / active_version / f"{active_version}.json", {})
                    target_version = active_version if active_metadata.get("inheritsFrom") == version else version
                    mods = root / "instances" / target_version / "mods"
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
        def _install_modrinth(root, project, version, loader):
            try:
                state["status"] = f"Installiere {loader.title()} für Minecraft {version} …"
                profile_id = Minecraft(root).install_loader(version, loader, lambda msg: state.update(status=msg))
                config["version"] = profile_id
                write_json(config_path, config)
                mods_dir = root / "instances" / profile_id / "mods"
                state["status"] = "Lade Modrinth-Mods herunter …"
                names = install_mod(project, version, loader, mods_dir, lambda msg: state.update(status=msg))
                state["status"] = "Modrinth-Installation fertig; Startprofil " + profile_id + ": " + (", ".join(names) or "bereits installiert")
            except Exception as exc:
                state["status"] = f"Modrinth-Fehler: {exc}"

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"
    try:
        webview.create_window("Block Launcher", url, width=1180, height=800, min_size=(760, 540))
        webview.start()
    finally:
        server.shutdown()
        server.server_close()

