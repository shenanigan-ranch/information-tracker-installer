# information-tracker-installer
Installer for the shenanigan-ranch information tracker app. Made using Python. 

## Features
- Install mode downloads and refreshes app files from GitHub.
- Repair mode re-downloads app files without requiring manual uninstall.
- Uninstall mode removes installed files and desktop/startup shortcuts.
- Startup shortcut behavior is enforced on each install/repair run:
	- Enabled: startup shortcut is created/updated.
	- Disabled: existing startup shortcut is removed.
- Installer registers an uninstall entry in Windows Apps settings (Current User).

## Windows Apps Uninstall Command
The installer writes an uninstall command into:
- `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ShenaniganRanchInformationTracker_<install_name>`

That command runs installer uninstall mode in unattended mode:
- `--uninstall --install-name <name> --yes`
