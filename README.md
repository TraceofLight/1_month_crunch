# SQL로 만드는 카페 주문 데이터베이스

## 주제와 실행 환경

주제는 카페 주문 관리이다. 고객이 메뉴를 주문하면 직원이 주문을 처리하고, 주문 하나에는 여러 주문 상세 품목이 연결된다. 엑셀 한 시트에 고객, 메뉴, 주문, 주문 품목을 모두 적으면 같은 고객 이메일과 메뉴 가격이 반복되고, 오타가 나도 관계가 깨졌는지 알기 어렵다. 이 설계는 고객, 직원, 메뉴 카테고리, 메뉴, 주문, 주문 상세를 테이블로 나누고 PK와 FK로 연결해 중복과 잘못된 참조를 줄인다.

DB는 SQLite를 선택했다. 별도 서버가 필요 없고 `evidence/cafe_orders.db` 파일 하나로 결과를 확인할 수 있어 입문 과제와 로컬 재현에 적합하다. 실행 도구는 Python 표준 라이브러리의 `sqlite3` 모듈이다. 백엔드 프레임워크, 웹 서버, ORM은 사용하지 않았다.

런타임은 `ubuntu:24.04` 기반 Dockerfile로 제공한다. Dockerfile은 Ubuntu 이미지 digest와 `python3=3.12.3-0ubuntu2.1`, `ca-certificates=20240203` 패키지 버전을 고정한다. 외부 Python 패키지는 사용하지 않는다. 컨테이너에서 설치되는 런타임은 Ubuntu 패키지의 `python3`와 Python에 포함된 `sqlite3` 모듈뿐이다.

## 실행 방법

Docker가 실행 중인 환경에서 아래 명령을 실행한다.

```powershell
docker build -t cafe-sql-assignment .
docker run --rm -v "${PWD}:/app" -w /app cafe-sql-assignment python3 scripts/run.py
```

`scripts/run.py`는 전체 파이프라인의 단일 진입점이다. 실행 순서는 스키마 생성, 샘플 데이터 입력, 핵심 쿼리 15개 실행, FK 오류 검증, 결과 파일 저장, 산출물 검증이다.

성공 출력은 다음과 같다.

```text
파이프라인 실행 완료
DB 파일: evidence/cafe_orders.db
검증 결과:
검증 통과: SQLite 스키마, 샘플 데이터, 쿼리, evidence 산출물이 요구사항을 만족합니다.
```

## 파일 구성

| 경로 | 역할 |
| --- | --- |
| `sql/schema.sql` | 테이블 생성, PK, FK, `NOT NULL`, `UNIQUE`, `CHECK` 제약조건 정의 |
| `sql/seed.sql` | 부모 테이블부터 자식 테이블 순서로 샘플 데이터 입력 |
| `sql/queries.sql` | 설명 주석이 붙은 핵심 쿼리 15개 |
| `scripts/run.py` | 전체 파이프라인 실행과 evidence 생성 |
| `scripts/verify.py` | 테이블 행 수, FK 동작, 쿼리 범주, evidence 존재 여부 검증 |
| `evidence/query_results.txt` | 쿼리 15개의 실행 결과 텍스트 |
| `evidence/integrity_check.txt` | 일부러 실패시킨 FK 입력 결과 |
| `evidence/verification.log` | 최종 검증 로그 |
| `evidence/cafe_orders.db` | 실행 후 생성된 SQLite DB 파일 |
| `Dockerfile` | 컨테이너 재현 환경 |

## 데이터 모델

| 테이블 | 주요 컬럼 | 설명 | 샘플 행 수 |
| --- | --- | --- | --- |
| `customer` | `customer_id`, `email`, `membership_level` | 주문하는 고객 | 10 |
| `staff` | `staff_id`, `email`, `role` | 주문을 처리하는 직원 | 10 |
| `menu_category` | `category_id`, `name`, `display_order` | 메뉴 분류 | 10 |
| `menu_item` | `menu_item_id`, `category_id`, `price` | 판매 메뉴 | 12 |
| `cafe_order` | `order_id`, `customer_id`, `staff_id`, `ordered_at`, `status` | 주문 헤더 | 12 |
| `order_item` | `order_item_id`, `order_id`, `menu_item_id`, `quantity`, `unit_price` | 주문별 품목 | 22 |

