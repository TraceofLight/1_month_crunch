# ai-gitgen — Git 변경 사항 기반 커밋 / PR 초안 자동 생성기

`git status` 와 `git diff` 결과를 입력으로 받아 **커밋 메시지** 와
**Pull Request 초안** 을 한 번에 1회 AI API 호출로 만들어주는 터미널 도구입니다.
Anthropic Claude API 를 기본 백엔드로 사용하며, 프롬프트·옵션·후처리까지
모두 코드에서 직접 제어해 결과 품질을 일정 수준 이상으로 끌어올립니다.

---

## 디렉터리 구조

```
ai-assignment/
├── main.py                  # CLI 진입점 (UTF-8 stdout 재설정 후 패키지에 위임)
├── aigitgen/                # 핵심 패키지
│   ├── cli.py               # argparse 서브커맨드, 흐름 오케스트레이션
│   ├── git_ops.py           # git status / diff / untracked 수집
│   ├── safe_mode.py         # 민감정보 마스킹 + diff 분량 절단
│   ├── prompts.py           # commit / pr 용 system + user 프롬프트 빌더
│   ├── ai_client.py         # Anthropic API 호출 + 예외 변환
│   ├── validators.py        # 길이/섹션/불릿 규칙 검증 및 자동 보정
│   └── render.py            # 터미널 출력(헤더·구획선·INFO 로그)
├── Dockerfile               # 평가자 재현용 컨테이너 (git + python:3.12-slim)
├── requirements.txt         # anthropic, python-dotenv
├── evidence/                # 실행 결과 캡처 (재현 확인용)
└── README.md                # 이 문서
```

---

## 빠른 시작

### 1. 사전 요구사항

- Python 3.10 이상 (개발은 3.12.10 에서 진행)
- Git CLI (PATH 등록 필수)
- Anthropic API Key

### 2. 설치

```bash
# 1) 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\Activate.ps1         # Windows PowerShell

# 2) 의존성 설치
pip install -r requirements.txt
```

### 3. API Key 설정 (환경변수)

코드에는 키를 하드코딩하지 않습니다. 다음 중 하나로 설정합니다.

```powershell
# Windows PowerShell
$env:AI_API_KEY = "sk-ant-..."
```

```bash
# macOS / Linux / Git Bash
export AI_API_KEY="sk-ant-..."
```

```bash
# .env 파일을 둬도 자동으로 로드됩니다 (python-dotenv 사용)
echo 'AI_API_KEY=sk-ant-...' > .env
```

환경변수 이름은 `AI_API_KEY` 를 우선 검사하고, 없으면 Anthropic 표준인
`ANTHROPIC_API_KEY` 도 받아들입니다. 둘 다 비어 있으면 다음과 같이 즉시 종료합니다.

```
[INFO] Git 변경 사항 수집 중...
[INFO] 변경 파일 7개 / diff 118줄 감지
[INFO] AI API 요청 중...
[ERROR] AI_API_KEY (또는 ANTHROPIC_API_KEY) 환경변수가 설정되지 않았습니다.
  예) Windows PowerShell: $env:AI_API_KEY = "YOUR_KEY"
       Bash:               export AI_API_KEY="YOUR_KEY"
```

### 4. 실행

Git 저장소 루트에서 실행합니다.

```bash
# 커밋 메시지 생성
python main.py commit

# PR 초안 생성 (현재 브랜치 ↔ main 비교, base 변경 가능)
python main.py pr
python main.py pr --base develop
```

---

## CLI 옵션

