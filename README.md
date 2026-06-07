# 파일 기반 가계부 콘솔 프로그램

수입과 지출 내역을 파일에 영구 저장하고, 추가/목록/검색/수정/삭제, 월별 요약,
예산 관리, 카테고리 관리, CSV 가져오기/내보내기를 제공하는 콘솔 애플리케이션이다.
표준 라이브러리만으로 구현했으며, 제너레이터 스트리밍, 데코레이터를 통한 공통
관심사 분리, 타입 힌트, 계층형 모듈 구조를 적용했다. 아래 본문은 각 요구사항의
실제 구현 코드를 파일/메서드와 함께 인용하고, `evidence/` 의 실행 로그 줄 번호를
근거로 제시하는 자체완결형 워크스루다.

## 목차

- [개발 환경과 제약](#개발-환경과-제약)
- [빠른 시작](#빠른-시작)
- [아키텍처와 모듈 구조](#아키텍처와-모듈-구조)
- [데이터 모델](#데이터-모델)
- [저장 파일 위치와 형식](#저장-파일-위치와-형식)
- [기능별 워크스루](#기능별-워크스루)
- [제너레이터 스트리밍 설계](#제너레이터-스트리밍-설계)
- [데코레이터로 공통 관심사 분리](#데코레이터로-공통-관심사-분리)
- [타입 힌트로 입출력 계약 명확화](#타입-힌트로-입출력-계약-명확화)
- [입력 검증, 오류 처리, 종료 코드](#입력-검증-오류-처리-종료-코드)
- [저장 안정성: 원자적 교체](#저장-안정성-원자적-교체)
- [import / export CSV 스키마](#import--export-csv-스키마)
- [설계 결정 고정 사항](#설계-결정-고정-사항)
- [보너스 기능](#보너스-기능)
- [테스트](#테스트)
- [Docker 로 재현](#docker-로-재현)
- [검증 산출물(evidence)](#검증-산출물evidence)
- [트러블슈팅](#트러블슈팅)

## 개발 환경과 제약

- Python 3.10 이상(개발/검증은 3.12.10).
- 외부 라이브러리를 설치하지 않는다. 표준 라이브러리만 사용한다(`pip install` 불필요).
- 저장 포맷은 JSONL 을 사용하며, 파일을 용도별로 3개 이상 분리한다.
- 모든 옵션은 리눅스 표준인 이중 대시(`--`)로 통일한다. 예: `--help`, `--limit`,
  `--from`, `--to`, `--month`.

## 빠른 시작

저장소 루트에서 실행한다.

```bash
# 전체 도움말
python -m budget_app --help

# 명령별 도움말(모든 명령이 --help 지원)
python -m budget_app add --help
python -m budget_app summary --help

# 거래 추가(대화형) / 조회(옵션)
python -m budget_app add
python -m budget_app list --limit 10
python -m budget_app summary --month 2024-01 --top 3
```

전체 기능을 한 번에 시연하고 검증 산출물을 만드는 단일 진입점은 다음과 같다.

```bash
python scripts/run_demo.py
```

이 스크립트는 깨끗한 `./data` 폴더에서 10개 기능을 순서대로 실행한 뒤, 실행 로그와
도움말, 저장 파일 내용, 오류 처리, 단위 테스트 결과를 `evidence/` 아래에 저장한다.
저장 폴더는 `--data-dir` 옵션으로 변경할 수 있다(기본값 `./data`).

`python -m budget_app` 진입점은 `budget_app/__main__.py` 가 CLI 의 `main` 을
호출하고 그 종료 코드로 프로세스를 끝내는 구조다.

```python
# budget_app/__main__.py
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

## 아키텍처와 모듈 구조

한 파일에 모든 코드를 몰아넣지 않고, 책임에 따라 다음과 같이 9개 모듈로 분리했다
(요구사항: 최소 3개 이상 모듈, 권장 CLI/서비스/저장소/모델 분리).

```
budget_app/
  __main__.py    : python -m budget_app 진입점
  cli.py         : argparse 정의, 대화형 입력, 명령 분기, 종료 코드
  services.py    : 도메인 로직(검증, 집계, 가져오기/내보내기) - BudgetService
  repository.py  : 파일별 저장소(거래/카테고리/예산/반복) - 파일 1개당 클래스 1개
  storage.py     : 저수준 파일 I/O(스트리밍 읽기, 원자적 쓰기)
  models.py      : 데이터 구조(dataclass)
  decorators.py  : 공통 관심사(로그/시간 측정/예외 처리) 데코레이터
  formatting.py  : 콘솔 출력 포맷터(표 정렬)
  errors.py      : 사용자 대상 예외(원인 + 힌트)
```

계층의 책임은 다음과 같다. CLI 계층은 입출력과 사용자 대화만 담당하고 업무 규칙을
모른다. 서비스 계층은 검증과 집계 같은 업무 규칙을 한곳에 모은다. 저장소 계층은
모델과 파일의 매핑만 담당하며, 다시 도메인을 모르는 저수준 I/O(storage)에 의존한다.
서비스의 생성자(`budget_app/services.py` 의 `BudgetService.__init__`)가 4개 저장소를
조립하는 부분에서 이 구조가 드러난다.

```python
# budget_app/services.py - BudgetService.__init__
def __init__(self, data_dir: Path) -> None:
    self.data_dir = data_dir
    self.transactions = TransactionRepository(data_dir / "transactions.jsonl")
    self.categories = CategoryStore(data_dir / "categories.jsonl")
    self.budgets = BudgetStore(data_dir / "budgets.jsonl")
    self.recurring = RecurringStore(data_dir / "recurring.jsonl")
```

의존 방향을 한쪽으로 정리했으므로, 저장 포맷을 바꾸더라도 storage 와 repository 만
손대면 되고 서비스/CLI 는 영향을 받지 않는다.

## 데이터 모델

거래 내역(Transaction)은 `dataclass` 로 정의하며 요구된 필드(`id`, `type`, `date`,
`amount`, `category`, `memo`, `tags`)를 모두 포함한다. JSONL 직렬화 계약은
`to_dict`/`from_dict` 로 명시한다.

```python
# budget_app/models.py
@dataclass
class Transaction:
    id: str
    type: str            # income | expense
    date: str            # YYYY-MM-DD
    amount: int          # 양의 정수
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "date": self.date,
            "amount": self.amount, "category": self.category,
            "memo": self.memo, "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        return cls(
            id=str(data["id"]), type=str(data["type"]), date=str(data["date"]),
            amount=int(data["amount"]), category=str(data["category"]),
            memo=str(data.get("memo", "")), tags=list(data.get("tags", []) or []),
        )
```

모델은 `Transaction`, `Category`, `Budget`, `Recurring` 네 개의 dataclass 로
정의하고, 저장소/서비스 클래스(`TransactionRepository`, `CategoryStore`,
`BudgetStore`, `RecurringStore`, `BudgetService`)와 함께 두 개 이상의 클래스를
사용한다.

## 저장 파일 위치와 형식

기본 저장 폴더는 `./data` 이며, 용도별로 다음 4개 파일에 JSONL(한 줄에 JSON 객체
하나) 형식으로 저장한다. 거래/카테고리/예산 3개는 필수이고, 반복 내역은 보너스용
추가 파일이다. 실제 저장 결과는 evidence/data_files.txt 에서 확인할 수 있다.

| 파일 | 용도 | data_files.txt 줄 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | 6-14 |
| `data/categories.jsonl` | 카테고리 목록 | 19-24 |
| `data/budgets.jsonl` | 월별 예산 | 29-30 |
| `data/recurring.jsonl` | 반복 내역 규칙(보너스) | 35 |

evidence/data_files.txt 6-14 에 기록된 거래 파일의 실제 한 줄은 다음과 같다.

```json
{"id": "TX-000003", "type": "expense", "date": "2024-01-15", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal"]}
```

이 밖에 실행 로그가 `data/budget_app.log` 에, 백업이 `data/backups/` 아래에
생성된다. JSONL 을 고른 이유는 한 줄이 한 레코드라 추가가 append 한 번으로 끝나고,
손상이 한 줄에 국한되며, 줄 단위 스트리밍이 자연스럽기 때문이다. JSON 직렬화는
`ensure_ascii=False` 로 한글을 그대로 저장한다(`budget_app/repository.py` 의
`_dumps`). 초기 실행 시 파일이 없으면 자동 생성하고, 카테고리가 비어 있으면 기본
카테고리를 만든 뒤 안내한다(`CategoryStore.ensure_defaults`).

```python
# budget_app/repository.py - CategoryStore.ensure_defaults
DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")

def ensure_defaults(self) -> list[str]:
    if self.list():
        return []
    for name in DEFAULT_CATEGORIES:
        storage.append_line(self.path, _dumps(Category(name=name).to_dict()))
    return list(DEFAULT_CATEGORIES)
```

## 기능별 워크스루

각 기능은 사용 예시, 실제 구현 코드, evidence 줄 인용을 함께 제시한다.

### 1. add (거래 추가, 대화형)

날짜/타입/카테고리/금액/메모/태그를 순서대로 입력받고, 저장 후 생성된 id 를
출력한다. 잘못된 값에는 원인과 힌트를 출력하고 같은 항목을 다시 입력받는다
(evidence/demo_run.txt 34-57). 카테고리는 등록된 목록에 있어야 하며, 없으면 재입력을
요구한다.

```text
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001
```

CLI 핸들러(`budget_app/cli.py` 의 `cmd_add`)는 재입력 헬퍼 `_prompt_until` 로 각
필드를 검증하며 받고, 서비스에 위임한다.

```python
# budget_app/cli.py - cmd_add (발췌)
date = _prompt_until("날짜(YYYY-MM-DD): ", validate_date)
tx_type = _prompt_until("타입(income/expense): ", validate_type)
category = _prompt_until("카테고리: ", _category_validator(service))
amount = _prompt_until("금액(양수): ", validate_amount)
memo = _input_optional("메모(선택): ").strip()
tags = parse_tags(_input_optional("태그(쉼표로 구분, 없으면 엔터): "))
tx = service.create_transaction(date=..., type=..., category=..., amount=..., memo=memo, tags=tags)
print(f"[저장 완료] id={tx.id}")
```

서비스의 `create_transaction` 은 검증과 id 생성, append 저장을 담당한다.

```python
# budget_app/services.py - BudgetService.create_transaction
def create_transaction(self, *, date, type, category, amount, memo="", tags=None) -> Transaction:
    clean_date = validate_date(date)
    clean_type = validate_type(type)
    clean_amount = validate_amount(amount)
    self._require_category(category)
    tx = Transaction(
        id=self.transactions.next_id(), type=clean_type, date=clean_date,
        amount=clean_amount, category=category, memo=memo.strip(), tags=list(tags or []),
    )
    self.transactions.add(tx)
    return tx
```

id 는 기존 최대 일련번호 + 1 로 생성한다(`TransactionRepository.next_id`), 그래서
demo 에서 `TX-000001`, `TX-000002` 처럼 순차 발급된다.

### 2. list (목록, 최신순 스트리밍)

`--limit` 기본값은 20 이다. 최신순은 가장 최근에 입력한 순서(파일 append 역순)를
뜻한다(근거는 아래 스트리밍 설계 절). 출력은 evidence/demo_run.txt 63-69 와 같다.

```text
$ python -m budget_app list --limit 3
id        | date       | type    | category | amount  | memo | tags
-------------------------------------------------------------------
TX-000005 | 2024-01-22 | expense | food     | 30,000  | 외식 | meal
TX-000004 | 2024-01-18 | expense | rent     | 150,000 | 월세 |
TX-000003 | 2024-01-15 | expense | food     | 15,000  | 점심 | meal
```

```python
# budget_app/cli.py - cmd_list
transactions = service.list_transactions(limit=args.limit)
print(formatting.format_transactions(transactions))
```

`list_transactions` 는 역방향 제너레이터에서 limit 개만 취해 스트리밍을 유지한다.

```python
# budget_app/services.py - BudgetService.list_transactions
def list_transactions(self, limit: int) -> list[Transaction]:
    if limit <= 0:
        raise ValidationError("limit 은 1 이상이어야 합니다.", hint="예: --limit 10")
    return list(_take(self.transactions.iter_recent(), limit))
```

### 3. search (조건 검색, 최신순 스트리밍)

기간(`--from`, `--to`), 카테고리(`--category`), 타입(`--type`), 메모 키워드(`--q`),
태그(`--tag`), 개수 제한(`--limit`)을 지원하며 조건은 AND 결합이다. 실행 예는
evidence/demo_run.txt 75-95 에 있다(타입+카테고리, 기간, 태그 검색).

```text
$ python -m budget_app search --type expense --category food
$ python -m budget_app search --from 2024-01-15 --to 2024-01-31
$ python -m budget_app search --tag meal --q 점심 --limit 5
```

조건은 `SearchFilter` dataclass 로 표현하고, 한 거래에 대한 일치 판정을 `matches`
가 담당한다. 서비스의 `search` 는 역방향 제너레이터에 이 판정을 걸어 흘려보낸다.

```python
# budget_app/services.py - SearchFilter.matches
def matches(self, tx: Transaction) -> bool:
    if self.month and not tx.date.startswith(self.month):
        return False
    if self.date_from and tx.date < self.date_from:
        return False
    if self.date_to and tx.date > self.date_to:
        return False
    if self.category and tx.category != self.category:
        return False
    if self.type and tx.type != self.type:
        return False
    if self.query and self.query.lower() not in tx.memo.lower():
        return False
    if self.tag and self.tag not in tx.tags:
        return False
    return True

# budget_app/services.py - BudgetService.search (발췌)
matched = (tx for tx in self.transactions.iter_recent() if criteria.matches(tx))
if limit is not None:
    matched = _take(matched, limit)
return list(matched)
```

### 4. summary (월별 요약)

총수입, 총지출, 잔액과 카테고리별 지출 TOP N(`--top`, 기본 3)을 출력한다. 데이터가
없는 달은 "데이터 없음"을 명시한다. 예산이 있으면 사용률과 초과 경고를 함께 낸다.
정상 요약은 evidence/demo_run.txt 105-116, 초과 경고는 188-198 에 있다.

```text
$ python -m budget_app summary --month 2024-01 --top 3
[2024-01 요약]
총 수입: 3,000,000원
총 지출: 215,000원
잔액: 2,785,000원
예산: 500,000원 (사용률 43.0%)

지출 TOP 3
1) rent 150,000원
2) food 45,000원
3) transport 20,000원
```

집계는 전체 거래를 한 줄씩 스트리밍하며 누적한다(전체를 리스트로 만들지 않음).

```python
# budget_app/services.py - BudgetService.summarize (발췌)
for tx in self.transactions.iter_all():   # 스트리밍 누적
    if not tx.date.startswith(clean_month):
        continue
    has_data = True
    if tx.type == "income":
        total_income += tx.amount
    else:
        total_expense += tx.amount
        per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount
top_expenses = sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)[:top]
budget = self.budgets.get(clean_month)
if budget is not None and budget > 0:
    usage_rate = round(total_expense / budget * 100, 1)
    over_budget = total_expense > budget
```

데이터 없는 달은 evidence 외에 단위 테스트로도 검증한다(`test_summary_no_data`).

### 5. budget (예산 설정/조회)

예산은 `data/budgets.jsonl` 에 영구 저장되고 summary 에 반영된다
(evidence/demo_run.txt 101-103, 초과 시 194 줄의 경고).

```text
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500,000원
```

```python
# budget_app/services.py - BudgetService.set_budget
def set_budget(self, month, amount) -> tuple[str, int]:
    clean_month = validate_month(month)
    clean_amount = validate_amount(amount)
    self.budgets.set(clean_month, clean_amount)
    return clean_month, clean_amount
```

`BudgetStore.set` 은 같은 달이 있으면 덮어쓰고 원자적으로 다시 쓴다.

### 6. category (카테고리 관리)

`category add` 는 대화형이다. 삭제 시 사용 중이면 막고, `--into` 로 대체 카테고리를
주면 거래를 옮긴 뒤 삭제한다. 사용 예는 evidence/demo_run.txt 16-28, 사용 중 삭제
차단 오류는 evidence/errors.txt 37-40 에 있다.

```text
$ python -m budget_app category remove --name food --into cafe
[삭제 완료] category=food (거래 2건을 'cafe'로 이동)
```

```python
# budget_app/services.py - BudgetService.remove_category (발췌)
in_use = [tx for tx in self.transactions.iter_all() if tx.category == clean]
moved = 0
if in_use:
    if into is None:
        raise CategoryInUseError(
            f"'{clean}' 카테고리를 사용하는 거래가 {len(in_use)}건 있습니다.",
            hint="--into <대체카테고리> 로 거래를 옮긴 뒤 삭제하세요.",
        )
    records = list(self.transactions.iter_all())
    for tx in records:
        if tx.category == clean:
            tx.category = into_clean
            moved += 1
    self.transactions.replace_all(records)
self.categories.remove(clean)
return moved
```

### 7. update (거래 수정, 옵션 기반)

`--id` 로 대상을 정하고 함께 준 필드만 수정한다(나머지 유지). 수정할 필드를 하나도
주지 않거나 없는 id 면 오류로 종료한다. 실행 예는 evidence/demo_run.txt 122-131,
없는 타입 입력 오류는 evidence/errors.txt 46-49 에 있다.

```text
$ python -m budget_app update --id TX-000005 --amount 28000 --memo 외식수정
[수정 완료] id=TX-000005
```

```python
# budget_app/services.py - BudgetService.update_transaction (발췌)
records = list(self.transactions.iter_all())
target = next((tx for tx in records if tx.id == tx_id), None)
if target is None:
    raise NotFoundError(f"거래를 찾을 수 없습니다: {tx_id}",
                        hint="list 명령으로 존재하는 id 를 확인하세요.")
if date is not None:     target.date = validate_date(date)
if type is not None:     target.type = validate_type(type)
if amount is not None:   target.amount = validate_amount(amount)
if category is not None: self._require_category(category); target.category = category
if memo is not None:     target.memo = memo.strip()
if tags is not None:     target.tags = list(tags)
self.transactions.replace_all(records)   # 원자적 재작성
```

### 8. delete (거래 삭제)

없는 id 는 "없는 데이터"로 처리해 안내한다(evidence/demo_run.txt 137-148, 없는 id
오류는 evidence/errors.txt 19-22).

```text
$ python -m budget_app delete --id TX-000001
[삭제 완료] id=TX-000001
```

```python
# budget_app/services.py - BudgetService.delete_transaction
def delete_transaction(self, tx_id: str) -> Transaction:
    records = list(self.transactions.iter_all())
    kept = [tx for tx in records if tx.id != tx_id]
    if len(kept) == len(records):
        raise NotFoundError(f"거래를 찾을 수 없습니다: {tx_id}",
                            hint="list 명령으로 존재하는 id 를 확인하세요.")
    removed = next(tx for tx in records if tx.id == tx_id)
    self.transactions.replace_all(kept)   # 원자적 재작성
    return removed
```

### 9. import / export (CSV 가져오기/내보내기)

`export` 는 `--month` 또는 `--from`/`--to` 중 하나 이상을 필수로 받는다. `import`
는 각 행을 검증해 일괄 등록하고, 실패 행(잘못된 날짜/타입/금액, 등록되지 않은
카테고리)은 사유와 함께 건너뛴다. 실행 예는 evidence/demo_run.txt 154-161
(export 4건, import imported=3/skipped=1), 조건 누락 오류는 evidence/errors.txt
28-31 에 있다.

```text
$ python -m budget_app export --out evidence/export_2024-01.csv --month 2024-01
[완료] evidence/export_2024-01.csv (4 records)

$ python -m budget_app import --from samples/import_sample.csv
[완료] imported=3, skipped=1
  - 건너뜀 5행: 등록되지 않은 카테고리입니다: ghost
```

```python
# budget_app/services.py - BudgetService.import_csv (발췌)
reader = csv.DictReader(handle)
missing = [c for c in ("date", "type", "category", "amount")
           if c not in (reader.fieldnames or [])]
if missing:
    raise ValidationError(f"CSV 필수 열이 없습니다: {', '.join(missing)}",
                          hint="헤더는 date,type,category,amount,memo,tags 여야 합니다.")
for line_no, row in enumerate(reader, start=2):
    try:
        self.create_transaction(
            date=row["date"], type=row["type"], category=row["category"],
            amount=row["amount"], memo=row.get("memo", "") or "",
            tags=parse_tags(row.get("tags", "") or ""))
        imported += 1
    except (ValidationError, NotFoundError) as exc:
        skipped += 1
        reasons.append(f"{line_no}행: {exc.message}")
```

`export_csv` 는 검색 결과를 헤더와 함께 CSV 로 쓴다. 태그가 여러 개라 셀 안에
쉼표가 들어가면 `csv` 모듈이 자동으로 따옴표 처리하고, 가져올 때 `parse_tags` 가
다시 분리한다. 결과 CSV 견본은 evidence/export_2024-01.csv 에 있다.

## 제너레이터 스트리밍 설계

목록과 검색은 저장 파일 전체를 한 번에 메모리로 읽지 않고 제너레이터로 한 줄씩
스트리밍한다. 핵심은 `budget_app/storage.py` 의 두 제너레이터다. 앞에서부터 읽는
`iter_lines_forward` 는 요약처럼 전체를 훑어 누적하는 작업에, 끝에서부터 읽는
`iter_lines_reverse` 는 목록/검색의 "최신순"에 쓴다.

```python
# budget_app/storage.py - iter_lines_reverse
def iter_lines_reverse(path: Path, block_size: int = 8192) -> Iterator[str]:
    if not path.exists():
        return
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        position = handle.tell()
        carry = b""                       # 블록 경계에 걸친 미완성 앞부분 줄
        while position > 0:
            read_size = min(block_size, position)
            position -= read_size
            handle.seek(position)
            chunk = handle.read(read_size)
            carry = chunk + carry
            parts = carry.split(b"\n")
            carry = parts[0]              # 더 앞 블록과 이어질 수 있으므로 보류
            for raw in reversed(parts[1:]):
                text = raw.decode("utf-8").strip()
                if text:
                    yield text
        text = carry.decode("utf-8").strip()
        if text:
            yield text
```

거래는 입력 순서대로 파일 끝에 append 되므로, 끝에서부터 읽으면 가장 최근 입력이
먼저 나온다. 여기서 최신순은 날짜 정렬이 아니라 입력(append) 역순이다. 날짜 정렬은
모든 줄을 읽어 정렬해야 해서 스트리밍과 충돌하지만, append 역순은 끝에서 필요한
만큼만 읽으면 되어 스트리밍과 맞물린다. 보통 거래를 시간 순서대로 입력하므로 두
기준은 사실상 일치한다.

이 설계의 이점은 일부만 필요한 경우에 드러난다. 저장소는 제너레이터를 그대로
넘긴다(`budget_app/repository.py` 의 `iter_recent`).

```python
# budget_app/repository.py - TransactionRepository.iter_recent
def iter_recent(self) -> Iterator[Transaction]:
    for line in storage.iter_lines_reverse(self.path):
        yield Transaction.from_dict(_loads(line))
```

서비스의 `_take` 가 앞쪽 limit 개만 취하고 즉시 멈추므로(`return`), 파일이 수십만
줄이어도 마지막 부근 블록만 읽고 종료한다. 메모리와 읽는 바이트 수가 limit 에
비례하고 파일 크기와 무관하다.

```python
# budget_app/services.py - _take
def _take(iterator: Iterator[Transaction], limit: int) -> Iterator[Transaction]:
    for index, item in enumerate(iterator):
        if index >= limit:
            return            # 조기 종료 -> 파일 끝부분만 읽고 멈춤
        yield item
```

역방향 읽기와 블록 경계 처리는 단위 테스트로 검증한다
(`test_reverse_stream_yields_newest_first`, `test_reverse_stream_crosses_block_boundary`,
evidence/tests.txt).

## 데코레이터로 공통 관심사 분리

명령 처리 함수 본문은 "무엇을 하는가"에만 집중하고, 로그/시간 측정/예외 처리는
`budget_app/decorators.py` 의 데코레이터로 분리했다. 세 데코레이터는 독립적이라
자유롭게 조합한다.

```python
# budget_app/decorators.py
def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("호출 시작: %s", func.__name__)
        result = func(*args, **kwargs)
        logger.info("호출 종료: %s", func.__name__)
        return result
    return wrapper

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            logger.info("실행 시간: %s = %.2f ms", func.__name__,
                        (time.perf_counter() - start) * 1000)
    return wrapper

def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            result = func(*args, **kwargs)
            return 0 if result is None else int(result)
        except BudgetAppError as exc:
            print(f"[오류] {exc.message}", file=sys.stderr)
            if exc.hint:
                print(f"[힌트] {exc.hint}", file=sys.stderr)
            return exc.exit_code
    return wrapper
```

CLI 의 모든 명령 핸들러는 세 데코레이터를 쌓아 적용한다. 본문에는 업무 로직만 남는다.

```python
# budget_app/cli.py
@handle_errors
@timed
@log_call
def cmd_summary(args: argparse.Namespace) -> int:
    service = _build_service(args)
    summary = service.summarize(month=args.month, top=args.top)
    print(formatting.format_summary(summary))
    return 0
```

이렇게 분리하면 모든 명령에서 로그/시간/예외 코드를 반복하지 않아도 되고, 정책이
바뀌어도(예: 로그 포맷) 데코레이터 한 곳만 고치면 된다. 로그는 콘솔을 어지럽히지
않도록 `data/budget_app.log` 로 남긴다. `handle_errors` 가 종료 코드를 만들어 주는
덕분에 오류 처리와 종료 코드 정책이 한 곳에 모인다.

## 타입 힌트로 입출력 계약 명확화

모든 함수와 데이터 구조에 타입 힌트를 적용해 입출력 계약을 분명히 했다. 요약 결과는
dataclass 로 타입을 고정한다.

```python
# budget_app/services.py
def summarize(self, month: str, top: int) -> SummaryResult:
    ...

@dataclass
class SummaryResult:
    month: str
    total_income: int
    total_expense: int
    balance: int
    top_expenses: list[tuple[str, int]]
    budget: int | None
    usage_rate: float | None
    over_budget: bool
    has_data: bool
```

호출하는 쪽(`budget_app/formatting.py`)은 `SummaryResult` 의 필드 이름과 타입만 보고
안전하게 출력 코드를 작성한다. `budget: int | None` 처럼 "값이 없을 수 있음"을
타입에 드러내면 예산 미설정 상황을 빠뜨리지 않고 처리하게 된다. 검색 조건도 dict
대신 `SearchFilter` dataclass 로 표현해, 가능한 조건이 타입으로 문서화된다. 이런
명시적 계약은 IDE 자동완성과 정적 분석의 도움을 받게 하고, 잘못된 형태의 값이
계층 사이를 넘나드는 실수를 줄인다.

## 입력 검증, 오류 처리, 종료 코드

입력 검증은 서비스 계층에 모았다. 날짜 형식, 0 이하 금액, 허용되지 않은 타입,
등록되지 않은 카테고리를 각각 명확한 예외로 처리한다. 검증 헬퍼는 순수 함수다.

```python
# budget_app/services.py - validate_date
def validate_date(value: str) -> str:
    text = value.strip()
    try:
        parsed = dt.datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).",
                              hint="예: 2024-01-15") from exc
    return parsed.strftime("%Y-%m-%d")
```

모든 사용자 대상 예외는 원인과 힌트를 갖는다(`budget_app/errors.py`).

```python
# budget_app/errors.py
class BudgetAppError(Exception):
    exit_code: int = 1
    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
```

대화형 입력은 잘못된 값이면 원인과 힌트를 출력하고 같은 항목을 다시 받는다
(evidence/errors.txt 7-13). 모든 오류는 스택트레이스 대신 `[오류] 원인` 과
`[힌트] 해결 방법` 형태로 표준 에러에 출력하고, 정상 종료는 0, 오류 종료는 0이
아닌 값을 반환한다. 예상치 못한 예외도 최상위(`budget_app/cli.py` 의 `main`)에서
잡아 스택트레이스 없이 요약만 출력하고 상세는 로그에 남긴다. 오류별 종료 코드는
evidence/errors.txt 의 각 블록 끝 `[exit code] 1` 로 확인할 수 있다.

## 저장 안정성: 원자적 교체

추가는 append 한 번으로 끝나지만 수정/삭제는 파일을 다시 써야 한다. 이때
`budget_app/storage.py` 의 `atomic_write_lines` 로, 같은 폴더의 임시 파일에 전체를
쓰고 `fsync` 한 뒤 `os.replace` 로 교체한다. `os.replace` 는 같은 파일시스템에서
원자적이라, 쓰는 도중 중단돼도 원본이 반쯤 덮어써진 손상 상태로 남지 않는다.

```python
# budget_app/storage.py - atomic_write_lines
def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            for line in lines:
                handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
```

`TransactionRepository.replace_all`, `CategoryStore.remove`, `BudgetStore.set` 이 모두
이 방식을 사용한다.

## import / export CSV 스키마

가져오기와 내보내기는 동일 스키마를 고정한다. 인코딩은 UTF-8 이고 헤더를 포함한다.
견본은 samples/import_sample.csv 에 있다.

| column | required | 설명 |
| --- | --- | --- |
| date | Y | `YYYY-MM-DD` |
| type | Y | `income` 또는 `expense` |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(`,`)로 구분한 문자열 |

태그가 두 개(`taxi`, `night`)이면 CSV 에는 `"taxi,night"` 로 기록되고, 가져올 때
다시 두 태그로 분리된다. 내보내기 결과는 evidence/export_2024-01.csv 에 있다.

## 설계 결정 고정 사항

요구사항이 선택지를 준 항목은 다음과 같이 고정했다.

- update 입력 방식: 옵션 기반(안 A). `update --id <id>` 에 수정할 필드만 옵션으로
  준다. 어떤 필드를 바꿀지 명시적이고 스크립트/재현에 유리해서다.
- 카테고리 파일이 비어 있을 때: 기본 카테고리 자동 생성(안 A). 첫 실행 시
  `food`, `transport`, `rent`, `salary`, `etc` 를 만들고 안내한다.
- 카테고리 삭제 시 사용 중 처리: 기본은 삭제를 막고, `--into` 로 대체 카테고리를
  주면 거래를 옮긴 뒤 삭제한다(둘 다 지원).
- "최신순"의 정의: 입력(append) 역순. 스트리밍과 양립시키기 위한 선택이며 위에서
  근거를 설명했다.

## 보너스 기능

- 백업(`backup`): 타임스탬프 폴더(`data/backups/backup-YYYYMMDD-HHMMSS`)에 저장
  파일을 복사한다(evidence/demo_run.txt 204-206).
- 반복 내역(`recurring add`/`recurring apply`): 월세/월급처럼 반복되는 내역을 규칙으로
  등록하고 특정 월에 적용해 거래를 자동 생성한다. 같은 규칙을 같은 달에 두 번
  적용하지 않도록, 생성 거래에 `recurring:<id>` 표식 태그를 달아 중복을 막는다
  (evidence/demo_run.txt 208-219: 1회차 생성=1, 2회차 건너뜀=1).
- 출력 테이블 정렬: 외부 라이브러리 없이 `unicodedata` 로 한글의 표시 폭(전각 2칸)을
  계산해 열을 맞춘다(`budget_app/formatting.py` 의 `display_width`).
- 저장 원자성 강화: 위 "저장 안정성" 절의 임시 파일 + `os.replace` 방식을 수정/삭제에
  적용했다.

## 테스트

표준 라이브러리 `unittest` 만 사용하므로 추가 설치 없이 실행한다.

```bash
python -m unittest discover -s tests -v
```

저수준 스트리밍(역방향 읽기, 블록 경계, 원자적 쓰기), 서비스 로직(검증, CRUD,
검색, 요약, 예산 초과, 카테고리 사용 중 삭제, 가져오기/내보내기, 백업, 반복 내역
중복 방지), CLI 종료 코드까지 31개 케이스를 포함한다. 실행 결과는 evidence/tests.txt
에 저장되어 있으며 31개 모두 통과한다(`Ran 31 tests ... OK`).

## Docker 로 재현

표준 라이브러리만 쓰므로 의존성 설치 단계가 없다.

```bash
docker build -t budget-app .

# 기본 실행: 전체 기능 시연 + evidence 생성
docker run --rm budget-app

# 개별 명령 실행
docker run --rm budget-app python -m budget_app summary --month 2024-01
```

이미지에는 `PYTHONUTF8=1` 을 설정해 어떤 환경에서도 한글 입출력이 깨지지 않도록 했다.

## 검증 산출물(evidence)

평가자가 코드를 다시 실행하지 않아도 동작을 확인할 수 있도록, `python scripts/run_demo.py`
실행 결과를 `evidence/` 아래에 텍스트로 보존했다.

- evidence/demo_run.txt: 10개 기능을 순서대로 실행한 전체 세션 로그(명령, 입력,
  출력, 종료 코드 포함).
- evidence/help.txt: 전체 및 명령별 `--help` 출력.
- evidence/data_files.txt: 실행 후 저장 파일 4종의 실제 내용과 내보낸 CSV 내용.
- evidence/errors.txt: 잘못된 날짜, 없는 id, export 조건 누락, 사용 중 카테고리
  삭제, 허용되지 않은 타입 등 오류 처리와 종료 코드.
- evidence/tests.txt: 단위 테스트 실행 결과(31개 통과).
- evidence/export_2024-01.csv: export 로 생성한 CSV 견본.

## 트러블슈팅

- 한글이 깨져 보이거나 `UnicodeEncodeError` 가 날 때: 콘솔 인코딩이 UTF-8 이 아닌
  환경(예: 일부 Windows cp949 콘솔)일 수 있다. 프로그램은 파이프/리다이렉트로 연결된
  표준 입출력을 자동으로 UTF-8 로 맞춘다(`budget_app/cli.py` 의 `_enable_utf8_io`).
  대화형에서 문제가 있으면 `PYTHONUTF8=1` 을 설정하거나, Windows 에서는 `chcp 65001`
  로 콘솔을 UTF-8 로 바꾼 뒤 실행한다.
- `No module named budget_app`: 저장소 루트(이 README 가 있는 폴더)에서 실행해야
  한다. `python -m budget_app ...` 는 현재 폴더의 `budget_app` 패키지를 찾는다.
- 저장 파일을 직접 편집하다 손상된 경우: 해당 줄만 제거하거나, `data/backups/` 의
  백업 폴더에서 파일을 복원한다.
