#!/usr/bin/env python3
"""작업 로그 자동 생성 — worklog/YYYY-MM-DD.md

왜 자동인가
  "기록하자"는 다짐은 바쁠 때 가장 먼저 무너진다. 그래서 사람이 적는 대신
  이미 남아 있는 커밋에서 뽑아 쓴다. 커밋 메시지를 제대로 쓰는 것만이 유일한 의무가 된다.

무엇을 걸러내나
  data: 로 시작하는 자동 수집 커밋과 봇 커밋은 뺀다. 매일 수십 건이라 이걸 넣으면
  로그가 아니라 노이즈가 된다.

사용
  python worklog.py            # 오늘
  python worklog.py 2026-08-08 # 특정 날짜
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "worklog")
REGISTRY = os.path.join(ROOT, "projects", "registry.json")

OWNER = "jinhae8971"


def repos() -> list[tuple[str, str]]:
    """추적 대상은 앱 대장에서 읽는다.

    코드에 목록을 박아 두면 앱이 늘 때마다 이 파일을 고쳐야 하고,
    결국 새 앱이 로그에서 빠진다. 대장 한 곳만 고치면 되게 한다.
    """
    try:
        with open(REGISTRY, encoding="utf-8") as f:
            apps = json.load(f)["apps"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"[worklog] 대장 읽기 실패 - 기본값 사용: {exc}")
        return [("market-heatmap", "market-heatmap")]
    out = []
    for a in apps:
        repo = a.get("repo", "")
        if "/" in repo:
            out.append((repo.split("/", 1)[1], a.get("name") or repo))
    return out

SKIP_PREFIX = ("data:", "chore: 콘텐츠 인덱스", "docs: 콘텐츠 인덱스")
SKIP_AUTHOR = ("github-actions[bot]",)

KIND = {
    "feat": "기능",
    "fix": "수정",
    "chore": "정리",
    "docs": "문서",
    "refactor": "리팩터",
    "test": "테스트",
}


def api(url: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "worklog",
    })
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def commits_on(repo: str, day: dt.date) -> list[dict]:
    since = f"{day}T00:00:00Z"
    until = f"{day}T23:59:59Z"
    url = (f"https://api.github.com/repos/{OWNER}/{repo}/commits"
           f"?since={since}&until={until}&per_page=100")
    try:
        raw = api(url)
    except Exception as exc:
        print(f"[worklog] {repo} 조회 실패: {exc}")
        return []

    out, seen = [], set()
    for c in raw:
        msg = c["commit"]["message"].splitlines()[0].strip()
        author = (c.get("author") or {}).get("login") or c["commit"]["author"]["name"]
        if msg.startswith(SKIP_PREFIX) or author in SKIP_AUTHOR:
            continue
        # 같은 메시지가 여러 커밋으로 쪼개진 경우 한 줄로 합친다
        if msg in seen:
            continue
        seen.add(msg)
        out.append({"msg": msg, "sha": c["sha"][:7],
                    "time": c["commit"]["committer"]["date"][11:16]})
    return list(reversed(out))


def classify(msg: str) -> tuple[str, str]:
    m = re.match(r"^(\w+):\s*(.+)$", msg)
    if not m:
        return "기타", msg
    return KIND.get(m.group(1), m.group(1)), m.group(2)


def render(day: dt.date, per_repo: dict[str, list[dict]]) -> str:
    total = sum(len(v) for v in per_repo.values())
    lines = [f"# 작업 로그 {day}", ""]
    if not total:
        lines.append("이 날은 기록된 변경이 없다.")
        return "\n".join(lines) + "\n"

    lines.append(f"*커밋 {total}건 · 저장소 {len([k for k,v in per_repo.items() if v])}곳*")
    lines.append("")
    for repo, items in per_repo.items():
        if not items:
            continue
        lines.append(f"## {repo}")
        lines.append("")
        for it in items:
            kind, body = classify(it["msg"])
            lines.append(f"- `{it['time']}` **{kind}** {body} <sub>{it['sha']}</sub>")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 남길 것")
    lines.append("")
    lines.append("- 새로 겪은 함정 → `lessons/`")
    lines.append("- 되돌릴 수 있는 결정 → `decisions/`")
    lines.append("- 버전이 올라갔다면 → 해당 저장소 `CHANGELOG.md`")
    return "\n".join(lines) + "\n"


def main() -> None:
    day = (dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1
           else dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date())
    per_repo = {f"{label} ({r})": commits_on(r, day) for r, label in repos()}

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{day}.md")
    text = render(day, per_repo)

    # 내용이 같으면 쓰지 않는다 — 빈 커밋이 쌓이는 걸 막는다
    if os.path.exists(path) and open(path, encoding="utf-8").read() == text:
        print(f"[worklog] {day} 변경 없음")
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    print(f"[worklog] {day} · 커밋 {sum(len(v) for v in per_repo.values())}건 → {path}")


if __name__ == "__main__":
    main()
