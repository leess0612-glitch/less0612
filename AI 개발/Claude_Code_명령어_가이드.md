# Claude Code 명령어 완벽 가이드

> Claude Code CLI 사용을 위한 필수 명령어 모음

---

## 목차

1. [기본 명령어](#1-기본-명령어)
2. [주요 CLI 플래그](#2-주요-cli-플래그)
3. [슬래시 명령어](#3-슬래시-명령어)
4. [키보드 단축키](#4-키보드-단축키)
5. [설정 관련](#5-설정-관련)
6. [실전 활용 예시](#6-실전-활용-예시)

---

## 1. 기본 명령어

### 시작하기

```bash
# 대화형 모드 시작
claude

# 질문과 함께 시작
claude "이 프로젝트 설명해줘"

# 질문 후 바로 종료 (비대화형)
claude -p "이 함수 설명해줘"

# 최근 대화 이어하기
claude -c

# 특정 세션 복구
claude -r "session-name"

# 버전 확인
claude -v

# 업데이트
claude update
```

---

## 2. 주요 CLI 플래그

### 권한 관련 (중요!)

| 플래그 | 설명 | 사용 예시 |
|--------|------|-----------|
| `--dangerously-skip-permissions` | 모든 권한 확인 건너뛰기 | `claude --dangerously-skip-permissions` |
| `--permission-mode` | 권한 모드 지정 | `claude --permission-mode plan` |

```bash
# 권한 확인 없이 실행 (주의: 위험할 수 있음)
claude --dangerously-skip-permissions

# Plan 모드로 시작 (코드 수정 없이 계획만)
claude --permission-mode plan
```

### 모델 선택

```bash
# Sonnet 모델 사용
claude --model sonnet

# Opus 모델 사용
claude --model opus

# 특정 모델 지정
claude --model claude-sonnet-4-5-20250929
```

### 시스템 프롬프트

```bash
# 시스템 프롬프트 추가 (기본 프롬프트 유지)
claude --append-system-prompt "항상 TypeScript를 사용해줘"

# 시스템 프롬프트 교체 (기본 프롬프트 대체)
claude --system-prompt "당신은 Python 전문가입니다"

# 파일에서 시스템 프롬프트 로드
claude -p --system-prompt-file ./prompt.txt "query"
```

### 도구 설정

```bash
# 특정 도구만 허용
claude --allowedTools "Bash(git log:*)" "Read"

# 특정 도구 차단
claude --disallowedTools "Bash(curl:*)"

# 사용할 도구 지정
claude --tools "Bash,Edit,Read"
```

### 세션 관리

```bash
# 최근 대화 이어하기
claude -c
claude --continue

# 특정 세션 복구
claude -r "abc123"
claude --resume "abc123"

# 세션 복구 + 새 세션 ID 생성
claude -r abc123 --fork-session
```

### 디렉토리 및 파일

```bash
# 추가 작업 디렉토리 지정
claude --add-dir ../apps ../lib

# 특정 설정 파일 사용
claude --settings ./settings.json
```

### 출력 형식 (자동화용)

```bash
# JSON 형식으로 출력
claude -p --output-format json "query"

# 스트리밍 JSON
claude -p --output-format stream-json "query"

# 최대 턴 수 제한
claude -p --max-turns 3 "query"
```

### 디버깅

```bash
# 디버그 모드
claude --debug "api,mcp"

# 상세 로깅
claude --verbose
```

---

## 3. 슬래시 명령어

대화 중에 `/`로 시작하는 명령어를 사용할 수 있습니다.

### 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 도움말 표시 |
| `/exit` | 종료 |
| `/clear` | 대화 히스토리 초기화 |
| `/status` | 상태 확인 (버전, 모델, 계정) |

### 세션 관리

| 명령어 | 설명 |
|--------|------|
| `/resume` | 이전 세션 복구 |
| `/rename <name>` | 현재 세션 이름 변경 |
| `/export [filename]` | 대화 내보내기 |
| `/rewind` | 이전 상태로 되돌리기 |

### 설정

| 명령어 | 설명 |
|--------|------|
| `/config` | 설정 인터페이스 열기 |
| `/model` | 모델 변경 |
| `/permissions` | 권한 설정 |
| `/settings` | 설정 파일 편집 |

### 메모리 & 컨텍스트

| 명령어 | 설명 |
|--------|------|
| `/memory` | CLAUDE.md 메모리 파일 편집 |
| `/init` | 프로젝트 CLAUDE.md 초기화 |
| `/context` | 컨텍스트 사용량 시각화 |
| `/cost` | 토큰 사용 통계 |
| `/compact` | 대화 압축 (토큰 절약) |

### 도구 & 통합

| 명령어 | 설명 |
|--------|------|
| `/mcp` | MCP 서버 관리 |
| `/hooks` | 훅 구성 관리 |
| `/ide` | IDE 통합 관리 |
| `/vim` | Vim 모드 활성화 |

### 작업 관리

| 명령어 | 설명 |
|--------|------|
| `/todos` | TODO 항목 나열 |
| `/bashes` | 백그라운드 작업 관리 |

### 기타

| 명령어 | 설명 |
|--------|------|
| `/doctor` | 설치 상태 확인 |
| `/bug` | 버그 리포트 |
| `/login` | 계정 전환 |
| `/logout` | 로그아웃 |

---

## 4. 키보드 단축키

### 기본 제어

| 단축키 | 설명 |
|--------|------|
| `Ctrl+C` | 현재 작업 취소 |
| `Ctrl+D` | 세션 종료 |
| `Ctrl+L` | 화면 지우기 |
| `Ctrl+R` | 명령어 히스토리 검색 |
| `Up/Down` | 히스토리 탐색 |

### 권한 & 모드

| 단축키 | 설명 |
|--------|------|
| `Shift+Tab` 또는 `Alt+M` | 권한 모드 토글 |
| `Alt+P` (Win/Linux) / `Option+P` (Mac) | 모델 전환 |
| `Esc + Esc` | 이전 상태로 복원 |

### 여러 줄 입력

| 방법 | 단축키 |
|------|--------|
| 백슬래시 | `\ + Enter` |
| macOS | `Option + Enter` |
| 설정 후 | `Shift + Enter` |

### 기타

| 단축키 | 설명 |
|--------|------|
| `Ctrl+B` | 백그라운드로 이동 |
| `Ctrl+O` | 상세 출력 토글 |
| `@` | 파일 경로 자동완성 |

---

## 5. 설정 관련

### 설정 파일 위치

| 범위 | 경로 | 용도 |
|------|------|------|
| 사용자 전역 | `~/.claude/settings.json` | 모든 프로젝트에 적용 |
| 프로젝트 | `.claude/settings.json` | 팀과 공유 |
| 로컬 | `.claude/settings.local.json` | 개인용 (Git 제외) |

### 주요 환경 변수

```bash
# API 키 설정
export ANTHROPIC_API_KEY="your-api-key"

# 기본 모델 설정
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"

# 자동 업데이트 비활성화
export DISABLE_AUTOUPDATER=1

# 텔레메트리 비활성화
export DISABLE_TELEMETRY=1

# Extended Thinking 토큰 설정
export MAX_THINKING_TOKENS=8000
```

### 커스텀 명령어 만들기

```bash
# 프로젝트 명령어
mkdir -p .claude/commands
echo "이 코드를 최적화해줘:" > .claude/commands/optimize.md

# 개인 명령어
mkdir -p ~/.claude/commands
echo "보안 취약점을 검토해줘:" > ~/.claude/commands/security.md
```

---

## 6. 실전 활용 예시

### 자동화 스크립트용

```bash
# 로그 분석
cat logs.txt | claude -p "이 에러 로그를 분석해줘"

# JSON 출력으로 저장
claude -p --output-format json "프로젝트 구조 분석해줘" > analysis.json

# 권한 확인 없이 자동 실행
claude --dangerously-skip-permissions -p "테스트 실행해줘"
```

### 개발 작업용

```bash
# TypeScript 전문가 모드로 시작
claude --append-system-prompt "항상 TypeScript와 최신 문법을 사용해줘"

# Plan 모드로 안전하게 시작
claude --permission-mode plan

# 특정 디렉토리도 포함해서 작업
claude --add-dir ../shared ../common
```

### 세션 관리

```bash
# 작업 이어하기
claude -c

# 특정 작업 세션 복구
claude -r "feature-auth"

# 세션 목록 확인 후 복구
claude  # 시작 후
/resume  # 세션 선택기 열기
```

### 토큰 절약

```bash
# 대화 중 압축
/compact

# 컨텍스트 사용량 확인
/context

# 비용 확인
/cost
```

### 디버깅

```bash
# 문제 진단
/doctor

# 디버그 모드로 시작
claude --debug "api,mcp" --verbose
```

---

## 빠른 참조 카드

### 가장 많이 쓰는 명령어

```bash
claude                              # 시작
claude -c                           # 이어하기
claude -p "질문"                    # 빠른 질문
claude --dangerously-skip-permissions  # 권한 스킵
```

### 가장 많이 쓰는 슬래시 명령어

```
/help      # 도움말
/clear     # 초기화
/compact   # 압축
/model     # 모델 변경
/context   # 사용량 확인
```

### 가장 많이 쓰는 단축키

```
Ctrl+C         # 취소
Shift+Tab      # 모드 변경
Esc + Esc      # 되돌리기
\ + Enter      # 여러 줄 입력
```

---

## 참고 문서

- CLI 참조: https://docs.anthropic.com/claude-code/cli
- 슬래시 명령어: https://docs.anthropic.com/claude-code/slash-commands
- 설정 가이드: https://docs.anthropic.com/claude-code/settings
