"""
VimeoTools package exposes lightweight helpers with lazy imports.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "deepgramTranscriber",
    "videoDownloader",
    "download_video",
    "fetch_metadata_as_string",
    "transcribe_audio",
]


def __getattr__(name: str) -> Any:
    """Lazily load heavy submodules on first access."""
    if name in {"deepgramTranscriber", "videoDownloader"}:
        module = import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    if name in {"download_video", "fetch_metadata_as_string"}:
        module = import_module(".videoDownloader", __name__)
        for attr in ("download_video", "fetch_metadata_as_string"):
            globals()[attr] = getattr(module, attr)
        return globals()[name]
    if name == "transcribe_audio":
        module = import_module(".deepgramTranscriber", __name__)
        globals()["transcribe_audio"] = getattr(module, "transcribe_audio")
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
