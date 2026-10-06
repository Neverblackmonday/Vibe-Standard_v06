---
audit_id: "AUDIT_YYYYMMDD_<주제>_v01"
created: "YYYY-MM-DDTHH:MM:SS+09:00"
auditor:
  agent: "External Auditor" # 또는 감사 세션 모델명
  model: "Claude Opus 5.5"
  thinking: "medium"
classification: "Independent Audit" # 특별 감사 | 정기 감사 | 적합성 감사
status: "completed" # completed | action_required
---

# [외부 감사 보고서] AUDIT_YYYYMMDD_<주제>_v01

> 본 문서는 대표님의 특별 지시 또는 독립 감사 기준에 따라 수행된 외부 감사 결과서입니다.
> 감사는 비정기적으로 수행되므로 `001, 002` 같은 일련번호 대신 **날짜 기반 명명(`AUDIT_YYYYMMDD_<주제>_v01.md`)**을 사용합니다.

## 1. 감사 개요 및 지시 사항
- **감사 명칭**: 감사 제목
- **감사 일시**: YYYY-MM-DDTHH:MM:SS+09:00
- **감사관**: 감사 부서/세션
- **감사 대상**: 검토 대상 폴더, 안건 또는 시스템 명세
- **대표님 지시 원문**:
  > 대표님의 지시 원문을 원형 그대로 인용합니다.

---

## 2. 거버넌스 승인 및 무결성 점검 (필수 점검 항목)
외부 감사는 대표님의 특별 요청 검토 외에도, 저장소 내 모든 안건과 변경 사항의 거버넌스 승인 누락 여부를 전수 점검합니다.

| 안건/기록 번호 | 구분 (REQ/EC/HOTFIX/RES) | 승인 필드 (`approved` / `confirmed`) | 승인 일시 기재 여부 | 정상 여부 |
| :---: | :---: | :---: | :---: | :---: |
| REQ-xxx | REQ | `approved: "YYYY-MM-DD..."` | 기재 완료 | 정상 |
| EC-xxx | EC | `status: "approved"`, `gate: ...` | 기재 완료 | 정상 |
| HOTFIX-xxx | HOTFIX | `confirmed: "YYYY-MM-DD..."` | 기재 완료 | 정상 |
| RES-xxx | RES | `result: "pass"` | 기재 완료 | 정상 |

---

## 3. 세부 감사 내용 및 정밀 분석
(대표님이 요청하신 특별 주제에 대한 정밀 분석, 기술적 적합성 검토, 아키텍처 실사 내용을 기술합니다.)

---

## 4. 지적 사항 및 권고 조치 (체크리스트)
- [ ] 1. 미승인 파일 수정 또는 Scope 이탈 방지 조치 완료
- [ ] 2. 승인 필드 누락 안건의 소급 보완 또는 사후 승인 절차 완료
- [ ] 3. 식별된 취약점 및 결함 조치 완료

---

## 5. 최종 종합 의견
- **감사 판정**: `적격 (Clean)` / `개선 권고 (Advisory)` / `부적격 (Non-Compliant)`
- **종합 소견**: 성인 직장인의 명확하고 평이한 어조로 최종 의견을 기록합니다.