`commit`, `pr` 두 서브커맨드 모두 다음 공통 옵션을 지원합니다.

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--model` | `claude-haiku-4-5-20251001` | 호출 모델. 품질을 더 원하면 `claude-sonnet-4-6` 등으로 교체. |
| `--temperature` | `0.3` | 샘플링 온도. 결정적 결과는 낮게, 다양한 표현은 높게. |
| `--max-tokens` | `1024` | 응답 길이 한도. 너무 작으면 본문이 잘리거나 비어 옵니다. |
| `--safe-mode` | off | 민감정보 마스킹 + diff 분량 제한을 켜고 프롬프트로 전송. |
| `--max-files` | `10` | safe-mode 활성 시 diff 에 포함할 파일 수 한도 (`0`=무제한). |
| `--max-lines` | `200` | safe-mode 활성 시 diff 라인 수 한도 (`0`=무제한). |
| `--cwd PATH` | 현재 디렉터리 | 대상 Git 저장소 경로 지정. |
| `--dry-run` | off | AI 호출 없이 조립된 프롬프트만 출력해 점검. |

서브커맨드 전용 옵션:

| 옵션 | 적용 | 기본값 | 설명 |
|---|---|---|---|
| `--staged` | `commit` | off | staged 변경만 사용 (기본은 staged + unstaged + 신규파일). |
| `--base` | `pr` | `main` | PR 비교 기준 브랜치. `git diff <base>...HEAD` 가 됩니다. |

---

## 사용 예시

### 커밋 메시지 생성

```bash
$ python main.py commit
[INFO] Git 변경 사항 수집 중...
[INFO] 변경 파일 3개 / diff 128줄 감지
[INFO] AI API 요청 중...
[DONE] 커밋 메시지 생성 완료
[INFO] AI API 호출 횟수: 1회
[INFO] 모델=claude-haiku-4-5-20251001 latency=842ms tokens(in/out)=2103/187

============================================================
                       Commit Message
============================================================
feat: Git 변경 사항 기반 커밋 메시지 자동 생성 기능 추가

- aigitgen/cli.py 에 commit 서브커맨드 추가, git diff 를 프롬프트 컨텍스트로 연결
- aigitgen/validators.py 에 제목 72자 한도와 본문 불릿 검증 후처리 적용
- API Key 미설정 시 사용자에게 PowerShell/Bash 예시 안내 메시지 출력
============================================================
```

### PR 초안 생성

```bash
$ python main.py pr --base main
[INFO] Git 변경 사항 수집 중...
[INFO] 변경 파일 12개 / diff 420줄 감지
[INFO] 현재 브랜치: b6-2, base: main
[INFO] AI API 요청 중...
[DONE] PR 초안 생성 완료
[INFO] AI API 호출 횟수: 1회
[INFO] 모델=claude-haiku-4-5-20251001 latency=1310ms tokens(in/out)=3812/420

============================================================
                          PR Title
============================================================
feat: 커밋/PR 자동 생성 CLI(ai-gitgen) 추가

============================================================
                          PR Body
============================================================
## Why
- 팀이 커밋 메시지와 PR 설명 작성에 매번 비슷한 시간을 들이고 있어, Git 변경을 입력으로 받는 자동 초안기를 도입함
- AI 결과의 길이/형식 일관성을 사람 손이 아닌 코드로 강제해 리뷰 비용을 줄이는 것이 목적

## What
- aigitgen 패키지 신설: git_ops / prompts / ai_client / validators / safe_mode / render 모듈로 책임 분리
- main.py 에서 argparse 기반 commit / pr 서브커맨드 노출, --model/--temperature/--max-tokens/--safe-mode 등 옵션 제공
- Anthropic API 호출 결과를 검증·자동 보정하여 커밋 72자 / PR 80자 / Why·What·How to Test 섹션 규칙을 강제

