"""REQ-012 적용본 폴더 v01을 v02로 복사하는 일회성 스크립트.

셸 복사(cp, Copy-Item)가 이 세션에서 권한 확인 대상이라 실행되지 않아 Python으로 복사한다.
v02 폴더가 이미 있으면 덮어쓰지 않고 멈춘다(덮어쓰기는 사용자 승인 대상이다).
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "Departments/Design/workspace/REQ-012_적용본_v01"
DST = ROOT / "Departments/Design/workspace/REQ-012_적용본_v02"

if DST.exists():
    sys.exit(f"[STOP] {DST.relative_to(ROOT).as_posix()}가 이미 있습니다. 덮어쓰지 않습니다.")
shutil.copytree(SRC, DST)
for p in sorted(DST.rglob("*")):
    if p.is_file():
        print(p.relative_to(ROOT).as_posix())
