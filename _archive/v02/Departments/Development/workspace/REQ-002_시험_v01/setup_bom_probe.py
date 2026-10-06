#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REQ-002 EC 3.4절 1번 setup.cmd BOM 실측.

원본 setup.cmd에서 앞머리 BOM을 모두 뗀 본문에 BOM을 0개·1개·2개 붙인 사본을
저장소 밖 임시 폴더에 하나씩 만들고 `cmd /c setup.cmd`로 실행해 첫 줄(@echo off) 처리 결과를 기록한다.
setup.cmd는 임시 폴더 안에서 git init·git add·git commit을 실행하며, 원본 저장소에는 영향이 없다.
마지막으로 개발 적용본 setup.cmd의 앞머리 바이트와 줄 끝을 확인한다.

사용법: python Departments/Development/workspace/REQ-002_시험_v01/setup_bom_probe.py
종료 코드: BOM 0개 사본이 첫 줄을 정상 처리하고 적용본이 BOM 0개·CRLF이면 0, 아니면 1.
"""

import datetime
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ORIGINAL = REPO / "setup.cmd"
APPLIED = REPO / "Departments/Development/workspace/REQ-002_적용본_v01/setup.cmd"
BOM = b"\xef\xbb\xbf"


def strip_bom(data):
    count = 0
    while data.startswith(BOM):
        data = data[len(BOM):]
        count += 1
    return data, count


def decode(raw):
    # chcp 65001 실행 전 오류 메시지는 콘솔 코드 페이지(cp949), 이후 출력은 UTF-8이므로 줄마다 해석한다
    lines = []
    for line in raw.splitlines():
        try:
            lines.append(line.decode("utf-8"))
        except UnicodeDecodeError:
            lines.append(line.decode("cp949", errors="replace"))
    return lines


def probe(body, bom_count):
    with tempfile.TemporaryDirectory(prefix=f"req002_bom{bom_count}_", ignore_cleanup_errors=True) as tmp:
        (Path(tmp) / "setup.cmd").write_bytes(BOM * bom_count + body)
        # 현재 폴더 실행 파일 검색이 꺼진 환경(NoDefaultCurrentDirectoryInExePath)에서도 실행되도록 경로를 명시한다
        res = subprocess.run(["cmd", "/c", r".\setup.cmd"], cwd=tmp, capture_output=True)
        out = decode(res.stdout)
        err = decode(res.stderr)
        # @echo off가 처리되지 않으면 echo가 켜진 채로 남아 다음 명령 줄(chcp 65001)이 프롬프트와 함께 출력된다
        echoed = any("chcp 65001" in line for line in out)
        first_line_error = any("echo" in line.lower() for line in err)
        completed = any("[성공]" in line for line in out)
        return res.returncode, out, err, echoed, first_line_error, completed


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    print(f"시각: {now}")
    raw = ORIGINAL.read_bytes()
    body, original_count = strip_bom(raw)
    print(f"원본 setup.cmd 앞머리 BOM 개수: {original_count}, 첫 16바이트: {raw[:16]!r}")

    results = {}
    for n in (0, 1, 2):
        rc, out, err, echoed, first_err, completed = probe(body, n)
        ok = completed and not echoed and not first_err
        results[n] = ok
        print(f"\n=== BOM {n}개 사본 | 종료 코드 {rc} | 명령 줄 표시(echo 켜짐) {echoed} | 첫 줄 오류 {first_err} | 끝까지 실행 {completed} | 첫 줄 정상 처리 {ok}")
        print("--- stdout")
        print("\n".join(out))
        print("--- stderr")
        print("\n".join(err))

    applied = APPLIED.read_bytes()
    applied_body, applied_count = strip_bom(applied)
    crlf = applied.count(b"\r\n")
    bare_lf = applied.count(b"\n") - crlf
    print(f"\n적용본 setup.cmd: 앞머리 BOM {applied_count}개, 첫 16바이트 {applied[:16]!r}, CRLF {crlf}줄, 단독 LF {bare_lf}줄, 원본 본문과 동일 {applied_body == body}")

    ok = results[0] and applied_count == 0 and bare_lf == 0 and applied_body == body
    print(f"\n전체 결과: {'기대대로' if ok else '기대와 다름'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
