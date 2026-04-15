import os
import re
import shutil
import sys
import threading
import tkinter as tk
import winreg
import argparse
from tkinter import messagebox
from tkinter import ttk

import requests
import pythoncom
import win32com.client

OWNER = "shenanigan-ranch"
USERNAME = "PrestonCurtis1"
REPO = "information-tracker"
URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/"
ENTRY_POINT = "shenanigan-ranch.exe"
SHORTCUT_NAME = "shenanigan-ranch.lnk"
INFO_TEXT = (
    "Installer for Shenanigan Ranches Information Tracker APP\n\n"
    "Your access token is like a password/product key. It allows this installer to access GitHub on your behalf to download the necessary files. the access token is read-only\n"
    "Your access token is likely in your email somewhere. search for shenanigan ranch access token. it will be used to authenticate with GitHub\n"
    "if you want to install on linux i recommend not using this installer and just using git clone instead. the username will be \"PrestonCurtis1\" and the password will be the access token.\n"
    "We ask that you do not share your access token with untrusted parties, or post it publicly, as this is a paid application and your token is tied to your purchase.\n"
    "If you believe your token has been compromised, please contact us immediately so we can revoke it and issue a new one.\n"
    "if you do not know or do not have a token, or experience any issues with the installation, please contact us\n"
    "if you are a new customer who would like to purchase an access token. Please contact us for purchasing information.\n"
    "Phone: (435) 255-8607 Email:bill@shenaniganranch.com Website:https://site.shenaniganranch.com/contact.html"
)
ACCESS_TOKEN_ENV_VAR = "ShenaniganRanchInformationTrackerAccessToken"
APP_DISPLAY_NAME = "Shenanigan Ranch Information Tracker"
APP_PUBLISHER = "Shenanigan Ranch"
UNINSTALL_ROOT = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"


def github_headers(token):
    headers = {"Accept": "application/vnd.github+json"}
    return headers


def github_request_kwargs(token):
    request_kwargs = {"headers": github_headers(token)}
    if token:
        # Authenticate as the PAT owner when accessing an org-owned repository.
        request_kwargs["auth"] = (USERNAME, token)
    return request_kwargs


def store_access_token_env(token):
    # Keep the token available to this process and persist for future launches.
    os.environ[ACCESS_TOKEN_ENV_VAR] = token
    os.putenv(ACCESS_TOKEN_ENV_VAR, token)
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Environment",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, ACCESS_TOKEN_ENV_VAR, 0, winreg.REG_SZ, token)


def load_access_token_env():
    token = os.environ.get(ACCESS_TOKEN_ENV_VAR, "").strip()
    if token:
        return token

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            stored_value, _ = winreg.QueryValueEx(key, ACCESS_TOKEN_ENV_VAR)
            return str(stored_value or "").strip()
    except OSError:
        return ""


def create_shortcut(target_path, shortcut_path, start_in):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.WorkingDirectory = start_in
    shortcut.Save()


def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def normalize_install_name(name):
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        return REPO

    cleaned_name = re.sub(r'[<>:"/\\|?*]+', "_", cleaned_name).strip(" .")
    return cleaned_name or REPO


def shortcut_name_for_install(install_name):
    if install_name == REPO:
        return SHORTCUT_NAME
    cleaned_name = (install_name or "").strip()
    if not cleaned_name:
        return SHORTCUT_NAME

    cleaned_name = re.sub(r'[<>:"/\\|?*]+', "_", cleaned_name).strip(" .")
    if not cleaned_name:
        return SHORTCUT_NAME

    return f"{cleaned_name}.lnk"


def get_roaming_appdata():
    # Try to get the real AppData from registry to bypass Store Python sandboxing
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            appdata_path = winreg.QueryValueEx(key, "AppData")[0]
            return appdata_path
    except Exception:
        pass
    
    # Fallback: use environment variable
    return os.environ.get("APPDATA", "")


def get_special_folder(name):
    shell = win32com.client.Dispatch("WScript.Shell")
    return shell.SpecialFolders(name)


def uninstall_registry_key_name(install_name):
    install_folder_name = normalize_install_name(install_name)
    return f"ShenaniganRanchInformationTracker_{install_folder_name}"


def build_uninstall_command(install_name):
    normalized_name = normalize_install_name(install_name)
    if getattr(sys, "frozen", False):
        exe_path = os.path.abspath(sys.executable)
        return f'"{exe_path}" --uninstall --install-name "{normalized_name}" --yes'

    python_exe = os.path.abspath(sys.executable)
    script_path = os.path.abspath(__file__)
    return f'"{python_exe}" "{script_path}" --uninstall --install-name "{normalized_name}" --yes'