## How to Test
- `pip install -r requirements.txt` 후 `$env:AI_API_KEY = "..."` 로 키 설정
- 변경이 있는 Git 저장소에서 `python main.py commit` 실행, 커밋 메시지가 구획선과 함께 출력되는지 확인
- 같은 저장소에서 `python main.py pr --base main` 실행, 출력에 `## Why`, `## What`, `## How to Test` 헤더와 각 섹션 ≥1 불릿이 포함되는지 확인
============================================================
```

### 변경 사항이 없을 때

```bash
$ python main.py commit
[INFO] Git 변경 사항 수집 중...
[INFO] 변경 파일 0개 / diff 0줄 감지
[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.
```

### dry-run (프롬프트 점검)

`--dry-run` 은 AI 호출을 하지 않고 system + user 프롬프트만 출력해
프롬프트 설계나 safe-mode 효과를 비용 없이 확인할 때 사용합니다.

```bash
$ python main.py commit --dry-run
[INFO] Git 변경 사항 수집 중...
[INFO] 변경 파일 7개 / diff 118줄 감지
[INFO] --dry-run: AI 호출 없이 프롬프트만 출력합니다.
=== SYSTEM ===
당신은 한국어로 작성되는 Git 커밋 메시지를 만드는 시니어 엔지니어입니다.
...
=== USER ===
[변경된 파일 목록]
- aigitgen/...
[git status]
...
```

---

## 동작 흐름

```
   ┌─────────────┐    ┌──────────────┐    ┌────────────┐    ┌─────────────┐
   │ git status  │ →  │ safe-mode    │ →  │ prompts.py │ →  │ Anthropic   │
   │ git diff    │    │ (옵션)       │    │ system+user│    │ Messages API│
   │ untracked   │    │ mask/truncate│    │            │    │ (1회 호출)  │
   └─────────────┘    └──────────────┘    └────────────┘    └──────┬──────┘
                                                                    │
                                       ┌────────────────────────────┘
                                       ▼
                              ┌─────────────────┐    ┌──────────────┐
                              │ validators.py   │ →  │ render.py    │
                              │ 길이/섹션/불릿  │    │ 구획선+로그  │
                              │ 자동 보정       │    │ 터미널 출력  │
                              └─────────────────┘    └──────────────┘
```

1. **수집**: `git_ops.snapshot()` 가 `git status --short`, `git diff HEAD`,
   현재 브랜치, 그리고 untracked 파일을 모읍니다. untracked 파일은
   `git diff --no-index /dev/null <file>` 로 합성 diff 를 만들어 인덱스를
   건드리지 않은 채로 신규 파일 내용까지 프롬프트에 실어줍니다.
2. **safe-mode**: 활성 시 `safe_mode.apply_safe_mode()` 가 diff 에서
   민감정보를 마스킹하고 파일/라인 수 한도로 잘라냅니다.
3. **프롬프트 조립**: `prompts.build_commit_prompt()` /
   `build_pr_prompt()` 가 출력 형식 규칙을 system 메시지에, 변경 컨텍스트를
   user 메시지에 분리해 담습니다.
4. **AI 호출**: `ai_client.call_anthropic()` 가 Anthropic Messages API 를
   **1회** 호출합니다. 인증 실패·네트워크 오류·속도 제한·기타 API 오류는
   각각 한국어 메시지로 변환됩니다.
5. **검증/보정**: `validators.parse_commit()` / `parse_pr()` 가 길이 한도와
   섹션/불릿 존재 여부를 확인합니다. 위반은 잘라내거나 자리표시자를 주입한
   뒤 `[WARN]` 으로 사용자에게 알립니다.
6. **출력**: `render.py` 가 헤더와 구획선으로 영역을 나누어 터미널에 보여줍니다.

---

## 프롬프트 설계 메모

### 결과 품질을 결정하는 요소

- **system 메시지를 형식·역할 규약 전용으로 사용**: 길이 한도(50/72/80),
  Conventional Commits prefix, Why/What/How to Test 헤더, 불릿 개수 같은
  "출력 모양" 을 system 에 박아두면 user 메시지의 가변성(변경 내용)이 결과
  형식을 흔들지 않습니다.
- **user 메시지는 컨텍스트 구획**: 변경 파일 목록 → status → diff 순서로
  넣고 각각 markdown fenced block 으로 감싸 모델이 "코드 영역" 으로 인지하게
  합니다. diff 가 너무 길면(기본 12,000자 / PR 14,000자) 명시적으로
  "[... N자 생략 ...]" 표시를 붙여 잘림 사실을 모델이 알게 합니다.
- **출력 contract 를 코드 파싱 가능하게**: PR 의 경우 `TITLE: <한 줄>` 로
  시작하고 `---` 구분선 다음 본문이 오도록 강제했습니다. 정규식 한 줄로
  제목/본문을 분리할 수 있어 다음 단계 검증이 단순해집니다.
- **금지 표현 명시**: 코드 블록(```)·"이상입니다"·머리말/꼬리말 같은 흔한
  잡음을 system 에 "넣지 마세요" 로 명시. 길게 풀어 쓴 한 줄짜리 "금지
  목록" 이 단순 예시보다 잡음 제거 효과가 큽니다.

### `temperature`, `max_tokens` 의 영향

- `temperature` 가 높을수록(>0.7) 같은 diff 라도 표현이 매번 달라지고
  형식을 깰 확률이 올라갑니다. 본 도구는 형식 강제가 중요하므로 기본
  **0.3** 으로 두었습니다. 다양한 후보를 보고 싶다면 0.7~0.9 까지 올려
  여러 번 호출해 비교해도 좋습니다(비용 증가).
