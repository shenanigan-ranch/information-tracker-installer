# Shenanigan Ranch Installer

This repository contains the Windows installer for Shenanigan Ranch Information Tracker. The installer downloads the app directly from GitHub, creates shortcuts, and registers an uninstall entry in Windows Apps settings for the current user.

## Requirements

- Windows only.
- A GitHub Personal Access Token for the repository owner account.
- Python 3 with these packages installed if you want to run the script directly:
	- `requests`
	- `pywin32`
	- `pyinstaller` only if you want to build the `.exe`

## What The Installer Does

- Install mode downloads the latest app files from GitHub into your roaming AppData folder.
- Repair mode re-downloads the app files without requiring a manual uninstall.
- Uninstall mode removes the installed files, desktop shortcut, Start Menu shortcut, startup shortcut, and Windows Apps entry.
- Startup shortcut behavior is enforced on every install or repair run:
	- If enabled, the startup shortcut is created or updated.
	- If disabled, any existing startup shortcut is removed.
- The installer writes an uninstall entry into Windows Apps settings for the current user.

## Using The Installer

### GUI Mode

Run the installer normally to open the Windows interface.

In the app window:

1. Enter an optional install folder name. If you leave it blank, the default folder name is used.
2. Enter your GitHub Personal Access Token.
3. Choose whether the app should run on startup.
4. Click one of the action buttons:
	 - Install: downloads the app and sets it up for the first time.
	 - Repair: downloads the app again and refreshes the installed files.
	 - Uninstall: removes the app and its shortcuts after confirmation.

The token is stored in your current user environment so you do not have to re-enter it every time.

### Command-Line Uninstall

The installer also supports unattended uninstall from the command line:

```powershell
ShenaniganRanchInstaller.exe --uninstall --yes
```

Optional arguments:

- `--install-name <name>`: targets a specific install folder and shortcut name.
- `--yes`: required for unattended uninstall.

Example:

```powershell
ShenaniganRanchInstaller.exe --uninstall --install-name "MyCustomInstall" --yes
```

## Building The Installer

Use `build.bat` to create the packaged executable with PyInstaller.

```powershell
build.bat
```

The output executable is written to `dist\ShenaniganRanchInstaller.exe`.

## Windows Apps Uninstall Entry

The installer stores its uninstall registration under:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ShenaniganRanchInformationTracker_<install_name>
```

That entry points to the same uninstall command used by the command-line flow above.
