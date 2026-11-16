from __future__ import annotations

import threading

_lock = threading.Lock()
_online = False


class OfflineError(PermissionError):
    """Raised when an external connection is attempted while OFFLINE."""


def is_online() -> bool:
    with _lock:
        return _online


def set_online(enabled: bool) -> None:
    global _online

    if type(enabled) is not bool:
        raise ValueError("Connection state must be true or false.")

    with _lock:
        _online = enabled


def require_online() -> None:
    if not is_online():
        raise OfflineError(
            "CURIOS is OFFLINE. Switch ONLINE before contacting a provider."
        )