- `max_tokens` 는 응답 잘림을 방지하는 안전망입니다. 기본 1024 토큰이면
  commit 메시지 + 4불릿 PR 본문까지 여유 있게 들어갑니다. 변경이 매우 클
  때 본문이 잘려 PR 섹션이 누락되면 validators 가 자리표시자를 넣고
  경고하지만, 근본 해결은 `--max-tokens 2048` 정도로 늘리는 것입니다.
- `model` 은 비용/품질 트레이드오프 축입니다. 기본 Haiku 는 짧은 변경엔
  충분합니다. 변경 규모가 크거나 자연어 품질이 더 중요하면 Sonnet 으로
  교체하세요(`--model claude-sonnet-4-6`).

---

## 출력 검증 규칙

`validators.py` 는 AI 응답을 받은 뒤 다음을 강제합니다.

| 항목 | 규칙 | 위반 시 동작 |
|---|---|---|
| 커밋 제목 | hard max 72자 | `…` 와 함께 71자로 잘라내고 `[WARN]` 발행 |
| 커밋 제목 | soft max 50자 권장 | 자르지 않고 `[WARN]` 만 발행 |
| 커밋 본문 | 불릿 1개 이상 | 불릿이 없으면 `[WARN]` 발행 (자르지 않음) |
| PR 제목 | max 80자 | `…` 와 함께 79자로 잘라내고 `[WARN]` 발행 |
| PR 본문 | `## Why` / `## What` / `## How to Test` 헤더 필수 | 누락 섹션은 `자리표시자` 와 함께 자동 추가하고 `[WARN]` 발행 |
| PR 본문 | 각 섹션 ≥1 불릿 | 불릿 없는 섹션엔 자리표시자 불릿을 자동 주입하고 `[WARN]` 발행 |

사용자가 결과를 보고 직접 다듬는 것이 최종 결정이라는 전제 위에서, "구조를
무너뜨리지 않고 경고만 띄우는" 후처리를 채택했습니다. AI 응답을 다시 호출해
재생성하지 않으므로 1회 호출 제약을 그대로 지킵니다.

---

## safe-mode 와 보안 운영

`git diff` 가 API 키·세션 토큰·이메일·개인키 같은 민감정보를 그대로 외부
LLM 으로 흘려보낼 수 있다는 점을 기본 가정으로 둡니다. `--safe-mode` 를
켜면 두 가지가 동시에 적용됩니다.

### (A) 정규식 마스킹

| 패턴 | 예시 입력 | 마스킹 결과 |
|---|---|---|
| Provider 키(sk-/sk-ant-/ghp_/AKIA/xox*) | `sk-ant-api03-AbCdEf...gh` | `sk-***gh` |
| `Authorization: Bearer ...` | `Bearer eyJabc...sig` | `Bearer ***MASKED***` |
| 키=값 형 비밀 (api_key, secret, password 등) | `password = "super_secret"` | `password=***MASKED***` |
| JWT (3-세그먼트 base64url) | `eyJabc.eyJ.sig` | `eyJ***ig` |
| 이메일 | `hee.jun.kim+admin@example.com` | `h***@example.com` |
| PEM PRIVATE KEY 블록 | `-----BEGIN ... PRIVATE KEY-----` 전체 | 한 줄 `***MASKED***` 로 치환 |

전체 패턴 목록은 `aigitgen/safe_mode.py` 의 `_PATTERNS` 를 보세요.

### (B) 분량 제한

- `--max-files N` (기본 10): diff 를 파일 단위로 잘라 상위 N 개만 전송
- `--max-lines N` (기본 200): 누적 라인 수가 N 을 넘으면 거기서 자르기
- 잘린 부분은 `[...K개 파일 ... 생략됨...]` / `[...총 X줄 중 Y줄까지
  전송...]` 로 명시되어 모델이 잘린 사실을 인지하게 합니다.

### 사용 시점

- 외부 LLM 정책상 비밀 유출 위험이 있는 저장소는 항상 `--safe-mode` 권장
- 매우 큰 PR(수천 줄) 은 토큰 비용 통제용으로도 유용
- 마스킹 통계는 INFO 로그에 함께 표시되어 어떤 패턴이 몇 건 잡혔는지 확인 가능

```
[INFO] safe-mode 적용: 파일 5/12, 라인 198/420, 마스킹 6건 {'api_key_prefixed': 3, 'bearer': 1, 'kv_secret': 1, 'email': 1}
```

