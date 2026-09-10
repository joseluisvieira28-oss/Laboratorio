from __future__ import annotations

import os
import subprocess
import sys

GATE_F_ENV = "DREAM_GATE_F_REPLACE"
BUILD_ENV = "DREAM_BUILD_RECOVERY_CANDIDATE"
MAINTENANCE_ENV = "DREAM_FORCE_MAINTENANCE"


def truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def run_script(name: str) -> int:
    script = os.path.join(os.path.dirname(__file__), name)
    return subprocess.run([sys.executable, script], check=False).returncode


def main() -> None:
    gate_f_rc = 0
    if truthy(GATE_F_ENV):
        gate_f_rc = run_script("gate_f_replace.py")
    elif truthy(BUILD_ENV):
        run_script("recovery_bootstrap.py")

    if gate_f_rc != 0:
        os.environ[MAINTENANCE_ENV] = "1"

    os.execvp("dream-account-runtime", ["dream-account-runtime"])


if __name__ == "__main__":
    main()