def register_uninstall_entry(install_name, install_location):
    key_name = uninstall_registry_key_name(install_name)
    display_name = APP_DISPLAY_NAME
    normalized_name = normalize_install_name(install_name)
    if normalized_name != REPO:
        display_name = f"{APP_DISPLAY_NAME} ({normalized_name})"

    uninstall_string = build_uninstall_command(install_name)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{UNINSTALL_ROOT}\\{key_name}") as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, display_name)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_location)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_string)
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, uninstall_string)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 0)


def remove_uninstall_entry(install_name):
    key_name = uninstall_registry_key_name(install_name)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{UNINSTALL_ROOT}\\{key_name}")
        return True
    except FileNotFoundError:
        return False


def fetch_repo_contents(contents_url, token):
    response = requests.get(contents_url, timeout=30, **github_request_kwargs(token))
    if response.status_code != 200:
        raise requests.RequestException(
            f"Failed to retrieve repository contents: {contents_url} {response.status_code}"
        )
    return response.json()


def collect_repo_stats(contents_url, token):
    items = fetch_repo_contents(contents_url, token)
    total_bytes = 0
    file_count = 0

    for item in items:
        item_type = item.get("type", "unknown")
        if item_type == "file":
            total_bytes += int(item.get("size", 0) or 0)
            file_count += 1
        elif item_type == "dir":
            child_bytes, child_files = collect_repo_stats(item["url"], token)
            total_bytes += child_bytes
            file_count += child_files

    return total_bytes, file_count