### 적용 전/후 비교 (evidence/safe_mode_demo.txt)

```
# 적용 전 (원본 diff 일부)
+ANTHROPIC_API_KEY = "sk-ant-api03-AbCdEf1234567890_qwertyuiopasdfgh"
+ADMIN_EMAIL = "hee.jun.kim+admin@example.com"
+password = "super_secret_db_pwd_2026"
+Authorization: Bearer eyJabc.eyJpc3MiOiJtZSJ9.signature1234

# 적용 후 (safe-mode ON)
+ANTHROPIC_API_KEY = "sk-***gh"
+ADMIN_EMAIL = "h***@example.com"
+password=***MASKED***
+Authorization: Bearer ***MASKED***
```

---

## 비용 / 요청 횟수 정책

- **1 실행 = 1 API 호출** 을 원칙으로 합니다. `commit` 도 `pr` 도 다중 호출
  없이 단일 응답에서 모든 결과를 얻도록 프롬프트가 설계되어 있습니다.
- 호출이 끝나면 `[INFO] AI API 호출 횟수: 1회` 와 토큰/지연/모델을
  반드시 로그로 남겨 비용 추적이 가능합니다.
- 기본 모델은 비용 친화적인 `claude-haiku-4-5-20251001` 입니다. 평균
  PR 1건(diff ~400줄)이 입력 토큰 3,000~5,000 / 출력 400~600 수준에서
  처리되며 Haiku 단가 기준 1회당 수 cent 내외입니다.
- 큰 diff 가 우려되는 환경에서는 `--safe-mode --max-lines 200` 으로
  입력을 강제로 한도 내로 묶어 비용 폭주를 막을 수 있습니다.

---

## Docker 로 재현 (선택)

평가자 환경의 Python·Git 버전 차이를 우회하기 위해 Dockerfile 을
포함했습니다. 이 도구는 호스트의 저장소를 읽어야 하므로 컨테이너에
저장소를 bind mount 합니다.

```bash
# 1) 이미지 빌드
docker build -t ai-gitgen .

# 2) 호스트 저장소를 /repo 로 mount 하고 commit 실행
docker run --rm -it \
  -v "$(pwd):/repo" \
  -e AI_API_KEY="$AI_API_KEY" \
  ai-gitgen commit

# 3) PR 초안
docker run --rm -it \
  -v "$(pwd):/repo" \
  -e AI_API_KEY="$AI_API_KEY" \
  ai-gitgen pr --base main
```

> Windows PowerShell 에서 `$(pwd)` 대신 `${PWD}` 를 사용하세요.

---

## evidence/ 폴더

평가자가 README 만 보고도 결과를 확인할 수 있도록 다음 캡처를 보관합니다.

| 파일 | 캡처한 시나리오 |
|---|---|
| `evidence/help.txt` | `python main.py --help` 및 각 서브커맨드 `--help` |
| `evidence/dry_run_commit.txt` | `python main.py commit --dry-run` 의 system + user 프롬프트 |
| `evidence/dry_run_pr.txt` | `python main.py pr --dry-run` 의 system + user 프롬프트 |
| `evidence/safe_mode_demo.txt` | 합성 diff 에 `apply_safe_mode()` 를 적용한 마스킹 결과 + 통계 |
| `evidence/error_no_api_key.txt` | 환경변수 미설정 시 정상적으로 안내 후 종료하는지 |
| `evidence/no_changes.txt` | 변경 없는 저장소에서 commit 명령 시 안내 후 종료 |

API 키가 필요한 실제 응답 캡처는 외부 비용/키 관리를 고려해 기본 evidence
에는 포함하지 않았습니다. 평가자가 자신의 키로 동일 명령을 실행하면 위
"사용 예시" 의 출력 형태 그대로(헤더·구획선·검증 로그 포함) 결과가
재현됩니다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `[ERROR] AI_API_KEY ... 설정되지 않았습니다` | 환경변수가 비어 있음. PowerShell/Bash 예시대로 설정 후 재실행. |
| `[ERROR] AI API 인증 실패` | 키가 잘못되었거나 만료. Anthropic 콘솔에서 키 재발급. |
| `[ERROR] AI API 호출이 속도 제한에 걸렸습니다` | 분당 호출 한도 초과. 잠시 대기 후 재시도. |
| `[ERROR] AI API 서버에 접속할 수 없습니다` | 방화벽/네트워크 문제. 회사망/프록시 환경 확인. |
| `[ERROR] git ... 실패: not a git repository` | Git 저장소가 아닌 디렉터리에서 실행. `--cwd` 로 저장소를 지정하거나 `git init` 후 재시도. |
| 본문이 짧게 잘려 PR 섹션이 비어 옴 | `--max-tokens 2048` 로 늘리거나 `--safe-mode --max-lines 200` 으로 입력 줄이기. |
| 콘솔에 한글이 깨짐 | 본 도구는 stdout 을 UTF-8 로 재설정하지만, 외부 캡처(`tee` 등) 시 셸 인코딩에 의존합니다. PowerShell 7 / Windows Terminal 권장. |