관계는 모두 1:N이다.

| 부모 테이블 | 자식 테이블 | FK | 의미 |
| --- | --- | --- | --- |
| `menu_category` | `menu_item` | `menu_item.category_id` | 카테고리 하나에 여러 메뉴가 속한다. |
| `customer` | `cafe_order` | `cafe_order.customer_id` | 고객 하나가 여러 주문을 만들 수 있다. |
| `staff` | `cafe_order` | `cafe_order.staff_id` | 직원 하나가 여러 주문을 처리할 수 있다. |
| `cafe_order` | `order_item` | `order_item.order_id` | 주문 하나가 여러 주문 상세를 가진다. |
| `menu_item` | `order_item` | `order_item.menu_item_id` | 메뉴 하나가 여러 주문 상세에서 판매될 수 있다. |

`order_item`을 분리한 이유는 주문 하나에 메뉴가 여러 개 들어갈 수 있기 때문이다. 주문 테이블에 `menu1`, `menu2`, `menu3`처럼 컬럼을 늘리면 메뉴 개수가 바뀔 때마다 스키마를 바꿔야 하고, 메뉴별 매출 집계도 어려워진다. 주문 헤더와 주문 상세를 나누면 주문의 공통 정보와 품목별 수량, 단가를 자연스럽게 분리할 수 있다.

## 제약조건과 무결성

모든 테이블은 PK를 가진다. `customer.email`, `staff.email`, `menu_category.name`, `menu_item.name`에는 `UNIQUE`를 적용해 중복을 막았다. 이름, 이메일, 주문 일시, 상태처럼 필수 값에는 `NOT NULL`을 적용했다. 주문 방식과 주문 상태는 `CHECK`로 허용 값만 저장한다.

FK는 실제로 동작한다. `scripts/run.py`는 존재하지 않는 `customer_id` 999를 참조하는 주문 입력을 시도하고, SQLite가 `FOREIGN KEY constraint failed`로 막은 결과를 `evidence/integrity_check.txt`에 저장한다.

SQLite에서는 FK 검사를 위해 연결마다 `PRAGMA foreign_keys = ON`을 실행해야 한다. 이 문장은 SQLite 전용 설정이다. `EXPLAIN QUERY PLAN`도 SQLite 전용 실행 계획 확인 문법이다. 자동 증가 키는 DB마다 문법이 다르므로 샘플 데이터에서는 ID 값을 직접 지정했다.

## SQL 사용 기준

`SELECT`는 저장된 데이터를 조회할 때 쓴다. `WHERE`는 필요한 행만 거르고, `ORDER BY`는 정렬하며, `LIMIT`은 결과 개수를 제한한다.

`INSERT`는 새 행을 넣을 때 쓴다. FK가 있는 자식 행을 넣기 전에는 부모 행이 먼저 있어야 한다. 이 과제에서는 `customer`, `staff`, `menu_category`를 먼저 넣고, 그 다음 `menu_item`, `cafe_order`, `order_item`을 넣었다.

`UPDATE`는 기존 행의 값을 바꿀 때 쓴다. Q14는 대기 상태 주문 110번을 결제 완료 상태로 바꾼다.

`DELETE`는 기존 행을 삭제할 때 쓴다. Q15는 취소 주문 112번을 삭제한다. `order_item.order_id`는 `ON DELETE CASCADE`를 사용하므로 해당 주문 상세도 함께 정리된다.

`JOIN`은 FK로 연결된 데이터를 한 결과로 모을 때 쓴다. 주문 목록만 보면 고객 이름과 직원 이름을 알 수 없지만, Q05는 `cafe_order`, `customer`, `staff`를 연결해 주문 처리 내역을 한 번에 보여준다.

`GROUP BY`는 여러 행을 묶어 지표를 만들 때 쓴다. Q09는 주문 상태별 건수를, Q10은 고객별 결제 매출을, Q11은 주문 방식별 평균 주문 금액을 계산한다.

인덱스는 자주 검색하거나 정렬하는 컬럼에 둔다. Q13은 기간별 주문 검색과 최신 주문 정렬에 쓰이는 `cafe_order.ordered_at`에 `idx_cafe_order_ordered_at` 인덱스를 만든다. 실행 계획에는 `SEARCH cafe_order USING INDEX idx_cafe_order_ordered_at`가 기록되어 인덱스가 사용됐음을 확인했다.

