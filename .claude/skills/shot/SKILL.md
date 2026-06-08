---
name: shot
description: 최신 스크린샷을 자동으로 찾아 불러옵니다 (인자 없음=최근 1개, 숫자 N=최근 N개, list=최근 5개 목록 보여줌). 사용자가 "스샷", "스크린샷", "방금 화면" 등을 언급하며 확인을 요청할 때 사용하세요.
user-invocable: true
allowed-tools:
  - Read
  - Bash(ls *)
---

# /shot — 최신 스크린샷 자동 로드

`C:\Users\a\Documents\스크린샷\` 폴더에서 가장 최근에 수정된 이미지 파일을 찾아 Read 툴로 불러옵니다.

인자: `$ARGUMENTS`

## 동작

1. `ls -t "C:\Users\a\Documents\스크린샷"` (또는 PowerShell의
   `Get-ChildItem ... | Sort-Object LastWriteTime -Descending`)로 폴더 내
   이미지 파일(.png, .jpg, .jpeg)을 최신 수정 시간 순으로 정렬합니다.
2. 인자에 따라 분기:
   - 인자 없음 → 가장 최근 파일 1개를 Read
   - 숫자 N (예: `3`) → 최근 N개를 모두 Read
   - `list` → 최근 5개 파일명과 수정 시각만 보여주고, 사용자가 어떤 것을
     볼지 선택하게 함 (자동으로 아무거나 고르지 않음)
3. 불러온 뒤 파일명을 한 줄로 알려주고, 바로 사용자가 원래 하려던 작업
   (UI 검토, 버그 확인 등)으로 이어갑니다.

## 주의

- 폴더가 비어있거나 없으면 그 사실을 알리고 멈춥니다 (임의로 다른 폴더를
  뒤지지 않음).
- 파일명에 한글/공백이 포함될 수 있으므로 경로는 항상 따옴표로 감쌉니다.
