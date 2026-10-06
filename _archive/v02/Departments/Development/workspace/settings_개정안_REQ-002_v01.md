# [개정안] `.claude/settings.json` deny 목록에 `Workflow/**` 추가

* **관련 안건**: `REQ-002` (4단계, 개발팀)
* **대상 파일**: `.claude/settings.json`
* **반영 주체**: 대표님 (`Edit(.claude/**)`, `Write(.claude/**)`가 `deny`에 등록되어 있어 에이전트는 직접 수정할 수 없다)

## 1. 변경 사유
`Workflow/`는 표준 자체의 매뉴얼 7종이며 대표님 단독 수정 구역이다(`AGENTS.md` 2절 2항). 플랫폼 수준의 `deny`에 등록하여 에이전트의 무단 변조를 차단한다.

## 2. 변경 내용
`deny` 배열 끝에 두 항목을 추가한다. 기존 항목 가운데 `Departments/Development/assets/scripts/**` 줄 끝에 쉼표가 필요하다.

```diff
       "Edit(Departments/Development/assets/scripts/**)",
-      "Write(Departments/Development/assets/scripts/**)"
+      "Write(Departments/Development/assets/scripts/**)",
+      "Edit(Workflow/**)",
+      "Write(Workflow/**)"
     ],
```

## 3. 영향도
* 3단계(설계팀)의 `Workflow/` 작성은 이미 완료되어 있어 이번 등록으로 중단되는 작업은 없다. 이후 `Workflow/` 개정은 대표님이 직접 수행한다.
* `ask` 목록과 다른 `deny` 항목은 변경하지 않는다.

## 4. 반영 후 확인 명령
```bash
python -c "import json; d=json.load(open('.claude/settings.json',encoding='utf-8')); print([x for x in d['permissions']['deny'] if 'Workflow' in x])"
```
기대 출력: `['Edit(Workflow/**)', 'Write(Workflow/**)']`
