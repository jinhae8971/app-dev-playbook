#!/usr/bin/env python3
"""저장소의 마크다운을 대시보드가 읽을 JSON 하나로 묶는다.

왜 빌드 단계를 두는가: 대시보드가 md 파일을 직접 fetch하면 파일이 늘 때마다
목록을 손으로 고쳐야 한다. 여기서 파일 시스템을 훑어 목록·본문·메타를 뽑아 두면
문서를 추가하는 것만으로 대시보드에 반영된다.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs", "content.json")
SECTIONS = {
    "guides": "가이드",
    "lessons": "오답노트",
    "decisions": "결정기록",
    "templates": "템플릿",
    "projects": "프로젝트",
    "worklog": "작업로그",
}


def git_date(path: str) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or ""
    except Exception:
        return ""


def parse(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")

    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else os.path.basename(path)

    # 첫 이탤릭 줄을 메타로 쓴다 (*2026-08-08 · 상태: 채택*)
    meta = ""
    mm = re.search(r"^\*(.+?)\*$", text, re.M)
    if mm:
        meta = mm.group(1).strip()

    headings = re.findall(r"^##\s+(.+)$", text, re.M)

    # 오답노트의 '신호' 줄 — 이 저장소에서 가장 재사용되는 한 줄
    signals = [s.strip() for s in
               re.findall(r"\*\*신호\*\*\s*(.+?)(?:\n|$)", text)]

    body = re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M).strip()
    plain = re.sub(r"[#*`>|\-\[\]()]", " ", body)

    return {
        "path": rel,
        "section": rel.split("/")[0] if "/" in rel else "root",
        "title": title,
        "meta": meta,
        "headings": headings,
        "signals": signals,
        "body": body,
        "search": re.sub(r"\s+", " ", (title + " " + plain))[:6000],
        "updated": git_date(rel),
        "words": len(plain.split()),
    }


def main() -> None:
    docs = []
    for section in SECTIONS:
        d = os.path.join(ROOT, section)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md"):
                docs.append(parse(os.path.join(d, fn)))
    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        docs.append(parse(readme))

    payload = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sections": SECTIONS,
        "docs": docs,
        "stats": {
            "docs": len(docs),
            "lessons": sum(1 for d in docs if d["section"] == "lessons"),
            "decisions": sum(1 for d in docs if d["section"] == "decisions"),
            "signals": sum(len(d["signals"]) for d in docs),
            "words": sum(d["words"] for d in docs),
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, OUT)
    print(f"문서 {payload['stats']['docs']}건 · 신호 {payload['stats']['signals']}개 → {OUT}")


if __name__ == "__main__":
    main()
