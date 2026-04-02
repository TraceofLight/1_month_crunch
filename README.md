# Mini NPU Simulator 제출 보고서

## 1. 프로젝트 개요
이 프로젝트는 정사각 행렬 기반의 간단한 MAC(Multiply-Accumulate) 연산으로 패턴을 판별하는 Mini NPU Simulator를 구현한 과제입니다. 사용자는 3x3 필터와 입력 패턴을 직접 넣어 결과를 확인할 수 있고, `data.json`에 저장된 패턴 묶음을 일괄 분석해 정답 여부와 성능 측정 결과를 함께 확인할 수 있습니다.

핵심 목표는 다음과 같습니다.
- Cross(+) 패턴과 X 패턴 필터 생성
- 2차원 MAC 연산과 1차원 평탄화 MAC 연산 구현
- 수동 입력 모드와 `data.json` 분석 모드 제공
- 실패 케이스를 포함한 결과 리포트와 성능 비교 제공

## 2. 실행 환경
- OS: Windows 11 IoT Enterprise LTSC 2024
- Shell: bash
- Python: 3.12.10
- 사용 라이브러리: Python 표준 라이브러리만 사용 (`json`, `re`, `dataclasses`, `pathlib`, `time`, `unittest`)

별도 패키지 설치 없이 바로 실행 가능합니다.

## 3. 실행 방법
### 3-1. 프로그램 실행
```bash
python main.py
```

실행 후 메뉴에서 다음 중 하나를 선택합니다.
- `1`: 사용자 입력(3x3) 모드
- `2`: `data.json` 분석 모드

### 3-2. 테스트 실행
```bash
python -m unittest -v
```

## 4. 파일 구조
- `d:/Projects/Github/1_month_crunch/.worktrees/e1-3-mini-npu/main.py`  
  Mini NPU Simulator 본체. 행렬 검증, 패턴 생성, MAC 연산, JSON 분석, 콘솔 UI를 포함합니다.
- `d:/Projects/Github/1_month_crunch/.worktrees/e1-3-mini-npu/data.json`  
  필터 데이터와 테스트 패턴 데이터가 들어 있는 기본 입력 파일입니다.
- `d:/Projects/Github/1_month_crunch/.worktrees/e1-3-mini-npu/tests/test_main.py`  
  핵심 기능을 검증하는 단위 테스트 파일입니다.
- `d:/Projects/Github/1_month_crunch/.worktrees/e1-3-mini-npu/README.md`  
  본 제출 보고서입니다.
- `d:/Projects/Github/1_month_crunch/.worktrees/e1-3-mini-npu/docs/`  
  계획 및 보조 문서가 위치하는 디렉터리입니다.

## 5. 구현 요약
구현된 내용은 다음과 같습니다.
- `Matrix` 데이터 클래스로 정사각 행렬 여부를 검증
- 홀수 크기 `N x N`에 대해 Cross 패턴과 X 패턴 필터 생성
- 2차원 MAC(`mac_2d`)과 1차원 평탄화 MAC(`mac_1d`) 구현
- 점수 비교 후 `Cross`, `X`, `UNDECIDED`를 반환하는 판정 로직 구현
- `data.json` 전체 케이스 분석 및 실패 사유 집계 구현
- 성능 측정을 위한 벤치마크 기능 구현
- 콘솔 입력 오류 재시도와 기본 `data.json` 자동 생성 기능 구현

현재 구현 기준 `data.json` 분석 결과는 다음과 같습니다.
- 총 테스트: 8
- 통과: 6
- 실패: 2

## 6. 핵심 기능 설명
### 6-1. 행렬 검증
`Matrix`는 빈 행렬을 거부하고, 모든 행의 길이가 동일한 정사각 행렬인지 검사합니다. 정사각 조건을 만족하지 않으면 `ValueError("matrix must be square")`를 발생시킵니다.

