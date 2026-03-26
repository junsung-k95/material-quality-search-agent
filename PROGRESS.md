# PROGRESS.md — Material Quality Search Agent

> **AI Agent 전용 작업 추적 문서**
> 이 파일은 모든 개발 작업의 상태를 기록합니다.
> 작업 시작 전 반드시 읽고, 완료 후 반드시 업데이트하세요.

---

## 📌 현재 상태 (Last Updated: 2026-03-26)

| 항목 | 내용 |
|------|------|
| **Active Branch** | `claude/enterprise-ui-redesign` |
| **Main Branch** | 최신 (PR #2, #3 머지 완료) |
| **진행 중인 작업** | Enterprise UI 재설계 (보일러 도메인 전환) |
| **배포** | Render (API) + Streamlit Community Cloud (UI) — 설정 완료, 실 배포 대기 |
| **테스트** | 기존 12/12 통과 (enterprise 재설계 후 재검증 필요) |

---

## 🏗️ 프로젝트 개요

**목적**: 보일러 제조회사 사내 품질 이슈 관리 시스템에 자연어 검색 기능을 추가한 데모
- AI가 자연어 질의를 이해하고 구조화된 필터를 생성 (단순 키워드 검색과의 차별화)
- 제품 개발 라이프사이클(PLM) 연동: 과거 개발 프로젝트의 품질이슈를 구상설계 단계에서 참조
- 품질팀 → 개발팀 이슈 이전 워크플로우 시뮬레이션

**핵심 파이프라인**:
```
자연어 질의
  → [Node1] 엔티티 추출 (Claude tool_use)
  → [Node2] 벡터 검색 (ChromaDB + sentence-transformers)
  → [Node3] 최적 엔티티 선택 (Claude tool_use)
  → [Node4] 필터 생성 (deterministic)
  → [Node5] 이슈 조회 (SQLite) + fallback
  → [Node6] 하이브리드 랭킹 (0.7×유사도 + 0.3×구조)
  → [Node7] 설명 생성 (Claude)
  → API 응답 / Streamlit UI
```

---

## ✅ 완료된 작업

### Phase 0 — 프로젝트 셋업 ✅
- `pyproject.toml` (langgraph, anthropic, chromadb, fastapi, streamlit 등)
- `.env.example`, `config.py` (pydantic-settings, `demo_mode` 프로퍼티)
- 전체 패키지 구조 (`src/material_quality_agent/`)

### Phase 1 — 데이터 레이어 ✅
- `data/sample_data.json` — 자동차 내장재 8개 부품, 27개 품질이슈 (→ 보일러 도메인으로 교체 예정)
- `db/issue_db.py` — SQLite CRUD (`init_db`, `query_by_filter`, `get_all`)
- `vector/embedder.py` — `paraphrase-multilingual-MiniLM-L12-v2` 래퍼
- `vector/store.py` — ChromaDB 시딩/검색
- `scripts/seed_db.py`

### Phase 2 — Agent 도구 ✅
- `tools/entity_extractor.py` — Claude tool_use + demo_mode 폴백 (정규식 키워드 분리)
- `tools/entity_selector.py` — Claude tool_use + demo_mode 폴백 (최고 유사도 자동 선택)
- `tools/filter_builder.py` — deterministic 필터 생성

### Phase 3 — LangGraph 파이프라인 ✅
- `graph/state.py` — `AgentState` TypedDict
- `graph/nodes.py` — 7개 노드 + demo_mode 폴백
- `graph/edges.py` — `should_fallback()` 조건부 엣지
- `graph/pipeline.py` — StateGraph 조립
- `search/ranker.py` — 하이브리드 랭킹

### Phase 4 — API 레이어 ✅
- `api/schemas.py` — `SearchRequest`, `SearchResponse` Pydantic 모델
- `api/main.py` — `POST /search`, `GET /health` (demo_mode 반환)

### Phase 5 — UI 레이어 ✅ (→ Phase 8에서 전면 교체 예정)
- `ui/app.py` — 단순 Streamlit 검색 UI (3-panel enterprise UI로 교체 중)
- `ui/requirements.txt` — Streamlit Community Cloud용 경량 deps

### Phase 6 — 테스트 ✅
- `tests/conftest.py` — mock Anthropic, EphemeralClient, in-memory SQLite
- `tests/test_entity_extractor.py`, `test_entity_selector.py`
- `tests/test_pipeline.py`, `tests/test_api.py`
- **12/12 통과**

### Phase 7 — 배포 설정 ✅
- `Dockerfile` — Python 3.11-slim + uv + sentence-transformers 모델 사전 다운로드
- `render.yaml` — FastAPI 단일 서비스 (Render 무료 플랜 1서비스 제한)
- `scripts/start_api.sh`, `scripts/start_ui.sh`
- `ui/requirements.txt` — Streamlit Community Cloud 경량 배포용
- Render URL: `https://material-quality-search-agent.onrender.com`

### 예외처리 / Demo Mode ✅
- `ANTHROPIC_API_KEY` 미설정 시 전체 파이프라인 정상 동작
- `settings.demo_mode` 플래그로 각 Claude 호출 지점에서 분기
- UI: demo_mode 경고 배너 자동 표시

---

## 🔄 진행 중인 작업

### Phase 8 — Enterprise UI 재설계 (IN PROGRESS)
**Branch**: `claude/enterprise-ui-redesign`
**Agent**: `af01948c9ba01e8f6` (백그라운드 실행 중)

#### 목표
보일러 제조회사의 사내 PLM 연동 품질 이슈 관리 시스템으로 재설계

#### 변경 파일 목록
| 파일 | 상태 | 내용 |
|------|------|------|
| `data/sample_data.json` | 🔄 작업중 | 자동차→보일러 도메인 전환, projects/users/resolutions 추가 |
| `db/issue_db.py` | ⏳ 대기 | projects, users, resolutions 테이블 추가 |
| `db/seed_data.py` | ⏳ 대기 | 신규 컬렉션 로드 |
| `scripts/seed_db.py` | ⏳ 대기 | 신규 테이블 시딩 |
| `api/schemas.py` | ⏳ 대기 | ProjectSummary, ResolutionRecord, ChatRequest/Response 모델 |
| `api/main.py` | ⏳ 대기 | `/projects`, `/issues/{id}/resolutions`, `/chat` 엔드포인트 |
| `graph/state.py` | ⏳ 대기 | `related_projects: list[dict]` 필드 추가 |
| `graph/nodes.py` | ⏳ 대기 | query_issues_node에 관련 프로젝트 조회 추가 |
| `ui/app.py` | ⏳ 대기 | 3-panel 엔터프라이즈 UI 전면 재작성 |

#### 신규 데이터 스키마 (목표)
```
product_families: 5종 (가정용 콘덴싱/업무용 대형/기름/전기/수소 혼소 가스 보일러)
components: 12종 (열교환기/버너/가스밸브/팬모터/메인PCB/온도센서/압력센서/순환펌프/팽창탱크/배기시스템/점화장치/급수필터)
projects: 8개 (KR/NA/EU 혼합, 2021-2024, 다양한 lifecycle_phase)
users: 10명 (품질팀 4, Part leader 2, 엔지니어 4)
issues: 40개 (severity: critical/major/minor, status: 신규/검토중/수용/기각/배정/해결)
resolutions: ~50개
```

#### 신규 API 엔드포인트 (목표)
```
GET  /projects                   → 프로젝트 목록
GET  /projects/{id}/issues       → 프로젝트별 이슈
GET  /issues/{id}/resolutions    → 해결 이력
POST /chat                       → AI 챗봇 (멀티턴, in-memory session)
```

#### UI 레이아웃 (목표)
```
┌─────────────────────────────────────────────────────────────────┐
│  [로고] 품질 이슈 관리 시스템          [사용자] 이민준 | 연구소    │
├──────────┬────────────────────────────────────┬─────────────────┤
│  현재     │  자연어 검색창            [검색]    │  💬 AI 어시스턴트│
│  프로젝트 │  [제품군▼][시장▼][심각도▼][상태▼]  │  (챗봇 패널)    │
│  컨텍스트 │  ─────────────────────────────────  │                 │
│          │  이슈 카드 (심각도/상태/시장 배지)    │  [입력창]       │
│  라이프   │  + 관련 프로젝트 링크               │                 │
│  사이클   │  + 해결이력 타임라인 (접기/펼치기)  │                 │
└──────────┴────────────────────────────────────┴─────────────────┘
```

---

## ⏳ 예정 작업

### Phase 9 — 재검증 & 머지
- [ ] 보일러 도메인으로 DB 재시딩 확인
- [ ] 기존 테스트 수정 (도메인 변경으로 인한 fixture 업데이트)
- [ ] 신규 엔드포인트 테스트 추가
- [ ] PR 생성 → main 머지
- [ ] Render 재배포 + Streamlit Community Cloud 재배포

### Phase 10 (선택) — MCP 연동
- [ ] vector_search, issue_db_query를 MCP 도구로 노출
- [ ] 외부 Claude 클라이언트에서 접근 가능하도록 설정

---

## 🗂️ 주요 파일 현황

```
material-quality-search-agent/
├── CLAUDE.md                    ✅ 아키텍처/컨벤션 레퍼런스
├── PROGRESS.md                  ✅ 이 파일 (작업 추적)
├── README.md                    ✅ 사용자 설정 가이드
├── pyproject.toml               ✅
├── Dockerfile                   ✅ Render 배포용
├── render.yaml                  ✅ API 단일 서비스
├── .env.example                 ✅
│
├── data/
│   ├── sample_data.json         🔄 보일러 도메인으로 교체 중
│   ├── issues.db                ✅ (재시딩 필요)
│   └── chroma/                  ✅ (재시딩 필요)
│
├── src/material_quality_agent/
│   ├── config.py                ✅ demo_mode 포함
│   ├── graph/
│   │   ├── state.py             🔄 related_projects 추가 예정
│   │   ├── nodes.py             🔄 query_issues_node 수정 예정
│   │   ├── edges.py             ✅
│   │   └── pipeline.py         ✅
│   ├── tools/
│   │   ├── entity_extractor.py  ✅ demo_mode 폴백 포함
│   │   ├── entity_selector.py   ✅ demo_mode 폴백 포함
│   │   └── filter_builder.py    ✅
│   ├── vector/
│   │   ├── embedder.py          ✅
│   │   └── store.py             ✅
│   ├── db/
│   │   ├── issue_db.py          🔄 신규 테이블 추가 예정
│   │   └── seed_data.py         🔄 신규 컬렉션 추가 예정
│   ├── search/
│   │   └── ranker.py            ✅
│   └── api/
│       ├── main.py              🔄 신규 엔드포인트 추가 예정
│       └── schemas.py           🔄 신규 모델 추가 예정
│
├── ui/
│   ├── app.py                   🔄 3-panel enterprise UI로 재작성 예정
│   └── requirements.txt         ✅ Streamlit Community Cloud용
│
├── tests/                       ✅ 12/12 통과 (재검증 필요)
└── scripts/
    ├── seed_db.py               🔄 신규 테이블 시딩 추가 예정
    ├── start_api.sh             ✅
    └── start_ui.sh              ✅
```

---

## 🔧 기술 스택

| 레이어 | 기술 | 버전 | 비고 |
|--------|------|------|------|
| Agent 오케스트레이션 | `langgraph` | ^0.2 | StateGraph, 조건부 엣지 |
| LLM | `anthropic` | ^0.40 | claude-sonnet-4-6, tool_use |
| 임베딩 | `sentence-transformers` | ^3.0 | paraphrase-multilingual-MiniLM-L12-v2 |
| 벡터 DB | `chromadb` | ^0.5 | 로컬 persistent |
| 이슈 DB | `sqlite3` | stdlib | 구조화 데이터 |
| API | `fastapi` + `uvicorn` | ^0.115 | REST |
| UI | `streamlit` | ^1.40 | 데모 프론트엔드 |
| 패키지 관리 | `uv` | latest | pyproject.toml |
| 테스트 | `pytest` + `pytest-asyncio` | ^8 / ^0.24 | |
| 린팅 | `ruff` | ^0.8 | |

---

## 🚀 배포 현황

| 서비스 | 플랫폼 | URL | 상태 |
|--------|--------|-----|------|
| FastAPI API | Render (free) | https://material-quality-search-agent.onrender.com | 설정 완료, 배포 대기 |
| Streamlit UI | Streamlit Community Cloud | — | 설정 필요 |

**환경변수 설정 필요:**
- Render: `ANTHROPIC_API_KEY`
- Streamlit Community Cloud: `API_BASE_URL=https://material-quality-search-agent.onrender.com`

---

## 📋 Agent 작업 가이드

### 새 작업 시작 전 체크리스트
1. 이 파일 (`PROGRESS.md`) 최신 내용 확인
2. `CLAUDE.md` 컨벤션 확인
3. `git status` 및 현재 브랜치 확인
4. 작업 대상 파일의 현재 상태 (✅/🔄/⏳) 확인

### 작업 완료 후 필수 사항
1. 이 파일의 해당 항목 상태 업데이트 (⏳→🔄→✅)
2. "완료된 작업" 섹션에 내용 추가
3. "현재 상태" 테이블의 날짜 업데이트
4. commit 메시지에 관련 Phase/항목 명시

### 브랜치 전략
```
main                          ← 안정 버전 (PR 머지만)
claude/enterprise-ui-redesign ← 현재 활성 개발 브랜치
claude/<feature>              ← 신규 기능 브랜치 네이밍
```

### 커밋 메시지 형식
```
<type>: <설명> (Phase N)

types: feat, fix, test, docs, refactor, chore
예: feat: add /chat endpoint and chatbot sidebar (Phase 8)
```

---

## 🐛 알려진 이슈 / 주의사항

| 항목 | 내용 |
|------|------|
| 데이터 재시딩 | 도메인 변경 후 `data/issues.db`, `data/chroma/` 삭제 후 재시딩 필요 |
| ChromaDB $in 필터 | 단일 조건에 `$and` 래퍼 사용 금지 (테스트에서 수정된 이슈) |
| Render 콜드 스타트 | sentence-transformers 모델은 Docker 이미지에 사전 포함 (460MB) |
| Render 무료 플랜 | 1 서비스 제한 → API만 배포, UI는 Streamlit Community Cloud |
| demo_mode | ANTHROPIC_API_KEY 없을 때 자동 활성화, 전체 파이프라인 동작 보장 |
