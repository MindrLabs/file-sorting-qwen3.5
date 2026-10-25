"""Shared helpers: a throwaway folder per test and a plain runner, no test framework needed."""
from __future__ import annotations

import atexit
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


def scratch_root(files: Dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="organizer-test-")).resolve()
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def tree(root: Path) -> Dict[str, str]:
    """Every file under root except the journal, with its text: the state a test compares."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".organizer" not in path.parts
    }


def run_tests(namespace: dict) -> None:
    tests = [value for name, value in namespace.items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"{Path(namespace['__file__']).name}: {len(tests)} passed")
