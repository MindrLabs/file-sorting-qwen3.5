"""The dev folders come back byte for byte from their designs, and staging never empties a folder it did not make."""
from fixtures import run_tests, scratch_root

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure.folders import DESIGNS, differing, folder_names, hash_tree, project_lines, rebuild  # noqa: E402
from measure.generator import answers, to_design  # noqa: E402
from measure.workspace import MARKER, NotStageable, stage, tree  # noqa: E402


def refused(root: Path) -> bool:
    try:
        stage(root, "dev-01")
    except NotStageable:
        return True
    return False


def test_there_are_twelve_dev_folders():
    assert folder_names() == [f"dev-{number:02d}" for number in range(1, 13)]


def test_an_english_and_a_korean_folder_rebuild_byte_for_byte():
    out = scratch_root({})
    assert rebuild(out, "dev-01") == [] and rebuild(out, "dev-02") == []
    assert (out / "dev-02" / "files").is_dir()


def test_a_changed_byte_is_named():
    out = scratch_root({})
    rebuild(out, "dev-03")
    files = out / "dev-03" / "files"
    changed = sorted(files.rglob("*.txt"))[0]
    changed.write_bytes(changed.read_bytes() + b" ")
    assert differing("dev-03", hash_tree(files)) == [changed.relative_to(files).as_posix()]


def test_the_labels_follow_from_each_design():
    for folder in folder_names():
        record = json.loads((DESIGNS / folder / "design.json").read_text(encoding="utf-8"))
        labelled = json.loads((DESIGNS / folder / "answers.json").read_text(encoding="utf-8"))
        assert answers(to_design(record["design"], record["language"]), labelled["note"]) == labelled, folder


def test_the_project_list_names_every_labelled_project_with_the_descriptions_it_has():
    lines = project_lines("dev-01").splitlines()
    assert [line.split(":")[0] for line in lines] == ["bank-closures", "maple-street-sale", "solo-cooking", "survivor-pension"]
    assert lines[0].startswith("bank-closures: Closing a late relative's bank accounts:") and lines[2] == "solo-cooking"


def test_staging_fills_an_empty_folder_and_restages_its_own():
    root = scratch_root({}) / "workspace"
    stage(root, "dev-01")
    assert (root / MARKER).is_file() and differing("dev-01", tree(root)) == []
    (root / "stray.txt").write_text("left by a run", encoding="utf-8")
    stage(root, "dev-02")
    assert not (root / "stray.txt").exists() and differing("dev-02", tree(root)) == []


def test_staging_refuses_a_folder_it_did_not_make():
    assert refused(scratch_root({"my-notes.txt": "keep me"}))
    linked = scratch_root({}) / "link"
    os.symlink(scratch_root({}), linked)
    assert refused(linked)


run_tests(globals())
