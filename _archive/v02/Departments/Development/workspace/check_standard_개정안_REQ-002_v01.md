# [개정안] `check_standard.py` scope 파싱 트레일링 슬래시 제거

* **관련 안건**: `REQ-002` (4단계, 개발팀)
* **대상 파일**: `Departments/Development/assets/scripts/check_standard.py`
* **반영 주체**: 대표님 (`AGENTS.md` 2절 2항에 따라 개발팀은 원본을 직접 수정하지 않는다)

## 1. 변경 사유
`load_all_reqs()`가 REQ `scope:`의 항목을 그대로 읽는다. 디렉터리를 `Workflow/`처럼 끝에 슬래시를 붙여 기재하면 매칭식 `f.startswith(s + "/")`이 `Workflow//`를 찾아 불일치로 처리한다. 그 결과 정상 변경이 scope 밖 파일로 반려된다.

## 2. 변경 내용 (1행)
파일 `check_standard.py` 71행.

```diff
-                    p = line.split("-", 1)[1].strip().strip("'\"")
-                    scope_lines.append(p.replace("\\", "/"))
+                    p = line.split("-", 1)[1].strip().strip("'\"")
+                    scope_lines.append(p.replace("\\", "/").rstrip("/"))
```

## 3. 영향도
* 변경 범위는 scope 항목 정규화 1곳이다. 매칭 로직(152행)과 다른 함수는 수정하지 않는다.
* 슬래시 없는 기존 항목(`Workflow`, `AGENTS.md`)은 결과가 같다.
* 항목이 `/` 한 글자뿐이면 빈 문자열이 되어 전체 허용이 될 수 있다. 현행 REQ에는 해당 항목이 없고, 현행 코드도 `/`는 어떤 파일과도 일치하지 않는다. 별도 방어 코드는 추가하지 않는다(YAGNI).

## 4. 사전 검증 결과 (원본 미수정, 식 단독 실행)
| 입력 scope 항목 | 대상 파일 | 현행 매칭 | 개정 매칭 |
| :--- | :--- | :---: | :---: |
| `Workflow/` | `Workflow/01_x.md` | 불일치 | 일치 |
| `Departments/Design/docs/tad/` | `Departments/Design/docs/tad/EC-002.md` | 불일치 | 일치 |
| `Workflow` | `Workflow/01_x.md` | 일치 | 일치 |

## 5. 반영 후 확인 명령
```bash
python Departments/Development/assets/scripts/check_standard.py
```
