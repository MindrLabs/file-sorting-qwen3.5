"""The re-run report names the machine, the measured packages, the settings and the compose's hash."""
from fixtures import run_tests, scratch_root

from env_report import PACKAGES, main, package_lines, sha256


def test_every_measured_package_is_listed_installed_or_not():
    assert [line.split(":")[0] for line in package_lines()] == list(PACKAGES)


def test_files_are_hashed_whole():
    root = scratch_root({"model.gguf": "abc"})
    assert sha256(root / "model.gguf") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert main([str(root / "model.gguf")]) == 0


run_tests(globals())