### 6-2. 패턴 생성
- `generate_cross_pattern(size)`: 중앙 행과 중앙 열이 1인 Cross(+) 패턴 생성
- `generate_x_pattern(size)`: 두 대각선이 1인 X 패턴 생성

두 함수 모두 `3 이상`의 `홀수 크기`만 허용합니다.

### 6-3. MAC 연산
- `mac_2d(pattern, filter_matrix)`: 2차원 중첩 반복문으로 MAC 계산
- `mac_1d(pattern_flat, filter_flat)`: 평탄화된 1차원 리스트 기준으로 MAC 계산

둘 다 같은 수학적 결과를 내며, 구현에서는 성능 비교를 위해 두 방식을 모두 제공합니다.

### 6-4. 판정 로직
- Cross 점수와 X 점수를 비교해 더 큰 쪽을 결과로 선택합니다.
- 두 값 차이가 `EPSILON`보다 작으면 동점으로 보고 `UNDECIDED`를 반환합니다.

### 6-5. 실행 모드
- 수동 입력 모드: 사용자가 3x3 필터 A, 필터 B, 패턴을 직접 입력
- JSON 분석 모드: `data.json`의 모든 케이스를 순회하며 결과, 요약, 성능표 출력

## 7. data.json 구조 설명
`data.json`은 최상위에 `filters`, `patterns` 두 영역으로 구성됩니다.

### 7-1. filters
크기별 필터 세트를 저장합니다.
- `size_5`
- `size_13`
- `size_25`

각 크기 안에는 다음 두 필터가 있습니다.
- `cross`: Cross(+) 기준 필터
- `x`: X 기준 필터

즉, 구조는 아래와 같습니다.
```json
{
  "filters": {
    "size_5": {
      "cross": [[...]],
      "x": [[...]]
    }
  }
}
```

### 7-2. patterns
분석 대상 입력 패턴과 기대 라벨을 저장합니다.
- 예: `size_5_1`, `size_13_3`, `size_25_3`
- 각 항목은 `input`, `expected`를 가집니다.

```json
{
  "patterns": {
    "size_13_3": {
      "input": [[...]],
      "expected": "x"
    }
  }
}
```

구현상 `expected`는 `+`, `cross`, `x` 같은 입력을 받아 내부적으로 `Cross` 또는 `X`로 정규화합니다.

## 8. 결과 리포트
### 8-1. 수동 입력 모드 실행 결과
다음 명령으로 최종 결과를 확인했습니다.

```bash
printf "1\n0 1 0\n1 1 1\n0 1 0\n1 0 1\n0 1 0\n1 0 1\n1 0 1\n0 1 0\n1 0 1\n" | python main.py
```

실측 결과는 다음과 같습니다.
- A 점수: 1.0
- B 점수: 5.0
- 연산 시간(평균/10회, 2D): 0.000670 ms
- 연산 시간(평균/10회, 1D): 0.000410 ms
- 최종 판정: B

즉, 입력 패턴은 필터 B와 더 높은 유사도를 보여 `B`로 판정되었습니다.

### 8-2. data.json 분석 모드 실행 결과
다음 명령으로 전체 데이터셋을 분석했습니다.

```bash
printf "2\n" | python main.py
```

케이스별 실측 결과는 다음과 같습니다.
- `size_5_1`: Cross=9.0, X=1.0, 판정=Cross, expected=Cross, PASS
- `size_5_2`: Cross=1.0, X=9.0, 판정=X, expected=X, PASS
- `size_13_1`: Cross=25.0, X=1.0, 판정=Cross, expected=Cross, PASS
- `size_13_2`: Cross=1.0, X=25.0, 판정=X, expected=X, PASS
- `size_13_3`: Cross=13.0, X=13.0, 판정=UNDECIDED, expected=X, FAIL
- `size_25_1`: Cross=49.0, X=1.0, 판정=Cross, expected=Cross, PASS
- `size_25_2`: Cross=1.0, X=49.0, 판정=X, expected=X, PASS
- `size_25_3`: FAIL, reason=`matrix must be square`

