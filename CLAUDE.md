# CLAUDE.md

> **문서 원칙**: 코드·설정 파일로 알 수 없고, 도구·하니스·모델이 대신 보장하지도 않는 것(규약·도메인 지식·함정)만 기록한다. 구조·목록은 소스가 따로 있으므로 나열하지 않는다 — 짧은 것은 의도된 생략이다. 내용을 추가할 때도 같은 기준을 따를 것.

## 최종 목표

큰 Notion 페이지 트리를 **반복해서 통째로 읽어 Markdown으로 export**하는 작업을, Notion API 호출 최소로 수행하는 캐싱 클라이언트를 제공한다. `notion_client.Client`의 드롭인 대체이며, `last_edited_time`을 변경 감지 신호로 써서 바뀐 서브트리만 다시 읽는다 (변경 없으면 루트 1콜, 변경분만 추가 호출).

## 아키텍처 결정 — dict 기반 유지 (2026-08-08 확정)

- 파이프라인(캐시·순회·블록 렌더링)은 **dict 기반**이다. 이유: ① 읽기 전용 export 도구는 모르는 입력을 건너뛰는 것이 맞다(부분 성공 > 크래시) ② Notion 블록 스키마는 열려 있어 엄격한 모델은 새 타입마다 깨진다 ③ 캐시가 원본 dict에 필드를 덧붙여 자라는 구조라 pydantic 왕복은 extra 필드를 유실시킨다.
- pydantic은 **property 렌더링 계층(`cached_notion/models/property.py`)에만** 사용한다.
- block/page 전면 pydantic화는 2023-12에 시도했다가 폐기했다. 미완성 작업물은 `archive/pydantic-models-wip` 브랜치에 보존되어 있다. **전면 모델화를 다시 시도하지 말 것** — 타입 안정성이 필요해지면 `TypedDict(total=False)` 방향으로.

## 캐시 불변식 (깨면 안 되는 의도)

- 캐시 엔트리는 API 응답에 `children`/`entries`/`*_completed`/`cached_time`을 **덧붙여 자라는 문서**다. 응답의 `last_edited_time`이 캐시와 같으면 덮어쓰지 않는다 — 축적된 트리를 보존하기 위한 의도적 동작이다.
- 순회 중 부모 목록에서 얻은 자식 객체를 `cached=` 힌트로 전달하는 것이 서브트리 가지치기의 핵심이다. 힌트 없는 retrieve는 항상 API를 호출한다.

## 데이터 주의

- 루트의 untracked 파일(`cr.json`, `manual.json`, `test.json`, `*.sqlite`, `run.py`, `examine_json.*`)은 실제 워크스페이스에서 긁은 덤프로 사내 데이터가 들어 있을 수 있다. **커밋 금지, 테스트 fixture로 복사 금지** — fixture는 합성 데이터만 쓴다.