---

## 운영 적용 시 우선순위 (다음 단계 로드맵)

이 도구를 실제 팀/리포지토리에 도입하면 곧바로 부딪치는 마찰점이 있습니다.
아래는 그 마찰을 기준으로 "**먼저 무엇을 더할지**" 를 우선순위와 근거까지
구체화한 로드맵입니다. 정렬 기준은 ① 도입 첫 주 사용자가 가장 자주 부딪치는
실 마찰, ② 구현 비용 대비 사용 빈도, ③ 외부 통합 여부(외부 통합은 권한·정책
승인 시간이 길어 후순위) 입니다.

| 우선순위 | 추가/개선 항목 | 근거 (왜 이 순서인가) | 영향 받는 모듈 |
|---|---|---|---|
| **P0** | **팀 컨벤션 외부 설정 파일 (`.ai-gitgen.yml`)** — Conventional Commits prefix 화이트리스트, scope 표기 규칙, PR 체크리스트 등을 yaml 로 외재화 | 도입 첫날 가장 자주 막히는 지점. 현재 `prompts.py` 의 system 메시지에 형식 규약이 박혀 있어 팀마다 다른 prefix(`feat/fix/chore` vs `feature/bugfix/...`)·이슈번호 표기·sign-off 규칙을 코드 수정 없이 반영할 수 없음. yaml 로드 → 프롬프트 변수 치환 한 단계만 추가하면 됨 (작은 비용, 매 호출에 영향) | `prompts.py`, 신규 `config.py` |
| **P0** | **PR 본문에 리포지토리 `.github/PULL_REQUEST_TEMPLATE.md` 머지** — 기존 팀 템플릿의 체크리스트·이슈 링크 자리를 보존하고 Why/What/How to Test 만 채워넣기 | 현재 출력은 "도구가 정한 3섹션 PR" 이라 GitHub PR 템플릿이 있는 저장소에서는 리뷰어가 체크리스트 누락을 이유로 PR 을 반려하는 일이 발생. 템플릿 파일을 읽고 placeholder 매칭으로 합치는 후처리만 필요 | `validators.py`, `render.py` |
| **P1** | **원격 반영 자동화 — `gh pr create` 래핑 또는 GitHub REST API 직접 호출** — 현재 출력된 PR 초안을 사용자가 복사해서 웹 UI 에 붙여넣는 단계를 없앰 | 본 과제 범위에서 의도적으로 제외한 부분. 실제 도입 시 가장 큰 ROI 가 나는 영역이지만, GitHub Token 권한·조직 정책 승인이 필요해 P0 보다 한 단계 뒤. 도구 자체보다 토큰·권한 관리 설계가 더 큰 작업이라 P1 | 신규 `gh_client.py`, `cli.py` |
| **P1** | **대규모 변경 분할 호출 (chunked summarization)** — 파일 그룹 단위로 부분 요약을 먼저 만들고 메타 요약 단계에서 합치기 | 현재는 `--max-lines 200` 으로 잘라 보내는데, 1,000+ 줄 PR 에서는 본문이 "X 외 다수 변경" 수준으로 부실해짐. 단, 다중 호출이 되므로 1회 호출 원칙(현재 정책)을 깨야 하고 비용도 N 배가 됨. 도입 빈도가 큰 변경 PR 에서만 필요해 P1. `--chunked` 옵션으로 명시 활성화하는 형태를 권장 | `cli.py`, `ai_client.py`, 신규 `chunker.py` |
| **P2** | **Pre-commit / Git hook 통합** — `git commit` 직전 또는 `git push` 직전에 도구가 자동 실행되어 메시지·PR 초안을 클립보드/에디터에 주입 | "도구를 잊고 그냥 평소처럼 커밋해버리는" 사용자 패턴을 차단. 다만 hook 은 사용자 개인 환경 설정이라 팀 단위 강제가 어렵고, 가끔 끄고 싶은 시점도 많아 P2. 별도 `aigitgen install-hook` 서브커맨드로 옵트인 설치하는 형태 | 신규 hook 스크립트, `cli.py` |
| **P2** | **다국어 출력 옵션 (`--lang en\|ko\|ja`)** — 현재 한국어 고정. 다국적 팀/오픈소스 리포지토리는 영어 PR 본문 필요 | 회사 내부 한국어 PR 만 쓰는 환경에서는 영향 없음. 글로벌 팀에서만 필수. system 프롬프트에 language 지시 1줄만 더하면 되지만, 후처리 검증 메시지(`[WARN]` 키워드 등) 도 같이 다국어화 해야 해서 변경 폭이 작지 않음 | `prompts.py`, `validators.py`, `render.py` |
| **P3** | **safe-mode 패턴 외부화 & 사내 비밀 패턴 추가** — 현재 `safe_mode.py` 의 `_PATTERNS` 에 회사 고유 패턴(내부 사번, 사내 토큰 prefix, 내부 도메인 등)을 추가하려면 코드 수정이 필요. `.ai-gitgen.yml` 의 `patterns:` 섹션으로 옮겨 정규식·치환 토큰만 적어도 확장되게 함 | 보안 위험도가 높은 영역이지만 현재도 기본 패턴은 OWASP 빈출 비밀을 거의 잡고 있음. 회사 고유 비밀이 다양해진 시점에 필요해서 P3. P0 의 yaml 설정 파일이 들어간 뒤에야 자연스럽게 얹는 작업 | `safe_mode.py`, `config.py` |
| **P3** | **결과 캐싱 / 비용 한도 가드** — 동일 diff·동일 파라미터에 대해 24h 캐시, 일일 토큰 사용량 누적 한도 초과 시 호출 차단 | 현재도 1회 호출 원칙·토큰 로그는 있어 비용이 폭주하진 않음. CI 에서 도구가 매 PR 마다 자동 호출되는 시나리오가 정착된 뒤에야 필요해서 가장 뒤 | 신규 `cache.py`, `ai_client.py` |