최종 요약은 다음과 같습니다.
- total: 8
- passed: 6
- failed: 2

### 8-3. 실패 케이스 분석
#### `size_13_3`
이 케이스는 Cross 패턴과 X 패턴을 절반씩 섞은 입력입니다. 실제 계산 결과 Cross 점수와 X 점수가 모두 `13.0`으로 동일하게 측정되었습니다. 구현은 동점일 때 `UNDECIDED`를 반환하도록 되어 있으므로, 기대값 `X`와 일치하지 않아 실패했습니다.

#### `size_25_3`
이 케이스는 의도적으로 마지막 행 길이가 줄어든 비정사각 행렬입니다. `Matrix` 검증 단계에서 정사각 행렬이 아니라고 판단해 `matrix must be square` 예외가 발생하고, 분석 리포트에는 해당 사유가 실패 원인으로 기록됩니다.

## 9. 성능 분석
`data.json` 분석 모드에서 출력된 실측 성능표는 아래와 같습니다.

| 크기 | 2D 평균(ms) | 1D 평균(ms) | 연산 횟수 |
| --- | ---: | ---: | ---: |
| 3x3 | 0.000680 | 0.000410 | 9 |
| 5x5 | 0.001250 | 0.000580 | 25 |
| 13x13 | 0.006130 | 0.003230 | 169 |
| 25x25 | 0.019880 | 0.014360 | 625 |

분석 내용은 다음과 같습니다.
- 두 구현 모두 행렬의 모든 원소를 한 번씩 순회하므로 시간 복잡도는 `O(N^2)`입니다.
- 실제 연산 횟수도 `N x N`으로 증가하며, 3x3에서 25x25로 갈수록 실행 시간이 함께 증가했습니다.
- 같은 데이터에 대해 1D 평탄화 방식이 모든 측정 구간에서 2D 방식보다 더 낮은 평균 시간을 보였습니다.
- 따라서 현재 구현의 보너스 포인트 성격의 최적화 요소는 `flatten()` 기반 1D MAC 비교 기능과, 이를 수치로 확인할 수 있는 벤치마크 출력입니다.

추가 보너스 성격의 구현 요소는 다음과 같습니다.
- 입력 형식 오류 발생 시 전체 3줄 입력을 다시 받는 콘솔 재시도 로직
- `data.json`이 없으면 기본 데이터를 자동 생성하는 초기화 로직
- 실패 케이스의 원인을 문자열로 명확히 남기는 리포트 구조

## 10. 테스트 및 검증
다음 명령으로 단위 테스트를 수행했습니다.

```bash
python -m unittest -v
```

검증 결과:
- 총 10개 테스트 실행
- 결과: `OK`

테스트는 다음 범주를 검증합니다.
- 정사각 행렬 검증
- 라벨 정규화
- Cross/X 패턴 생성
- 2D MAC와 1D MAC 일치성
- 동점 처리(`UNDECIDED`)
- 벤치마크 결과의 유효성
- 기본 `data.json` 생성
- 분석 결과 요약(total 8 / passed 6 / failed 2)
- 콘솔 입력 검증과 재시도 흐름

## 11. 트러블슈팅 / 배운 점
- 동점 케이스는 단순 오분류가 아니라, 실제로 두 필터 점수가 같은 경우임을 확인했습니다. 따라서 `size_13_3` 실패는 구현 버그라기보다 판정 정책의 결과입니다.
- 입력 데이터 검증을 일찍 수행하면, `size_25_3`처럼 잘못된 형식의 데이터도 빠르게 차단하고 명확한 실패 사유를 남길 수 있습니다.
- 같은 `O(N^2)` 연산이라도 데이터 접근 방식에 따라 실행 시간이 달라질 수 있음을 2D/1D 비교로 확인했습니다.
- 과제 제출 문서는 구현과 정확히 일치해야 하므로, README에는 실제 실행 결과와 테스트 결과만 반영했습니다.
