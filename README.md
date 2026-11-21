# Block Launcher

A Minecraft: Java Edition launcher written in Python. The Windows launcher opens a responsive desktop window with an embedded web interface; it does not open a separate browser.

[English](#english) · [Deutsch](#deutsch)

## English

### Features

- Browse Mojang releases, snapshots, and older Java Edition versions.
- Install Minecraft files and launch installed versions.
- Manage local offline player profiles.
- Search Modrinth for mods compatible with a selected Minecraft version and Fabric or Quilt.
- Install a mod and its required dependencies with one click. Fabric or Quilt is set up automatically, and the matching profile is selected for launch.
- Manage local mod JAR files and view Modrinth project icons.
- Watch launch status and live game output in the built-in Terminal page.
- Configure the Minecraft data directory, Java executable, and memory allocation.
- Import and export Modrinth `.mrpack` files in the native Tkinter interface.

### Requirements

- Windows 10 or later for the included `start.bat` workflow.
- Python 3.10 or later, with `python` available on `PATH`.
- Java installed. Minecraft releases can require different Java versions; use the Java path setting if Java is not available on `PATH`.
- An internet connection for version metadata, game files, libraries, assets, and Modrinth.
- The WebView2 Runtime for the embedded Windows interface. `start.bat` installs the Python `pywebview` package when it is missing.

### Run on Windows

Double-click `start.bat`. On the first run, it installs `pywebview` if needed, then opens Block Launcher in its own desktop window. Internet access is required for that first-time package installation.

To use the native Tkinter interface instead, run this from the project directory:

```powershell
python main.py
```

### Run from Python or install as a package

Install the project and its Python dependencies:

```powershell
python -m pip install .
```

Open the embedded interface:

```powershell
python main.py --browser
```

Open the native Tkinter interface:

```powershell
python main.py
```

On Linux and macOS, the native interface can be started with `python3 main.py`. The embedded interface may require a platform-specific `pywebview` GUI backend.

### Mods

Choose a Minecraft version and Fabric or Quilt in **Mods**, search Modrinth, then install a result. The launcher installs the loader profile and required mod dependencies. Choose that loader profile on the Home page to launch the instance.

Only Fabric and Quilt are set up automatically. Forge and NeoForge installation are not currently supported. A mod must support the selected Minecraft version and loader. The launcher verifies Modrinth downloads against the hashes provided by Modrinth.

### Data and logs

- Windows Minecraft data: `%APPDATA%\.minecraft\PythonLauncher`
- macOS Minecraft data: `~/Library/Application Support/minecraft`
- Linux Minecraft data: `${XDG_DATA_HOME:-~/.local/share}/minecraft`
- Launcher settings: `~/.block-launcher/settings.json`
- Game output: `<minecraft-data-directory>/logs/latest-game.log`
- Launcher log: `<minecraft-data-directory>/logs/launcher.log`

### Limitations

Player profiles are offline profiles. Microsoft account authentication and online session tokens are not implemented, so these profiles are intended for single-player and servers that allow offline-mode connections. Minecraft and Java are not bundled with the launcher.

## Deutsch

### Funktionen

- Mojang-Versionen durchsuchen: Releases, Snapshots und ältere Java-Edition-Versionen.
- Minecraft-Dateien installieren und installierte Versionen starten.
- Lokale Offline-Spielerprofile verwalten.
- Modrinth nach Mods für eine ausgewählte Minecraft-Version sowie Fabric oder Quilt durchsuchen.
- Mods und erforderliche Abhängigkeiten mit einem Klick installieren. Fabric oder Quilt wird automatisch eingerichtet und das passende Startprofil ausgewählt.
- Lokale Mod-JARs verwalten und Modrinth-Projekt-Icons anzeigen.
- Startstatus und Live-Spielausgabe im integrierten Terminal ansehen.
- Minecraft-Datenordner, Java-Pfad und Arbeitsspeicher einstellen.
- Modrinth-`.mrpack`-Dateien in der nativen Tkinter-Oberfläche importieren und exportieren.

### Voraussetzungen

- Windows 10 oder neuer für den Start über `start.bat`.
- Python 3.10 oder neuer; der Befehl `python` muss über `PATH` verfügbar sein.
- Eine installierte Java-Version. Verschiedene Minecraft-Versionen benötigen unterschiedliche Java-Versionen. Falls Java nicht über `PATH` gefunden wird, den Java-Pfad in den Einstellungen angeben.
- Internetverbindung für Versionsdaten, Spieldateien, Bibliotheken, Assets und Modrinth.
- Für das eingebettete Windows-Fenster wird die WebView2 Runtime benötigt. `start.bat` installiert das Python-Paket `pywebview`, falls es noch fehlt.

### Start unter Windows

`start.bat` doppelklicken. Beim ersten Start installiert die Datei bei Bedarf `pywebview` und öffnet den Launcher anschließend in einem eigenen Desktop-Fenster. Für die erstmalige Paketinstallation ist eine Internetverbindung erforderlich.

Die native Tkinter-Oberfläche lässt sich stattdessen im Projektordner so starten:

```powershell
python main.py
```

### Aus Python starten oder als Paket installieren

Projekt und Python-Abhängigkeiten installieren:

```powershell
python -m pip install .
```

Eingebettete Oberfläche starten:

```powershell
python main.py --browser
```

Native Tkinter-Oberfläche starten:

```powershell
python main.py
```

Unter Linux und macOS kann die native Oberfläche mit `python3 main.py` gestartet werden. Für die eingebettete Oberfläche kann ein plattformspezifisches `pywebview`-GUI-Backend erforderlich sein.

### Mods

Unter **Mods** Minecraft-Version und Fabric oder Quilt wählen, Modrinth durchsuchen und ein Ergebnis installieren. Der Launcher richtet das Loader-Profil ein und installiert erforderliche Mod-Abhängigkeiten. Auf der Startseite anschließend das passende Loader-Profil zum Spielen auswählen.

Automatisch eingerichtet werden derzeit nur Fabric und Quilt. Forge und NeoForge werden nicht unterstützt. Ein Mod muss zur gewählten Minecraft-Version und zum ausgewählten Loader passen. Modrinth-Downloads werden anhand der von Modrinth angegebenen Prüfsummen überprüft.

### Daten und Protokolle

- Minecraft-Daten unter Windows: `%APPDATA%\.minecraft\PythonLauncher`
- Minecraft-Daten unter macOS: `~/Library/Application Support/minecraft`
- Minecraft-Daten unter Linux: `${XDG_DATA_HOME:-~/.local/share}/minecraft`
- Launcher-Einstellungen: `~/.block-launcher/settings.json`
- Spielausgabe: `<Minecraft-Datenordner>/logs/latest-game.log`
- Launcher-Protokoll: `<Minecraft-Datenordner>/logs/launcher.log`

### Einschränkungen

Die Spielerprofile sind Offline-Profile. Microsoft-Kontoanmeldung und Online-Sitzungstokens sind nicht implementiert. Die Profile eignen sich daher für Einzelspieler und Server, die Verbindungen im Offline-Modus erlauben. Minecraft und Java sind nicht im Launcher enthalten.

## Project structure / Projektstruktur

```text
mc_launcher/
  app.py       Tkinter interface and application entry point
  core.py      Minecraft metadata, downloads, Java and process launch
  modrinth.py  Modrinth search, compatibility and downloads
  packs.py     Modrinth modpack import and export
  webui.py     Embedded desktop interface and local API
main.py        Application entry point
start.bat      Windows startup script
```
