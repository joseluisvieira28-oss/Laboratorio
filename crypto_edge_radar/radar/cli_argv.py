from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


def strip_exact_self_path_echo(
    argv: Iterable[str] | None = None,
    *,
    executable: str | None = None,
) -> list[str]:
    """Remove only a duplicated path to the running executable from argv.

    This is a narrow Windows/PyInstaller launcher hardening measure. It never
    ignores arbitrary unknown arguments: only an argument resolving exactly to
    the current executable path may be removed.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    exe = executable or sys.executable

    def norm(value: str) -> str:
        return os.path.normcase(os.path.abspath(os.path.expanduser(value)))

    exe_norm = norm(exe)
    cleaned: list[str] = []
    removed = False

    for arg in args:
        if not removed:
            try:
                if Path(arg).suffix.lower() == ".exe" and norm(arg) == exe_norm:
                    removed = True
                    continue
            except (OSError, TypeError, ValueError):
                pass
        cleaned.append(arg)

    return cleaned


__all__ = ["strip_exact_self_path_echo"]