## 핵심 쿼리 15개

| 번호 | 범주 | 확인 내용 | 결과 증거 |
| --- | --- | --- | --- |
| Q01 | 기본 조회 | `WHERE`로 서울 강남구 고객 조회 | `evidence/query_results.txt` |
| Q02 | 기본 조회 | 판매 가능 메뉴를 가격 내림차순 정렬 | `evidence/query_results.txt` |
| Q03 | 기본 조회 | 최신 주문 5건을 `LIMIT`으로 제한 | `evidence/query_results.txt` |
| Q04 | 기본 조회 | 결제 완료 포장 주문 최근 3건 조회 | `evidence/query_results.txt` |
| Q05 | 조인 | 주문, 고객, 담당 직원을 `INNER JOIN` | `evidence/query_results.txt` |
| Q06 | 조인 | 주문 상세, 메뉴, 카테고리를 `INNER JOIN` | `evidence/query_results.txt` |
| Q07 | 조인과 집계 | 주문별 결제 금액을 `JOIN`과 `GROUP BY`로 계산 | `evidence/query_results.txt` |
| Q08 | 조인 | 고객별 주문 수를 `LEFT JOIN`으로 조회 | `evidence/query_results.txt` |
| Q09 | 집계 | 주문 상태별 건수를 `COUNT`로 계산 | `evidence/query_results.txt` |
| Q10 | 집계 | 고객별 결제 완료 매출을 `SUM`으로 계산 | `evidence/query_results.txt` |
| Q11 | 집계 | 주문 방식별 평균 주문 금액을 `AVG`로 계산 | `evidence/query_results.txt` |
| Q12 | 서브쿼리 | Q10과 같은 고객별 결제 매출을 상관 서브쿼리로 계산 | `evidence/query_results.txt` |
| Q13 | 인덱스 | `ordered_at` 인덱스 생성과 실행 계획 확인 | `evidence/query_results.txt` |
| Q14 | 수정 | 대기 주문을 결제 완료로 `UPDATE` | `evidence/query_results.txt` |
| Q15 | 삭제 | 취소 주문을 `DELETE`하고 상세 행 정리 확인 | `evidence/query_results.txt` |

Q10과 Q12는 같은 요구를 두 방식으로 푼다. Q10은 `JOIN` 후 `GROUP BY`로 고객별 매출을 계산한다. Q12는 고객 행마다 상관 서브쿼리를 실행해 결제 완료 매출을 계산한다. 전체 고객을 대상으로 순위를 만들 때는 Q10처럼 한 번에 묶어 집계하는 방식이 더 읽기 쉽고 일반적으로 효율적이다. Q12는 고객별 계산식을 결과 컬럼 안에 직접 보여주므로 서브쿼리 사고방식을 익히기 좋지만, 데이터가 커지면 행마다 하위 계산을 반복할 수 있어 실행 계획을 확인해야 한다.

## 실행 결과 요약

`evidence/query_results.txt`에는 Q01부터 Q15까지 모든 결과가 들어 있다. 주요 결과는 다음과 같다.

| 확인 항목 | 결과 |
| --- | --- |
| Q01 서울 강남구 고객 | 김민준, 강지민 |
| Q03 최신 주문 5건 | 112, 111, 110, 109, 108 |
| Q09 주문 상태별 건수 | `paid` 9건, `cancelled` 2건, `pending` 1건 |
| Q10 고객별 결제 매출 1위 | 이서연 34200 |
| Q11 평균 주문 금액 1위 주문 방식 | `delivery` 20833.3 |
| Q13 인덱스 확인 | `idx_cafe_order_ordered_at` 사용 |
| Q14 수정 결과 | 주문 110번 상태가 `paid`로 변경 |
| Q15 삭제 결과 | 주문 112번과 주문 상세 112번 모두 0건 |

최종 검증 로그는 `evidence/verification.log`에 저장되어 있다.

```text
파이프라인 실행 완료
DB 파일: evidence/cafe_orders.db
검증 결과:
검증 통과: SQLite 스키마, 샘플 데이터, 쿼리, evidence 산출물이 요구사항을 만족합니다.
```

