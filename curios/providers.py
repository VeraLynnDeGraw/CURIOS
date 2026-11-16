from __future__ import annotations

import json
import os
import re
import stat
import urllib.error
import urllib.request
from pathlib import Path
from .network import require_online
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "curios"
CONFIG_FILE = CONFIG_DIR / "providers.json"


def _read_config() -> list[dict[str, str]]:
    if not CONFIG_FILE.exists():
        return []
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        providers = data.get("providers", [])
        return providers if isinstance(providers, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_config(providers: list[dict[str, str]]) -> None:
    # Fail closed if the platform cannot reject symbolic links.
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("Secure configuration writing is unavailable.")

    # Secure the directory before creating or writing credentials.
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

    directory_info = CONFIG_DIR.lstat()
    if not stat.S_ISDIR(directory_info.st_mode):
        raise OSError("Configuration path must be a real directory.")

    os.chmod(CONFIG_DIR, 0o700)

    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC

    fd = os.open(CONFIG_FILE, flags, 0o600)

    try:
        file_info = os.fstat(fd)

        if not stat.S_ISREG(file_info.st_mode):
            raise OSError("Configuration path must be a regular file.")

        if file_info.st_nlink != 1:
            raise OSError("Configuration file must not have hard links.")

        # Enforce permissions before modifying file contents.
        os.fchmod(fd, 0o600)
        os.ftruncate(fd, 0)

        stream = os.fdopen(fd, "w", encoding="utf-8")
        fd = -1

        with stream:
            json.dump({"providers": providers}, stream, indent=2)

    finally:
        if fd >= 0:
            os.close(fd)


def list_providers() -> list[dict[str, str]]:
    # Never return API keys to the browser.
    return [
        {key: value for key, value in item.items() if key != "api_key"}
        for item in _read_config()
    ]


def save_provider(payload: dict[str, Any]) -> None:
    name = str(payload.get("name", "")).strip()
    base_url = str(payload.get("base_url", "")).strip().rstrip("/")
    model = str(payload.get("model", "")).strip()
    api_key = str(payload.get("api_key", "")).strip()

    if not name or not model or not base_url:
        raise ValueError("Name, base URL, and model are required.")
    if not re.match(r"^https?://", base_url, re.IGNORECASE):
        raise ValueError("Base URL must begin with http:// or https://")
    if len(name) > 60 or len(model) > 200 or len(base_url) > 500:
        raise ValueError("One or more fields are too long.")

    providers = _read_config()
    provider_id = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-") or "provider"
    existing = next((p for p in providers if p.get("id") == provider_id), None)
    record = {
        "id": provider_id,
        "name": name,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
    }
    if existing:
        providers[providers.index(existing)] = record
    else:
        providers.append(record)

    _write_config(providers)


def remove_provider(provider_id: str) -> None:
    providers = [p for p in _read_config() if p.get("id") != provider_id]
    _write_config(providers)


def chat(provider_id: str, messages: list[dict[str, str]]) -> str:
    require_online()
    provider = next((p for p in _read_config() if p.get("id") == provider_id), None)
    if not provider:
        raise ValueError("Provider not found. Add it in Connections first.")

    safe_messages = []
    for item in messages[-30:]:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        safe_messages.append({"role": role, "content": content[:12000]})

    if not safe_messages or safe_messages[-1]["role"] != "user":
        raise ValueError("A user message is required.")

    url = provider["base_url"].rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": provider["model"],
        "messages": safe_messages,
        "stream": False,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if provider.get("api_key"):
        headers["Authorization"] = "Bearer " + provider["api_key"]

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Provider returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach provider: {exc}") from exc
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Provider returned an unexpected response format.") from exc
