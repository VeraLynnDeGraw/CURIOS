from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from .server import run_server

URL = "http://127.0.0.1:8765"


def find_browser() -> list[str] | None:
    candidates = [
        ("firefox", ["firefox", "--no-remote", "--profile"]),
        ("chromium", ["chromium", "--user-data-dir"]),
        ("chromium-browser", ["chromium-browser", "--user-data-dir"]),
        ("google-chrome", ["google-chrome", "--user-data-dir"]),
    ]
    for executable, command in candidates:
        path = shutil.which(executable)
        if path:
            return command
    return None


def launch_browser() -> subprocess.Popen | None:
    command = find_browser()
    if not command:
        return None

    profile = Path.home() / ".local" / "share" / "curios" / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)

    if command[0] == "firefox":
        args = [*command, str(profile), "--new-window", URL]
    else:
        args = [*command, str(profile), "--no-first-run", "--new-window", URL]

    try:
        return subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return None


def main() -> None:
    browser_process = None
    print("CURIOS — local AI chat room")
    print(f"Local address: {URL}")
    print("Press Ctrl+C to shut down CURIOS and its browser session.")
    try:
        # Give the local server time to bind before opening the browser.
        import threading

        server_thread = threading.Thread(
            target=run_server,
            kwargs={"host": "127.0.0.1", "port": 8765},
            daemon=True,
        )
        server_thread.start()
        time.sleep(0.35)
        browser_process = launch_browser()
        if browser_process is None:
            print("No supported browser was launched. Open the address above manually.")
        while server_thread.is_alive():
            server_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print("\nShutting down CURIOS...")
    finally:
        if browser_process is not None and browser_process.poll() is None:
            # Terminate only the browser process group created by this CURIOS launch.
            try:
                os.killpg(browser_process.pid, signal.SIGTERM)
                browser_process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                os.killpg(browser_process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        print("CURIOS stopped.")


if __name__ == "__main__":
    main()