FK 오류 확인 결과는 `evidence/integrity_check.txt`에 저장되어 있다.

```text
없는 customer_id를 참조하는 주문 입력을 시도했다.
실행 SQL:
INSERT INTO cafe_order (order_id, customer_id, staff_id, ordered_at, order_type, status)
VALUES (999, 999, 1, '2026-05-15 09:00:00', 'takeout', 'paid');
결과: FK 제약조건으로 차단됨 (FOREIGN KEY constraint failed)
```

## 이 DB로 뽑을 수 있는 핵심 지표 3개

첫 번째 지표는 고객별 결제 완료 매출이다. Q10으로 확인하며, 우수 고객 식별과 멤버십 혜택 설계에 쓸 수 있다.

두 번째 지표는 주문 방식별 평균 주문 금액이다. Q11로 확인하며, 배달, 매장, 포장 중 어떤 방식의 객단가가 높은지 판단할 수 있다.

세 번째 지표는 주문 상태별 건수다. Q09로 확인하며, 취소 주문과 대기 주문 비율을 보고 운영 병목이나 결제 실패를 점검할 수 있다.

## 위협 모델과 운영상 주의점

잘못된 참조가 가장 중요한 데이터 위험이다. 주문이 존재하지 않는 고객을 참조하면 고객별 매출과 주문 이력이 틀어진다. FK와 `PRAGMA foreign_keys = ON`으로 이 위험을 막는다.

중복 고객과 중복 메뉴도 위험하다. 같은 이메일이 여러 고객으로 저장되면 고객별 매출이 분산된다. `UNIQUE` 제약조건으로 이메일과 메뉴명을 중복 저장하지 못하게 했다.

상태 값 오타는 집계 오류를 만든다. `paid`, `pending`, `cancelled` 외의 값이 들어가면 Q09 같은 상태별 집계가 깨진다. `CHECK` 제약조건으로 허용 상태만 저장한다.

삭제는 신중해야 한다. Q15는 취소 주문을 삭제하면서 주문 상세까지 함께 지워지는지 확인한다. 실제 운영 DB라면 물리 삭제 대신 상태 변경이나 감사 로그를 검토할 수 있지만, 이 과제는 `DELETE` 동작을 보여주기 위해 취소 주문 하나를 삭제했다.

SQL 주입 위험은 현재 구조에서는 낮다. 외부 입력을 받는 애플리케이션이나 API가 없고, 정해진 SQL 파일만 실행하기 때문이다. 나중에 화면이나 서버를 붙인다면 문자열 연결로 SQL을 만들지 말고 파라미터 바인딩을 사용해야 한다.

## 문제 해결 절차

컨테이너 빌드가 실패하면 Docker가 실행 중인지 먼저 확인한다. 그 다음 `docker build -t cafe-sql-assignment .`를 다시 실행해 `ubuntu:24.04` 이미지와 Ubuntu 패키지 저장소에 접근 가능한지 확인한다.

`FOREIGN KEY constraint failed`가 예상하지 못한 곳에서 발생하면 INSERT 순서를 확인한다. 부모 테이블인 `customer`, `staff`, `menu_category`, `menu_item`, `cafe_order`가 먼저 입력되어야 자식 테이블인 `order_item`을 입력할 수 있다.

FK 오류가 나야 하는데 나지 않으면 SQLite 연결에서 `PRAGMA foreign_keys = ON`이 실행됐는지 확인한다. SQLite는 연결마다 FK 검사를 명시적으로 켜야 한다.

쿼리 결과가 이전 실행과 다르면 `scripts/run.py`를 다시 실행한다. 이 스크립트는 기존 `evidence/cafe_orders.db`를 지우고 새 DB를 만든 뒤 같은 SQL을 다시 실행한다.

쿼리 수나 범주 검증이 실패하면 `sql/queries.sql`의 Q 번호가 Q01부터 Q15까지 유지되는지 확인한다. `scripts/verify.py`는 15개 블록과 `WHERE`, `ORDER BY`, `LIMIT`, `INNER JOIN`, `LEFT JOIN`, `GROUP BY`, `COUNT`, `SUM`, `AVG`, `UPDATE`, `DELETE`, `CREATE INDEX`, 서브쿼리 존재를 검사한다.