### 우선순위 결정 근거 요약

- **P0 두 가지는 "도입 첫 PR" 에서 곧바로 깨질 부분** 이라 가장 먼저 처리합니다.
  컨벤션 외재화 없이는 매 저장소마다 코드를 갈아엎어야 하고, PR 템플릿 머지
  없이는 리뷰어 단계에서 PR 자체가 반려됩니다.
- **P1 두 가지는 큰 ROI 지만 외부 의존(GitHub Token, 다중 호출 정책 변경)이
  있어** P0 컨벤션 정착 이후로 미룹니다. 외부 의존이 들어가면 검증·롤백 비용
  도 같이 커집니다.
- **P2 / P3 는 "쓰면 좋지만 빠져도 사용자가 우회 가능"한 항목들** 입니다.
  도구가 팀 안에서 자리 잡았는지를 본 다음에 결정합니다.

이 순서는 본 저장소의 `aigitgen/` 모듈 분리(특히 `prompts.py` / `validators.py`
/ `safe_mode.py` 가 책임 단위로 쪼개진 점)를 전제로 한 것입니다. 각 항목의
"영향 받는 모듈" 컬럼이 그대로 다음 PR 의 작업 범위가 되며, P0 항목 두 개는
모두 1~2일 분량의 작은 PR 로 분리해 머지 가능합니다.

---

## 제약과 책임

- `git push`, GitHub PR 자동 생성(REST API 연동) 같은 원격 반영은 구현
  범위에 포함하지 않습니다. 본 도구는 **초안 텍스트 출력까지** 가 목표입니다.
  실제 도입 시 가장 먼저 추가해야 할 통합인지에 대한 우선순위 근거는 바로 위
  "운영 적용 시 우선순위" 표의 P1 항목을 참고하세요.
- 생성된 커밋/PR 문구는 최종 정답이 아닙니다. 반드시 사용자가 검토·수정한
  뒤 적용하세요. safe-mode 의 정규식 마스킹도 모든 형태의 비밀을 잡아
  내지는 못하므로, 비밀이 의심되는 변경은 별도 점검을 권장합니다.
