"""Turns a folder design into real files with a fixed seed, so the same bytes come out every time. Text
files carry the clue sentence where the design says; binary files are a format header and random bytes."""
from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

TEXT = {".txt", ".md", ".csv", ".json", ".py"}
CLUE_AT = {"mid": (700, 1600), "deep": (2600, 3400)}
HEADERS = {".pdf": b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n", ".jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
           ".png": b"\x89PNG\r\n\x1a\n", ".heic": b"\x00\x00\x00\x18ftypheic", ".docx": b"PK\x03\x04",
           ".xlsx": b"PK\x03\x04", ".zip": b"PK\x03\x04", ".dmg": b"\x78\x01\x73\x0d\x62\x62\x60"}
HEADINGS = {".csv": "id,item,value,updated,note", ".json": "{", ".py": '"""Export helpers."""',
            ".md": "# Notes"}
FILLER = [
    "Please find the attached summary for your review.",
    "Let me know if the timing still works for everyone.",
    "Action items were assigned at the end of the call.",
    "The numbers below are rounded to the nearest whole value.",
    "This message and any attachments are confidential.",
    "Thanks again for your patience while we sorted this out.",
    "We can revisit the open questions next week.",
    "I moved the remaining items to the shared folder.",
    "Reminder: the office is closed on the public holiday.",
    "Sent from my phone, so please excuse the typos.",
    "The previous version had a few formatting issues that are fixed here.",
    "Nothing urgent, just keeping everyone in the loop.",
    "We agreed to keep the same format as last time.",
    "If anything looks off, reply to this thread and I will update it.",
    "The totals were checked twice against the original sheet.",
    "Next steps are listed in order of priority.",
]
FILLER_KO = [
    "첨부한 요약본 확인 부탁드립니다.",
    "일정이 모두에게 괜찮은지 알려 주세요.",
    "통화 마지막에 할 일을 나눠 맡았습니다.",
    "아래 숫자는 반올림한 값입니다.",
    "이 메일과 첨부 파일은 대외비입니다.",
    "정리하는 동안 기다려 주셔서 감사합니다.",
    "남은 질문은 다음 주에 다시 이야기해요.",
    "나머지는 공유 폴더로 옮겨 두었습니다.",
    "공휴일에는 사무실이 쉽니다.",
    "휴대폰으로 보내서 오타가 있을 수 있어요.",
    "지난번 서식 문제는 이번에 고쳤습니다.",
    "급한 건 아니고 공유차 드립니다.",
    "지난번과 같은 형식으로 하기로 했습니다.",
    "이상한 점이 있으면 답장 주세요, 바로 고칠게요.",
    "합계는 원본과 두 번 대조했습니다.",
    "다음 할 일은 우선순위 순서대로 적었습니다.",
]
FILLERS = {"en": FILLER, "ko": FILLER_KO}


class Row(NamedTuple):
    name: str
    project: Optional[str]   # None: nothing a careful person could file it under
    clue: str                # name | early | mid | deep | -
    kb: int                  # rough size; text files are filled with unrelated paragraphs to reach it
    topic: str = ""          # which clue sentence a text file carries


class Design(NamedTuple):
    rows: Sequence[Row]
    clues: Dict[str, str]                     # project -> the one sentence that gives it away
    existing: Dict[str, Tuple[str, int]]      # already organized: path -> (project, kb)
    language: str = "en"                      # picks the paragraphs that name no project


def to_design(data: Dict[str, Any], language: str) -> Design:
    """The `design` part of a design.json record."""
    rows = [Row(item["name"], item["project"], "-" if item["clue"] == "none" else item["clue"],
                int(item["kb"]), item["topic"] or "") for item in data["files"]]
    existing = {f"{item['project']}/{item['file']}": (item["project"], int(item["kb"]))
                for item in data["existing"]}
    return Design(rows, {item["name"]: item["clue"] for item in data["projects"]}, existing, language)


def paragraph(draw: random.Random, filler: Sequence[str]) -> str:
    return " ".join(draw.sample(list(filler), draw.randint(3, 6)))


def filler_lines(suffix: str, draw: random.Random, count: int, filler: Sequence[str]) -> List[str]:
    if suffix == ".csv":
        return [f"{i},item-{i},{draw.random():.2f},2026-09-{draw.randint(1, 28):02d}," for i in range(count)]
    if suffix == ".py":
        return [f"value_{i} = {draw.randint(0, 999)}  # {draw.choice(list(filler))}" for i in range(count)]
    return [paragraph(draw, filler) for _ in range(count)]


def text_file(row: Row, suffix: str, draw: random.Random, design: Design) -> str:
    head = HEADINGS.get(suffix, "")
    lines = [head] if head else []
    target, (low, high) = row.kb * 1024, CLUE_AT.get(row.clue, (0, 0))
    clue_at = draw.randint(low, high) if row.topic else -1
    if row.topic and row.clue in ("name", "early"):  # right under the header: inside the first 300 characters
        lines.append(clue_line(suffix, design.clues[row.topic]))
        clue_at = -1
    while sum(len(line) + 1 for line in lines) < target:
        if 0 <= clue_at <= sum(len(line) + 1 for line in lines):
            lines.append(clue_line(suffix, design.clues[row.topic]))
            clue_at = -1
        lines.extend(filler_lines(suffix, draw, 1, FILLERS[design.language]))
    if suffix == ".json":  # an export from a Korean app keeps its Korean readable
        notes = json.dumps(" ".join(lines[1:]), ensure_ascii=design.language == "en")
        lines = ["{", f'  "exported": "2026-10-01",', f'  "notes": {notes}', "}"]
    return "\n".join(lines) + "\n"


def clue_line(suffix: str, sentence: str) -> str:
    return {".csv": f"0,note,0,2026-10-01,\"{sentence}\"", ".py": f"# {sentence}"}.get(suffix, sentence)


def binary_file(row: Row, suffix: str, draw: random.Random) -> bytes:
    header = HEADERS[suffix]
    return header + draw.randbytes(row.kb * 1024 - len(header))


def write(path: Path, row: Row, draw: random.Random, design: Design) -> None:
    suffix = path.suffix.lower()
    path.parent.mkdir(parents=True, exist_ok=True)
    if suffix in TEXT:
        path.write_text(text_file(row, suffix, draw, design), encoding="utf-8")
    else:
        path.write_bytes(binary_file(row, suffix, draw))


def answers(design: Design, note: str) -> Dict[str, object]:
    labelled = [row for row in design.rows if row.project]
    return {
        "note": note,
        "answers": {row.name: row.project for row in design.rows},
        "known_by": {row.name: "name" if row.clue == "name" else "content" for row in labelled},
        "keep_in_place": sorted(design.existing),
        "ignore": [],
        "design": {row.name: row.clue for row in design.rows},
    }


def build(target: Path, design: Design, seed: int) -> None:
    """Every file of the design under `target`, which is emptied first."""
    draw = random.Random(seed)
    if target.exists():
        shutil.rmtree(target)
    existing = [Row(name, project, "name", kb, project if name.endswith(".md") else "")
                for name, (project, kb) in design.existing.items()]
    for row in list(design.rows) + existing:
        write(target / row.name, row, draw, design)


__all__ = ["Design", "Row", "answers", "build", "to_design"]