def run_install(token, install_name, log, status, progress, run_on_startup=True, mode="install"):
    mode_label = "Repair" if mode == "repair" else "Installation"
    appdata = get_roaming_appdata()
    print(f"Roaming AppData directory: {appdata}")
    install_folder_name = normalize_install_name(install_name)
    shortcut_file_name = shortcut_name_for_install(install_name)
    target_dir = os.path.join(appdata, install_folder_name)
    print(f"Target installation directory: {target_dir}")
    log(f"Install directory: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    try:
        total_repo_bytes, total_files = collect_repo_stats(URL, token)
        log("Successfully retrieved repository contents.")
        log(f"Repository contains {total_files} files.")
    except requests.RequestException as err:
        log(str(err))
        status(f"{mode_label} failed")
        return False

    processed_files = 0
    downloaded_repo_bytes = 0

    def download_items(contents_url, destination_dir):
        nonlocal processed_files, downloaded_repo_bytes

        items = fetch_repo_contents(contents_url, token)
        for item in items:
            name = item.get("name", "(unnamed)")
            item_type = item.get("type", "unknown")
            log(f"Processing item: {name} (type: {item_type})")

            if item_type == "dir":
                nested_dir = os.path.join(destination_dir, name)
                os.makedirs(nested_dir, exist_ok=True)
                log(f"Creating directory: {nested_dir}")
                download_items(item["url"], nested_dir)
                continue

            if item_type != "file":
                log(f"Skipping non-file item: {name} (type: {item_type})")
                continue

            file_path = os.path.join(destination_dir, name)
            status(f"Starting download: {name}")
            download = requests.get(
                item["download_url"],
                timeout=30,
                stream=True,
                **github_request_kwargs(token),
            )
            if download.status_code == 200:
                temp_path = f"{file_path}.download"
                with open(temp_path, "wb") as file_obj:
                    for chunk in download.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        file_obj.write(chunk)
                        downloaded_repo_bytes += len(chunk)
                        if total_repo_bytes > 0:
                            overall_percent = (downloaded_repo_bytes / total_repo_bytes) * 100
                            status(
                                f"{downloaded_repo_bytes} out of {total_repo_bytes} bytes downloaded ({overall_percent:.1f}%)"
                            )
                            progress(min(100, int(overall_percent)))
                        else:
                            status(f"{downloaded_repo_bytes} bytes downloaded")

                try:
                    os.replace(temp_path, file_path)
                except PermissionError as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    error_msg = f"Permission denied while updating {name}. Close the app if it is running and try again."
                    log(error_msg)
                    status(f"Permission denied: {name}")
                    raise PermissionError(error_msg) from e

                log(f"Finished downloading: {name}")
            else:
                log(f"Failed to download {name}: HTTP {download.status_code}")
                log(f"Response Content: {download.content}")

            processed_files += 1
            if total_repo_bytes <= 0:
                progress(min(100, int((processed_files / max(1, total_files)) * 100)))

        return True

    if not download_items(URL, target_dir):
        return False

    appdata = get_roaming_appdata()
    install_folder_name = normalize_install_name(install_name)
    shortcut_file_name = shortcut_name_for_install(install_name)
    target_path = os.path.join(appdata, install_folder_name, ENTRY_POINT)
    
    # Create desktop shortcut
    desktop_folder = get_special_folder("Desktop")
    desktop_shortcut_path = os.path.join(desktop_folder, shortcut_file_name)
    create_shortcut(target_path, desktop_shortcut_path, os.path.join(appdata, install_folder_name))
    log(f"Desktop shortcut created at: {desktop_shortcut_path}")

    # Create Start Menu shortcut so Windows search can discover the app.
    programs_folder = get_special_folder("Programs")
    start_menu_shortcut_path = os.path.join(programs_folder, shortcut_file_name)
    create_shortcut(target_path, start_menu_shortcut_path, os.path.join(appdata, install_folder_name))
    log(f"Start Menu shortcut created at: {start_menu_shortcut_path}")
    
    # Enforce startup shortcut preference every run.
    startup_folder = get_special_folder("Startup")
    startup_shortcut_path = os.path.join(startup_folder, shortcut_file_name)
    if run_on_startup:
        create_shortcut(target_path, startup_shortcut_path, os.path.join(appdata, install_folder_name))
        log(f"Startup shortcut created at: {startup_shortcut_path}")
    else:
        if remove_file_if_exists(startup_shortcut_path):
            log(f"Startup shortcut removed at: {startup_shortcut_path}")
        else:
            log("Startup shortcut not created (disabled by user)")

    register_uninstall_entry(install_name, target_dir)
    log("Registered app in Windows Apps settings.")

    if total_repo_bytes > 0:
        log(f"Project download total: {downloaded_repo_bytes} out of {total_repo_bytes} bytes downloaded (100.0%)")
    else:
        log(f"Project download total: {downloaded_repo_bytes} bytes downloaded")

    progress(100)
    status(f"{mode_label} completed")
    return True


def run_uninstall(install_name, log, status, progress):
    appdata = get_roaming_appdata()
    install_folder_name = normalize_install_name(install_name)
    shortcut_file_name = shortcut_name_for_install(install_name)
    target_dir = os.path.join(appdata, install_folder_name)

    status("Uninstalling...")
    progress(10)

    desktop_folder = get_special_folder("Desktop")
    startup_folder = get_special_folder("Startup")
    programs_folder = get_special_folder("Programs")
    desktop_shortcut_path = os.path.join(desktop_folder, shortcut_file_name)
    startup_shortcut_path = os.path.join(startup_folder, shortcut_file_name)
    start_menu_shortcut_path = os.path.join(programs_folder, shortcut_file_name)

    if remove_file_if_exists(desktop_shortcut_path):
        log(f"Removed desktop shortcut: {desktop_shortcut_path}")
    else:
        log("Desktop shortcut not found.")

    if remove_file_if_exists(startup_shortcut_path):
        log(f"Removed startup shortcut: {startup_shortcut_path}")
    else:
        log("Startup shortcut not found.")

    if remove_file_if_exists(start_menu_shortcut_path):
        log(f"Removed Start Menu shortcut: {start_menu_shortcut_path}")
    else:
        log("Start Menu shortcut not found.")

    progress(40)

    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        log(f"Removed installation directory: {target_dir}")
    else:
        log("Installation directory not found.")

    progress(80)

    if remove_uninstall_entry(install_name):
        log("Removed app entry from Windows Apps settings.")
    else:
        log("Windows Apps entry was not found.")

    progress(100)
    status("Uninstall completed")
    return True


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{REPO} Installer")
        self.root.state('zoomed')
        self.root.minsize(620, 420)

        self.install_name_var = tk.StringVar(value=REPO)
        self.token_var = tk.StringVar(value=load_access_token_env())
        self.show_token_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.IntVar(value=0)
        self.startup_var = tk.BooleanVar(value=False)
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text=f"{REPO} Installer", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(main, text="Install, repair, or uninstall the app and manage startup shortcut behavior.")
        subtitle.pack(anchor="w", pady=(2, 14))

        ttk.Label(main, text="Install folder name (optional):").pack(anchor="w")
        ttk.Entry(main, textvariable=self.install_name_var).pack(fill=tk.X, pady=(4, 10))

        ttk.Label(main, text="GitHub Personal Access Token:").pack(anchor="w")
        self.token_entry = ttk.Entry(main, textvariable=self.token_var, show="*")
        self.token_entry.pack(fill=tk.X, pady=(4, 4))
        ttk.Checkbutton(
            main,
            text="Show access token",
            variable=self.show_token_var,
            command=self._update_token_visibility,
        ).pack(anchor="w", pady=(0, 10))

        info_frame = ttk.LabelFrame(main, text="Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = ttk.Label(info_frame, text=INFO_TEXT, justify=tk.LEFT, wraplength=640)
        info_label.pack(anchor="w")

        options_frame = ttk.LabelFrame(main, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            options_frame,
            text="Run application on startup",
            variable=self.startup_var,
        ).pack(anchor="w")

        controls = ttk.Frame(main)
        controls.pack(fill=tk.X, pady=(0, 10))

        self.install_button = ttk.Button(controls, text="Install", command=lambda: self.start_action("install"))
        self.install_button.pack(side=tk.LEFT)
        self.repair_button = ttk.Button(controls, text="Repair", command=lambda: self.start_action("repair"))
        self.repair_button.pack(side=tk.LEFT, padx=(8, 0))
        self.uninstall_button = ttk.Button(controls, text="Uninstall", command=lambda: self.start_action("uninstall"))
        self.uninstall_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Progressbar(main, variable=self.progress_var, maximum=100, mode="determinate").pack(fill=tk.X)
        ttk.Label(main, textvariable=self.status_var).pack(anchor="w", pady=(8, 8))

        self.log_widget = tk.Text(main, wrap="word", height=16, state="disabled")
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.log_widget, command=self.log_widget.yview)
        self.log_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def append_log(self, message):
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, f"{message}\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    def clear_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.configure(state="disabled")

    def set_status(self, message):
        self.status_var.set(message)

    def set_progress(self, value):
        self.progress_var.set(value)

    def _update_token_visibility(self):
        self.token_entry.configure(show="" if self.show_token_var.get() else "*")

    def start_action(self, action):
        if action == "uninstall":
            install_name = self.install_name_var.get().strip() or REPO
            confirm = messagebox.askyesno(
                "Confirm Uninstall",
                f"Uninstall '{normalize_install_name(install_name)}' and remove its shortcuts?",
            )
            if not confirm:
                return

        self.install_button.configure(state="disabled")
        self.repair_button.configure(state="disabled")
        self.uninstall_button.configure(state="disabled")
        self.set_progress(0)
        action_label = action.capitalize()
        self.set_status(f"Starting {action}...")
        self.append_log(f"Starting {action_label}...")
        worker = threading.Thread(target=self._action_worker, args=(action,), daemon=True)
        worker.start()

    def _action_worker(self, action):
        install_name = self.install_name_var.get().strip()
        token = self.token_var.get().strip()
        run_on_startup = self.startup_var.get()

        def ui_log(msg):
            self.root.after(0, self.append_log, msg)

        def ui_status(msg):
            self.root.after(0, self.set_status, msg)

        def ui_progress(value):
            self.root.after(0, self.set_progress, value)

        if action in ("install", "repair"):
            if not token:
                error_msg = "GitHub Personal Access Token is required."
                self.root.after(0, self.append_log, error_msg)
                self.root.after(0, self.set_status, f"{action.capitalize()} failed")
                self.root.after(0, messagebox.showerror, "Installer Error", error_msg)
                self.root.after(0, self._set_action_buttons_state, "normal")
                return

            store_access_token_env(token)
            self.root.after(0, self.append_log, f"Stored access token in environment variable: {ACCESS_TOKEN_ENV_VAR}")

        # win32com requires COM to be initialized in this worker thread.
        pythoncom.CoInitialize()
        try:
            if action in ("install", "repair"):
                success = run_install(
                    token,
                    install_name,
                    ui_log,
                    ui_status,
                    ui_progress,
                    run_on_startup,
                    mode=action,
                )
            else:
                success = run_uninstall(install_name, ui_log, ui_status, ui_progress)

            if success:
                self.root.after(0, messagebox.showinfo, "Installer", f"{action.capitalize()} completed successfully.")
        except requests.RequestException as err:
            error_msg = f"Network error: {err}"
            self.root.after(0, self.append_log, error_msg)
            self.root.after(0, self.set_status, f"{action.capitalize()} failed")
            self.root.after(0, messagebox.showerror, "Installation Error", error_msg)
        except Exception as err:
            error_msg = f"Unexpected error: {err}"
            self.root.after(0, self.append_log, error_msg)
            self.root.after(0, self.set_status, f"{action.capitalize()} failed")
            self.root.after(0, messagebox.showerror, "Installation Error", error_msg)
        finally:
            pythoncom.CoUninitialize()
            self.root.after(0, self._set_action_buttons_state, "normal")

    def _set_action_buttons_state(self, state):
        self.install_button.configure(state=state)
        self.repair_button.configure(state=state)
        self.uninstall_button.configure(state=state)


def parse_args():
    parser = argparse.ArgumentParser(description="Shenanigan Ranch installer")
    parser.add_argument("--uninstall", action="store_true", help="Run uninstall mode and exit")
    parser.add_argument("--install-name", default=REPO, help="Install name/folder to target")
    parser.add_argument("--yes", action="store_true", help="Run unattended without extra prompts")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.uninstall:
        if not args.yes:
            print("Refusing unattended uninstall without --yes")
            return

        def cli_log(message):
            print(message)

        def cli_status(message):
            print(message)

        def cli_progress(_value):
            return

        pythoncom.CoInitialize()
        try:
            run_uninstall(args.install_name, cli_log, cli_status, cli_progress)
        finally:
            pythoncom.CoUninitialize()
        return

    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
