"""What to attach to a re-run: machine, Python packages, and the exact model file and compose used.

    python3 tools/env_report.py [path/to/model.gguf]
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import os
import platform
import sys
from pathlib import Path
from typing import List

PACKAGES = ("model-compose", "llama-cpp-python", "torch", "huggingface-hub")
SETTINGS = ("LLM_REPO", "LLM_GGUF", "LLM_REVISION", "LLM_N_CTX", "LLM_PRESENCE_PENALTY", "LLM_MIN_P")
HERE = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def package_lines() -> List[str]:
    lines = []
    for name in PACKAGES:
        try:
            lines.append(f"{name}: {importlib.metadata.version(name)}")
        except importlib.metadata.PackageNotFoundError:
            lines.append(f"{name}: not installed")
    return lines


def machine_lines() -> List[str]:
    return [f"os: {platform.platform()}", f"machine: {platform.machine()}", f"processor: {platform.processor()}",
            f"cpus: {os.cpu_count()}", f"python: {sys.version.split()[0]}"]


def setting_lines() -> List[str]:
    env = dict(line.split("=", 1) for line in env_file_lines() if "=" in line)
    return [f"{name}: {os.environ.get(name, env.get(name, '(compose default)'))}" for name in SETTINGS]


def env_file_lines() -> List[str]:
    path = HERE / ".env"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def main(argv: List[str]) -> int:
    lines = machine_lines() + package_lines() + setting_lines()
    lines.append(f"compose sha256: {sha256(HERE / 'model-compose.yml')}")
    lines += [f"model sha256: {sha256(Path(path))}  {path}" for path in argv]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
