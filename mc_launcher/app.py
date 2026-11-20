from __future__ import annotations

import logging
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .core import Minecraft, Profiles, available_ram_gb, default_root, discover_java, read_json, write_json
from .packs import export_modrinth_pack, import_modrinth_pack

BG = "#11151b"
PANEL = "#1b222b"
PANEL2 = "#232d37"
TEXT = "#edf2f7"
MUTED = "#9aa8b5"
GREEN = "#73d393"
ACCENT = "#45b879"


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.window = root
        self.config_path = Path.home() / ".block-launcher" / "settings.json"
        self.config = read_json(self.config_path, {})
        self.mc_root = Path(self.config.get("minecraft_dir") or default_root())
        self.mc = Minecraft(self.mc_root, int(self.config.get("parallel_downloads", 8)))
        self.profiles = Profiles(self.mc_root)
        self.manifest = {"versions": []}
        self.proc = None
        self.current_page = "Home"
        self.window.title("Block Launcher")
        self.window.geometry("1120x740")
        self.window.minsize(900, 600)
        self.window.configure(bg=BG)
        self._style()
        self._load_saved()
        self._layout()
        self.load_versions()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("PanelMuted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 22, "bold"))
        style.configure("Hero.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 17, "bold"))
        style.configure("TButton", background=PANEL2, foreground=TEXT, padding=(13, 8), borderwidth=0, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#34434f")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#0b1a11", padding=(20, 12), font=("Segoe UI", 11, "bold"))
        style.map("Accent.TButton", background=[("active", "#58c988")])
        style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT, font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#276643")])

    def _layout(self):
        self.nav = tk.Frame(self.window, bg="#0c1015", width=205)
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)
        tk.Label(self.nav, text="⬢  BLOCK", bg="#0c1015", fg=GREEN, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=22, pady=(25, 4))
        tk.Label(self.nav, text="MINECRAFT JAVA", bg="#0c1015", fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=25, pady=(0, 22))
        self.nav_buttons = {}
        for page in ["Home", "Versions", "Mods", "Modpacks", "Accounts", "Settings"]:
            button = tk.Button(self.nav, text=page, anchor="w", padx=20, pady=11, bd=0, cursor="hand2",
                               bg="#0c1015", fg=MUTED, activebackground=PANEL, activeforeground=TEXT,
                               font=("Segoe UI", 10), command=lambda p=page: self.show_page(p))
            button.pack(fill="x", padx=9, pady=2)
            self.nav_buttons[page] = button
        tk.Label(self.nav, text="Vanilla • Java Edition", bg="#0c1015", fg=MUTED, font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=20, pady=18)
        self.content = tk.Frame(self.window, bg=BG)
        self.content.pack(side="left", fill="both", expand=True, padx=30, pady=24)
        self.status_var = tk.StringVar(value="Bereit")
        tk.Label(self.window, textvariable=self.status_var, anchor="w", bg="#0c1015", fg=MUTED, padx=215, pady=7, font=("Segoe UI", 8)).pack(side="bottom", fill="x")
        self.show_page("Home")

    def _load_saved(self):
        profs = self.profiles.all()
        if not profs:
            profs = [{"name": "Spieler", "uuid": None}]
            self.profiles.save(profs)
        self.selected_profile = self.config.get("profile", profs[0]["name"])
        self.selected_version = self.config.get("version", "latest release")
        self.ram = int(self.config.get("ram_gb", 4))

    def show_page(self, page: str):
        self.current_page = page
        for name, button in self.nav_buttons.items():
            button.configure(bg=PANEL if name == page else "#0c1015", fg=TEXT if name == page else MUTED)
        for child in self.content.winfo_children():
            child.destroy()
        getattr(self, f"page_{page.lower()}")()

    def heading(self, title: str, subtitle: str):
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.content, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(3, 20))

    def panel(self, parent=None, **kwargs):
        return ttk.Frame(parent or self.content, style="Panel.TFrame", padding=18, **kwargs)

    def page_home(self):
        self.heading("Dein Spielplatz", "Minecraft Java starten und Installationen verwalten.")
        hero = self.panel()
        hero.pack(fill="x", pady=(0, 16))
        ttk.Label(hero, text="MINECRAFT  JAVA EDITION", style="PanelMuted.TLabel").pack(anchor="w")
        ttk.Label(hero, text="Zeit für ein neues Abenteuer.", style="Hero.TLabel").pack(anchor="w", pady=(7, 20))
        row = ttk.Frame(hero, style="Panel.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Version", style="PanelMuted.TLabel").pack(side="left")
        self.home_version = ttk.Combobox(row, width=24, state="readonly")
        self.home_version.pack(side="left", padx=(8, 20))
        self.home_version.bind("<<ComboboxSelected>>", lambda _: self._version_changed(self.home_version.get()))
        ttk.Label(row, text="Profil", style="PanelMuted.TLabel").pack(side="left")
        self.home_profile = ttk.Combobox(row, width=18, state="readonly")
        self.home_profile.pack(side="left", padx=8)
        self.home_profile.bind("<<ComboboxSelected>>", lambda _: self._profile_changed(self.home_profile.get()))
        self.play_button = ttk.Button(row, text="▶  SPIELEN", style="Accent.TButton", command=self.launch_game)
        self.play_button.pack(side="right")
        self.home_status = ttk.Label(hero, text="Versionen werden geladen …", style="PanelMuted.TLabel")
        self.home_status.pack(anchor="w", pady=(14, 0))
        cards = ttk.Frame(self.content)
        cards.pack(fill="both", expand=True)
        for title, desc, action in [("Versionen", "Releases und Snapshots von Mojang laden.", "Versions"),
                                    ("Profile", "Lokale Offline-Spieler verwalten.", "Accounts"),
                                    ("Einstellungen", "RAM, Java und Minecraft-Ordner.", "Settings")]:
            card = self.panel(cards)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            ttk.Label(card, text=title, style="Hero.TLabel").pack(anchor="w")
            ttk.Label(card, text=desc, style="PanelMuted.TLabel", wraplength=200).pack(anchor="w", pady=(8, 20))
            ttk.Button(card, text="Öffnen", command=lambda p=action: self.show_page(p)).pack(anchor="w")
        self._refresh_home_choices()

    def page_versions(self):
        self.heading("Versionen", "Offizielle Versionen aus dem Mojang-Manifest installieren.")
        top = ttk.Frame(self.content)
        top.pack(fill="x", pady=(0, 12))
        self.version_search = tk.StringVar()
        ent = tk.Entry(top, textvariable=self.version_search, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
        ent.pack(side="left", fill="x", expand=True, ipady=9)
        ent.bind("<KeyRelease>", lambda _: self._filter_versions())
        ttk.Button(top, text="Aktualisieren", command=lambda: self.load_versions(refresh=True)).pack(side="left", padx=10)
        self.versions_tree = ttk.Treeview(self.content, columns=("version", "type", "release", "status"), show="headings")
        for col, label, width in [("version", "VERSION", 220), ("type", "TYP", 120), ("release", "DATUM", 160), ("status", "STATUS", 160)]:
            self.versions_tree.heading(col, text=label)
            self.versions_tree.column(col, width=width)
        self.versions_tree.heading("#0", text="VERSION") if "#0" in self.versions_tree["columns"] else None
        self.versions_tree.pack(fill="both", expand=True)
        self.versions_tree.bind("<Double-1>", lambda _: self.install_selected())
        controls = ttk.Frame(self.content)
        controls.pack(fill="x", pady=14)
        ttk.Button(controls, text="Installieren", command=self.install_selected).pack(side="left")
        ttk.Label(controls, text="Doppelklick auf eine Version installiert sie.", style="Muted.TLabel").pack(side="left", padx=14)
        self.versions_status = tk.StringVar(value="Lade Manifest …")
        ttk.Label(self.content, textvariable=self.versions_status, style="Muted.TLabel").pack(anchor="w")
        self._filter_versions()

    def page_accounts(self):
        self.heading("Spielerprofile", "Offline-Profile funktionieren lokal und auf Servern mit deaktivierter Online-Authentifizierung.")
        box = self.panel()
        box.pack(fill="both", expand=True)
        self.account_list = tk.Listbox(box, bg=PANEL, fg=TEXT, selectbackground="#276643", relief="flat", font=("Segoe UI", 11), height=10)
        self.account_list.pack(fill="both", expand=True)
        bar = ttk.Frame(box, style="Panel.TFrame")
        bar.pack(fill="x", pady=(16, 0))
        ttk.Button(bar, text="Profil hinzufügen", command=self.add_profile).pack(side="left")
        ttk.Button(bar, text="Entfernen", command=self.remove_profile).pack(side="left", padx=8)
        ttk.Button(bar, text="Als aktives Profil setzen", command=self.set_profile).pack(side="left")
        self.refresh_profiles()

    def page_settings(self):
        self.heading("Einstellungen", "Lege Speicherort, Java und Arbeitsspeicher fest.")
        box = self.panel()
        box.pack(fill="x")
        self.setting_ram = tk.IntVar(value=self.ram)
        self.setting_path = tk.StringVar(value=str(self.mc_root))
        self.setting_java = tk.StringVar(value=self.config.get("java_path", ""))
        self.setting_workers = tk.IntVar(value=int(self.config.get("parallel_downloads", 8)))
        self._setting_row(box, "Minecraft-Verzeichnis", self.setting_path, lambda: self._browse_dir(self.setting_path))
        self._setting_row(box, "Java-Pfad (leer = automatisch)", self.setting_java, lambda: self._browse_java())
        ramrow = ttk.Frame(box, style="Panel.TFrame")
        ramrow.pack(fill="x", pady=12)
        ttk.Label(ramrow, text="RAM für Minecraft", style="Panel.TLabel", width=28).pack(side="left")
        total_ram = available_ram_gb()
        ram_max = max(2, min(16, total_ram or 16))
        ttk.Scale(ramrow, from_=2, to=ram_max, variable=self.setting_ram, orient="horizontal").pack(side="left", fill="x", expand=True, padx=12)
        self.ram_label = ttk.Label(ramrow, text=f"{self.ram} GB", style="Panel.TLabel")
        self.ram_label.pack(side="left")
        self.setting_ram.trace_add("write", lambda *_: self.ram_label.configure(text=f"{self.setting_ram.get()} GB"))
        ttk.Label(box, text=(f"Erkannter Arbeitsspeicher: {total_ram} GB. Hohe Zuweisungen lassen wenig Speicher für Windows und andere Programme." if total_ram else "Hohe RAM-Zuweisungen lassen wenig Speicher für Windows und andere Programme."), style="PanelMuted.TLabel", wraplength=760).pack(anchor="w")
        self._setting_row(box, "Parallele Downloads (1–16)", self.setting_workers, None)
        ttk.Button(box, text="Einstellungen speichern", style="Accent.TButton", command=self.save_settings).pack(anchor="e", pady=(12, 0))
        java = self.panel()
        java.pack(fill="x", pady=16)
        ttk.Label(java, text="Java gefunden", style="Hero.TLabel").pack(anchor="w", pady=(0, 8))
        found = discover_java()
        ttk.Label(java, text="\n".join(f"{p}  ({src})" for p, src in found) if found else "Java wurde nicht im PATH gefunden.", style="PanelMuted.TLabel", wraplength=700).pack(anchor="w")

    def page_mods(self):
        self.heading("Mods", "Mod-Dateien pro Installation verwalten. Vanilla und Fabric-Mods werden als JAR-Dateien unterstützt.")
        bar = ttk.Frame(self.content)
        bar.pack(fill="x", pady=(0, 12))
        self.mods_version = ttk.Combobox(bar, state="readonly", width=28)
        self.mods_version.pack(side="left")
        self.mods_version.bind("<<ComboboxSelected>>", lambda _: self.refresh_mods())
        ttk.Button(bar, text="JAR hinzufügen", command=self.add_mod).pack(side="left", padx=8)
        ttk.Button(bar, text="Entfernen", command=self.remove_mod).pack(side="left")
        self.mods_list = tk.Listbox(self.content, bg=PANEL, fg=TEXT, selectbackground="#276643", relief="flat", font=("Segoe UI", 10))
        self.mods_list.pack(fill="both", expand=True)
        self._refresh_mod_versions()

    def page_modpacks(self):
        self.heading("Modpacks", "Importiere Modrinth .mrpack-Dateien in getrennte Instanzen.")
        box = self.panel()
        box.pack(fill="x")
        ttk.Label(box, text="Modrinth Modpack", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(box, text="Beim Import werden Modrinth-Downloads geprüft und die Pack-Overrides übernommen. CurseForge-Archive sind derzeit nicht installierbar, da die offiziellen API-Dateien eine CurseForge-API-Berechtigung erfordern.", style="PanelMuted.TLabel", wraplength=760).pack(anchor="w", pady=10)
        ttk.Button(box, text=".mrpack importieren", command=self.import_pack).pack(anchor="w")
        ttk.Label(box, text=f"Instanzen: {self.mc_root / 'instances'}", style="Muted.TLabel").pack(anchor="w", pady=12)
        packbar = ttk.Frame(box, style="Panel.TFrame")
        packbar.pack(fill="x", pady=(4, 0))
        ttk.Button(packbar, text="Modpack-Instanz exportieren", command=self.export_pack).pack(side="left")
        ttk.Label(packbar, text="Exportiert Instanzdateien als Modrinth-Archiv mit Overrides.", style="PanelMuted.TLabel").pack(side="left", padx=12)

    def _setting_row(self, parent, label, var, command):
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=9)
        ttk.Label(row, text=label, style="Panel.TLabel", width=29).pack(side="left")
        entry = tk.Entry(row, textvariable=var, bg=PANEL2, fg=TEXT, insertbackground=TEXT, relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        if command:
            ttk.Button(row, text="Durchsuchen", command=command).pack(side="left", padx=(8, 0))

    def load_versions(self, refresh=False):
        def work():
            try:
                manifest = self.mc.version_manifest(refresh=refresh)
                self.window.after(0, lambda: self._versions_loaded(manifest))
            except Exception as exc:
                self.window.after(0, lambda: self._show_error(f"Versionsliste konnte nicht geladen werden:\n{exc}"))
        threading.Thread(target=work, daemon=True).start()

    def _versions_loaded(self, manifest):
        self.manifest = manifest
        if self.current_page == "Versions":
            self._filter_versions()
        self._refresh_home_choices()
        self.status_var.set(f"{len(manifest.get('versions', []))} offizielle Versionen geladen")

    def _filter_versions(self):
        if not hasattr(self, "versions_tree"):
            return
        q = self.version_search.get().strip().lower()
        self.versions_tree.delete(*self.versions_tree.get_children())
        for version in self.manifest.get("versions", []):
            if q and q not in version["id"].lower() and q not in version["type"].lower():
                continue
            installed = (self.mc_root / "versions" / version["id"] / f"{version['id']}.jar").exists()
            self.versions_tree.insert("", "end", iid=version["id"], values=(version["id"], version["type"], version.get("releaseTime", "")[:10], "Installiert" if installed else "Nicht installiert"))
        if not self.versions_tree.get_children():
            self.versions_status.set("Keine passenden Versionen.")

    def _version_changed(self, value):
        self.selected_version = value
        self.config["version"] = value
        self._save_config()
        self._refresh_home_choices()

    def _refresh_home_choices(self):
        if not hasattr(self, "home_version") or not self.home_version.winfo_exists():
            return
        versions = self.manifest.get("versions", [])
        latest = self.manifest.get("latest", {})
        ids = [v["id"] for v in versions]
        choices = [f"latest release ({latest.get('release', '…')})", f"latest snapshot ({latest.get('snapshot', '…')})"] + ids
        self.home_version["values"] = choices
        if self.selected_version in choices:
            self.home_version.set(self.selected_version)
        else:
            self.home_version.set(choices[0] if choices else "")
        self.home_profile["values"] = [p["name"] for p in self.profiles.all()]
        self.home_profile.set(self.selected_profile)
        self._actual_version(self.home_version.get(), lambda actual: self.home_status.configure(text=f"Ausgewählt: {actual} • {'Installiert' if (self.mc_root / 'versions' / actual / f'{actual}.jar').exists() else 'Noch nicht installiert'}") if self.home_status.winfo_exists() else None)

    def _actual_version(self, value, callback):
        if value.startswith("latest release"):
            value = self.manifest.get("latest", {}).get("release", "")
        elif value.startswith("latest snapshot"):
            value = self.manifest.get("latest", {}).get("snapshot", "")
        if value:
            callback(value)

    def _selected_version_id(self):
        value = self.home_version.get() if hasattr(self, "home_version") else self.selected_version
        return (self.manifest.get("latest", {}).get("release", "") if value.startswith("latest release") else
                self.manifest.get("latest", {}).get("snapshot", "") if value.startswith("latest snapshot") else value)

    def install_selected(self):
        selected = self.versions_tree.selection() if hasattr(self, "versions_tree") else []
        if not selected:
            return
        version_id = selected[0]
        self._run_background(lambda: self.mc.install(version_id, self._set_status), f"Minecraft {version_id} installiert.")

    def launch_game(self):
        version_id = self._selected_version_id()
        if not version_id:
            messagebox.showerror("Version fehlt", "Die Versionsliste wird noch geladen.")
            return
        if not (self.mc_root / "versions" / version_id / f"{version_id}.jar").exists():
            if messagebox.askyesno("Installation erforderlich", f"Minecraft {version_id} ist noch nicht installiert. Jetzt installieren?"):
                self._run_background(lambda: self.mc.install(version_id, self._set_status), "Installation abgeschlossen. Du kannst jetzt auf Spielen klicken.")
            return
        profile = self.selected_profile
        ram = int(self.config.get("ram_gb", self.ram))
        java = self.config.get("java_path") or None
        try:
            if self.proc and self.proc.poll() is None:
                messagebox.showinfo("Spiel läuft", "Minecraft läuft bereits.")
                return
            game_dir = self.mc_root / "instances" / version_id
            self.proc = self.mc.launch(version_id, profile, ram, java, game_dir)
            self._set_status(f"Minecraft {version_id} gestartet als {profile}")
            self.window.after(3000, self._poll_game)
        except Exception as exc:
            self._show_error(str(exc))

    def add_profile(self):
        name = self._prompt("Neues Offline-Profil", "Spielername (3–16 Zeichen, Buchstaben/Ziffern/_):")
        if not name:
            return
        if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", name):
            messagebox.showerror("Ungültiger Name", "Der Name muss 3–16 Zeichen lang sein und darf Buchstaben, Zahlen und _ enthalten.")
            return
        profiles = self.profiles.all()
        if any(p["name"].lower() == name.lower() for p in profiles):
            messagebox.showerror("Profil vorhanden", "Dieser Spielername ist bereits gespeichert.")
            return
        profiles.append({"name": name, "uuid": None})
        self.profiles.save(profiles)
        self.refresh_profiles()
        self._refresh_home_choices()

    def remove_profile(self):
        sel = self.account_list.curselection()
        if not sel:
            return
        name = self.account_list.get(sel[0]).split("  •")[0]
        profiles = [p for p in self.profiles.all() if p["name"] != name]
        if not profiles:
            messagebox.showinfo("Profil benötigt", "Mindestens ein lokales Profil muss vorhanden sein.")
            return
        self.profiles.save(profiles)
        if self.selected_profile == name:
            self.selected_profile = profiles[0]["name"]
        self.refresh_profiles()
        self._refresh_home_choices()

    def set_profile(self):
        sel = self.account_list.curselection()
        if sel:
            self.selected_profile = self.account_list.get(sel[0]).split("  •")[0]
            self.config["profile"] = self.selected_profile
            self._save_config()
            self._refresh_home_choices()

    def refresh_profiles(self):
        if not hasattr(self, "account_list"):
            return
        self.account_list.delete(0, "end")
        for profile in self.profiles.all():
            mark = "  • aktiv" if profile["name"] == self.selected_profile else ""
            self.account_list.insert("end", profile["name"] + mark)

    def _profile_changed(self, name):
        self.selected_profile = name
        self.config["profile"] = name
        self._save_config()

    def _refresh_mod_versions(self):
        if not hasattr(self, "mods_version") or not self.mods_version.winfo_exists():
            return
        vals = [p.name for p in (self.mc_root / "instances").iterdir() if p.is_dir()] if (self.mc_root / "instances").exists() else []
        self.mods_version["values"] = vals
        if vals:
            self.mods_version.set(vals[0])
            self.refresh_mods()

    def refresh_mods(self):
        self.mods_list.delete(0, "end")
        path = self.mc_root / "instances" / self.mods_version.get() / "mods"
        path.mkdir(parents=True, exist_ok=True)
        for mod in sorted(path.glob("*.jar")):
            self.mods_list.insert("end", mod.name)

    def add_mod(self):
        files = filedialog.askopenfilenames(title="Mod-JARs auswählen", filetypes=[("Java Archive", "*.jar")])
        dest = self.mc_root / "instances" / self.mods_version.get() / "mods"
        dest.mkdir(parents=True, exist_ok=True)
        for file in files:
            source = Path(file)
            if source.stat().st_size > 250 * 1024 * 1024:
                messagebox.showerror("Datei zu groß", f"{source.name} überschreitet 250 MB.")
                continue
            (dest / source.name).write_bytes(source.read_bytes())
        self.refresh_mods()

    def remove_mod(self):
        sel = self.mods_list.curselection()
        if sel:
            name = self.mods_list.get(sel[0])
            (self.mc_root / "instances" / self.mods_version.get() / "mods" / name).unlink(missing_ok=True)
            self.refresh_mods()

    def import_pack(self):
        archive = filedialog.askopenfilename(filetypes=[("Modrinth Modpack", "*.mrpack"), ("ZIP", "*.zip")])
        if not archive:
            return
        name = self._prompt("Instanzname", "Name der neuen Instanz:")
        if not name:
            return
        name = re.sub(r"[^A-Za-z0-9 _.-]", "", name).strip(" .")
        if not name:
            messagebox.showerror("Ungültiger Name", "Bitte einen gültigen Instanznamen eingeben.")
            return
        self._run_background(lambda: import_modrinth_pack(Path(archive), self.mc_root, name, self._set_status), f"Modpack {name} importiert.")

    def export_pack(self):
        instances = self.mc_root / "instances"
        names = [p.name for p in instances.iterdir() if p.is_dir()] if instances.exists() else []
        if not names:
            messagebox.showinfo("Keine Instanzen", "Es gibt noch keine Instanzen zum Exportieren.")
            return
        choice = self._prompt("Instanz exportieren", "Instanzname exakt eingeben:\n" + ", ".join(names))
        if not choice:
            return
        instance = instances / choice
        if not instance.is_dir():
            messagebox.showerror("Instanz nicht gefunden", "Bitte einen Namen aus der Liste eingeben.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".mrpack", filetypes=[("Modrinth Modpack", "*.mrpack")], initialfile=f"{choice}.mrpack")
        if not dest:
            return
        version = instance.name if instance.name in [v["id"] for v in self.manifest.get("versions", [])] else self._selected_version_id()
        try:
            export_modrinth_pack(instance, Path(dest), choice, version or "unknown")
            self.status_var.set(f"Exportiert: {dest}")
        except Exception as exc:
            self._show_error(str(exc))

    def save_settings(self):
        path = Path(self.setting_path.get()).expanduser()
        try:
            workers = max(1, min(16, int(self.setting_workers.get())))
            self.ram = max(2, min(16, int(self.setting_ram.get())))
            path.mkdir(parents=True, exist_ok=True)
            self.mc_root = path
            self.mc = Minecraft(path, workers)
            self.profiles = Profiles(path)
            self.config.update({"minecraft_dir": str(path), "java_path": self.setting_java.get().strip(), "ram_gb": self.ram, "parallel_downloads": workers})
            self._save_config()
            messagebox.showinfo("Gespeichert", "Einstellungen wurden gespeichert.")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Fehler", str(exc))

    def _browse_dir(self, var):
        chosen = filedialog.askdirectory(initialdir=var.get() or str(Path.home()))
        if chosen:
            var.set(chosen)

    def _browse_java(self):
        chosen = filedialog.askopenfilename(filetypes=[("Java", "java.exe" if os.name == "nt" else "java"), ("All files", "*.*")])
        if chosen:
            self.setting_java.set(chosen)

    @staticmethod
    def _prompt(title, prompt):
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.configure(bg=BG)
        dialog.transient()
        dialog.grab_set()
        tk.Label(dialog, text=prompt, bg=BG, fg=TEXT, font=("Segoe UI", 10)).pack(padx=18, pady=(16, 8))
        value = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=value, bg=PANEL2, fg=TEXT, insertbackground=TEXT, relief="flat")
        entry.pack(fill="x", padx=18, ipady=7)
        result = {"value": None}
        def done():
            result["value"] = value.get().strip()
            dialog.destroy()
        ttk.Button(dialog, text="OK", command=done).pack(anchor="e", padx=18, pady=14)
        entry.bind("<Return>", lambda _: done())
        entry.focus_set()
        dialog.wait_window()
        return result["value"]

    def _run_background(self, task, success):
        self._set_status("Arbeite …")
        def work():
            try:
                task()
                self.window.after(0, lambda: self._task_done(success))
            except Exception as exc:
                self.window.after(0, lambda error=str(exc): self._show_error(error))
        threading.Thread(target=work, daemon=True).start()

    def _task_done(self, message):
        self._set_status(message)
        if self.current_page == "Versions" and hasattr(self, "versions_tree"):
            self._filter_versions()
        self._refresh_mod_versions()
        self._refresh_home_choices()

    def _poll_game(self):
        if self.proc is None:
            return
        code = self.proc.poll()
        if code is None:
            self.window.after(3000, self._poll_game)
        else:
            self._set_status(f"Minecraft beendet (Code {code}). Ausgabe: {self.mc_root / 'logs' / 'latest-game.log'}")

    def _set_status(self, message):
        self.window.after(0, lambda: self.status_var.set(message))
        if hasattr(self, "versions_status") and self.current_page == "Versions":
            self.window.after(0, lambda: self.versions_status.set(message))

    def _show_error(self, message):
        self.status_var.set("Fehler")
        messagebox.showerror("Block Launcher", message)

    def _save_config(self):
        self.config["profile"] = self.selected_profile
        self.config["version"] = self.selected_version
        write_json(self.config_path, self.config)


def main():
    log_file = default_root() / "logs" / "launcher.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=str(log_file),
                        format="%(asctime)s %(levelname)s %(message)s")
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()

