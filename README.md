# Block Launcher

Ein schlanker Minecraft-Java-Launcher in Python mit dunkler Desktop-Oberfläche. Er nutzt ausschließlich die offiziellen Mojang-Versionsmetadaten und benötigt keine zusätzlichen Python-Pakete.

## Voraussetzungen

- Python 3.10 oder neuer
- Java für Minecraft (die benötigte Version steht in den Mojang-Metadaten; ältere und aktuelle Minecraft-Versionen benötigen unterschiedliche Java-Versionen)
- Internetzugang für Versionslisten und Downloads

## Start unter Windows

`start.bat` doppelklicken oder im Projektordner ausführen:

```powershell
python main.py
```

## Start unter Linux/macOS

```sh
python3 main.py
```

Optional installierbar als Python-Anwendung:

```sh
python -m pip install .
block-launcher
```

## Funktionen

- Mojang-Versionsmanifest mit Release-, Snapshot-, alten Beta- und Alpha-Versionen
- parallele Minecraft-, Library- und Asset-Downloads mit SHA-1-Prüfung
- Minecraft-Installationen und Start mit den versionsspezifischen offiziellen JVM- und Spielargumenten
- lokale Offline-Spielerprofile
- RAM-Einstellung, Java-Pfadauswahl und Auffinden von Java
- Modrinth-Suche nach Minecraft-Version und Modloader mit Ein-Klick-Installation passender Mods und erforderlicher Abhängigkeiten
- SHA-1/SHA-512-Prüfung von Modrinth-Dateien sowie lokale JAR-Verwaltung in `instances/<version>/mods`
- Bei kleinen Fenstern kompakte Navigation, scrollbarer Inhaltsbereich und flexible Tabellenbreiten
- Import und Export von Modrinth-`.mrpack`-Archiven mit Overrides
- Spielausgabe in `logs/latest-game.log`

Minecraft-Daten werden unter Windows standardmäßig in `%APPDATA%\.minecraft\PythonLauncher`, unter macOS in `~/Library/Application Support/minecraft` und unter Linux in `~/.local/share/minecraft` gespeichert. Launcher-Einstellungen liegen in `~/.block-launcher/settings.json`.

## Hinweise zu Grenzen

Offline-Profile melden sich nicht bei Microsoft an und eignen sich nur für Einzelspieler oder Server ohne Online-Authentifizierung. Microsoft-Konten und sichere Token-Speicherung sind nicht implementiert. Fabric/Forge/NeoForge/Quilt-Installer, CurseForge-API-Modpacks und Newsfeed-Integration sind ebenfalls nicht enthalten. Modrinth-Mods werden passend zu gewählter Minecraft-Version und Loader gesucht und installiert; zum Laden der Mods muss die Installation bereits den passenden Modloader enthalten. Der Launcher lädt und startet offizielle Vanilla-Versionen.

## Projektstruktur

```text
mc_launcher/
  app.py       Tkinter-Oberfläche
  core.py      Mojang-Metadaten, Downloads, Java und Startprozess
  modrinth.py  Modrinth-Suche, Kompatibilitätsfilter und Mod-Downloads
  packs.py     Modrinth-Archiv Import/Export
  webui.py     Responsive Browser-Oberfläche als Tkinter-Fallback
main.py        Programmeinstieg
```
