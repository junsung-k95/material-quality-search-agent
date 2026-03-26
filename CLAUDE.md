# CLAUDE.md — Material Quality Search Agent

> This file is the primary reference for AI assistants working on this codebase.
> Read this before writing any code.

---

## 1. Project Overview

This service answers natural-language queries about **material quality issues** (자재 품질 문제) in automotive interior parts manufacturing. It is designed for **demo purposes** to show that "AI understands the input and builds a filter — not just keyword search."

### Success Criteria (Demo)
- User sees `AI가 '대시보드' → '대시보드 커버'로 매핑함` style explanation
- Filter applied is shown explicitly (e.g., `component = 대시보드 커버`)
- Top 3–5 quality issues are returned with cause, solution, and material info
- Response feels instant (1–3 sec target)

### Out of Scope
- Real SAP system integration
- Real-time data sync
- Model fine-tuning / training automation

---

## 2. Architecture

```
[User Query]  e.g. "대시보드 쪽에서 기포가 생김"
     │
     ▼
[Node 1: extract_entities]          ← Claude tool_use
  → candidate_terms: ["대시보드"]
     │
     ▼
[Node 2: vector_search]             ← ChromaDB + sentence-transformers
  → vector_candidates: [
      {"name": "대시보드 커버", "score": 0.92},
      {"name": "센터 콘솔 패널", "score": 0.61}
    ]
     │
     ▼
[Node 3: select_entity]             ← Claude tool_use
  → selected_component: "대시보드 커버"
  → selection_reason: "입력 '대시보드'와 가장 유사한 부품으로 판단"
     │
     ▼
[Node 4: build_filter]              ← deterministic Python
  → filter: {"component": "대시보드 커버"}
     │
     ▼
[Node 5: query_issues]              ← SQLite
  → issues: [...matched rows...]
     │          └─ if empty → [fallback edge] → relax filter → full search
     ▼
[Node 6: hybrid_rank]               ← ranker.py
  → ranked_results (Top-K=5):
      Final Score = 0.7 × embedding_similarity + 0.3 × structural_score
     │
     ▼
[Node 7: generate_explanation]      ← Claude (no tool_use)
  → explanation: human-readable summary
     │
     ▼
[API Response / Streamlit UI]
```

### LangGraph State

```python
# src/material_quality_agent/graph/state.py
class AgentState(TypedDict):
    user_query: str
    candidate_terms: list[str]       # Node 1 output (FR-02)
    vector_candidates: list[dict]    # Node 2 output (FR-04)
    selected_component: str          # Node 3 output (FR-05)
    selection_reason: str            # Node 3 output (FR-06)
    filter: dict                     # Node 4 output (FR-07)
    fallback_used: bool              # Node 5 fallback flag (FR-08)
    issues: list[dict]               # Node 5 output (FR-09)
    ranked_results: list[dict]       # Node 6 output (FR-11/12)
    explanation: str                 # Node 7 output (FR-13/14)
```

---

## 3. Tech Stack

| Layer | Library | Version | Notes |
|-------|---------|---------|-------|
| Agent orchestration | `langgraph` | `^0.2` | StateGraph, conditional edges |
| LLM | `anthropic` | `^0.40` | tool_use for extraction/selection |
| LangChain bridge | `langchain-anthropic` | `^0.3` | If using LangChain tool wrappers |
| Embeddings | `sentence-transformers` | `^3.0` | Model: `paraphrase-multilingual-MiniLM-L12-v2` (Korean support) |
| Vector DB | `chromadb` | `^0.5` | Local persistent store |
| Issue DB | `sqlite3` (stdlib) | — | Structured issue storage |
| API | `fastapi` + `uvicorn` | `^0.115` / `^0.32` | REST endpoint |
| UI | `streamlit` | `^1.40` | Demo frontend |
| Validation | `pydantic` | `^2.0` | Schemas |
| Dependency mgmt | `uv` | latest | `pyproject.toml` based |
| Testing | `pytest` + `pytest-asyncio` | `^8` / `^0.24` | |
| Linting | `ruff` | `^0.8` | Replaces flake8 + black |
| Type checking | `mypy` | `^1.0` | |

### LLM Model
- **Default**: `claude-sonnet-4-6` (fast, capable)
- Set via env var `ANTHROPIC_MODEL` (default: `claude-sonnet-4-6`)
- Never hardcode model names in business logic — always read from config

---

## 4. Repository Structure

```
material-quality-search-agent/
├── CLAUDE.md                          ← You are here
├── README.md                          ← User-facing setup guide
├── pyproject.toml                     ← All dependencies + tool config
├── .env.example                       ← Required env vars
│
├── src/
│   └── material_quality_agent/
│       ├── config.py                  ← Settings (reads .env)
│       │
│       ├── graph/                     ← LangGraph pipeline
│       │   ├── state.py               ← AgentState TypedDict
│       │   ├── nodes.py               ← Node functions (one per pipeline step)
│       │   ├── edges.py               ← Conditional edge logic (fallback FR-08)
│       │   └── pipeline.py            ← StateGraph assembly + compile()
│       │
│       ├── tools/                     ← Claude tool_use wrappers
│       │   ├── entity_extractor.py    ← FR-02: query → candidate_terms
│       │   ├── entity_selector.py     ← FR-05/06: candidates → selected + reason
│       │   └── filter_builder.py      ← FR-07/08: entity → filter dict
│       │
│       ├── vector/                    ← Embedding + ChromaDB
│       │   ├── embedder.py            ← sentence-transformers wrapper
│       │   └── store.py               ← ChromaDB CRUD (FR-03, FR-04)
│       │
│       ├── db/                        ← Issue database
│       │   ├── issue_db.py            ← SQLite queries (FR-09)
│       │   └── seed_data.py           ← Korean automotive demo data
│       │
│       ├── search/
│       │   └── ranker.py              ← FR-11: hybrid scoring
│       │
│       └── api/
│           ├── main.py                ← FastAPI app + /search endpoint
│           └── schemas.py             ← Pydantic request/response models
│
├── ui/
│   └── app.py                         ← Streamlit demo UI
│
├── data/
│   └── sample_data.json               ← Seed data for components + issues
│
├── tests/
│   ├── conftest.py                    ← Fixtures (mock Claude, mock ChromaDB)
│   ├── test_entity_extractor.py
│   ├── test_entity_selector.py
│   ├── test_pipeline.py               ← Full graph integration test
│   └── test_api.py
│
└── scripts/
    └── seed_db.py                     ← One-time: seed SQLite + ChromaDB
```

---

## 5. Setup & Development

### Prerequisites
- Python 3.11+
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `ANTHROPIC_API_KEY` from console.anthropic.com

### Install

```bash
uv sync
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### Seed the databases

```bash
uv run python scripts/seed_db.py
```

This populates:
- `data/issues.db` — SQLite with sample quality issues
- `data/chroma/` — ChromaDB with component + issue embeddings

### Run the API

```bash
uv run uvicorn material_quality_agent.api.main:app --reload --port 8000
```

### Run the UI

```bash
uv run streamlit run ui/app.py
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Lint & type check

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

---

## 6. Key Conventions

### Python style
- **Python 3.11+** — use `match/case`, `tomllib`, PEP 695 where helpful
- **Type hints everywhere** — all function signatures must be typed
- **Async by default** — all I/O-bound functions use `async def`
- **Ruff** for formatting (replaces black): line length 100
- No `print()` in source — use Python `logging` module

### Claude API usage

```python
# Always use tool_use for structured outputs from LLM
# Never parse free-form text from Claude — define a tool schema instead

client = anthropic.AsyncAnthropic()

response = await client.messages.create(
    model=settings.anthropic_model,  # read from config, never hardcode
    max_tokens=1024,
    tools=[MY_TOOL_SCHEMA],
    messages=[{"role": "user", "content": prompt}],
)
# Extract tool_use block from response.content
```

### LangGraph nodes

```python
# Each node is a pure async function: AgentState → dict (partial state update)
# Return only the keys you're updating — LangGraph merges into state

async def extract_entities(state: AgentState) -> dict:
    terms = await call_entity_extractor(state["user_query"])
    return {"candidate_terms": terms}
```

### Error handling
- Only catch exceptions at the API boundary (`api/main.py`)
- Nodes should raise exceptions; LangGraph handles retries if configured
- Fallback logic lives in `graph/edges.py` as conditional edge functions

### Secrets
- Never commit `.env`
- Read all secrets via `config.py` using `pydantic-settings`
- `.env.example` must stay up to date with all required vars

---

## 7. Data Models

### Component Master (in ChromaDB)
```json
{
  "id": "comp-001",
  "type": "component",
  "name": "대시보드 커버",
  "embedding": [...]
}
```

### Quality Issue Record (in SQLite)
```json
{
  "id": "issue-001",
  "product": "자동차 내장재",
  "component": "대시보드 커버",
  "issue": "표면 기포 발생",
  "cause": "수분 과다 흡수",
  "solution": "건조 공정 온도 및 시간 최적화",
  "material_code": "MAT-PL-00123",
  "material_class": "플라스틱 수지",
  "class_hierarchy": "원자재 > 플라스틱 > 플라스틱 수지"
}
```

### API Response Schema
```json
{
  "query_interpretation": {
    "input_terms": ["대시보드"],
    "mapped_component": "대시보드 커버",
    "reason": "입력 '대시보드'와 가장 유사한 부품으로 판단됨",
    "fallback_used": false
  },
  "filter_applied": {
    "component": "대시보드 커버"
  },
  "results": [
    {
      "rank": 1,
      "score": 0.87,
      "component": "대시보드 커버",
      "issue": "표면 기포 발생",
      "cause": "수분 과다 흡수",
      "solution": "건조 공정 개선",
      "material_code": "MAT-PL-00123",
      "material_class": "플라스틱 수지",
      "class_hierarchy": "원자재 > 플라스틱 > 플라스틱 수지",
      "similarity_breakdown": {
        "same_component": true,
        "issue_similarity": 0.91,
        "cause_similarity": 0.83
      }
    }
  ],
  "explanation": "대시보드 커버의 표면 기포 문제는 주로 수분 과다로 인해 발생합니다..."
}
```

---

## 8. Functional Requirements Mapping

| FR ID | Description | Implementation Location |
|-------|-------------|------------------------|
| FR-01 | Natural language input | `api/schemas.py` `SearchRequest` |
| FR-02 | Entity candidate extraction | `tools/entity_extractor.py` |
| FR-03 | Component master embedding | `vector/store.py` + `scripts/seed_db.py` |
| FR-04 | Top-K vector search | `vector/store.py::search()` |
| FR-05 | Optimal entity selection | `tools/entity_selector.py` |
| FR-06 | Selection reason | `tools/entity_selector.py` (reason field) |
| FR-07 | Structured filter generation | `tools/filter_builder.py` |
| FR-08 | Fallback filter relaxation | `graph/edges.py::should_fallback()` |
| FR-09 | Issue DB filtering | `db/issue_db.py::query_by_filter()` |
| FR-10 | Embedding similarity on issues | `vector/store.py::search_issues()` |
| FR-11 | Hybrid ranking (0.7/0.3) | `search/ranker.py` |
| FR-12 | Top-K=5 results | `search/ranker.py` (k parameter) |
| FR-13 | Similarity explanation per result | `graph/nodes.py::generate_explanation` |
| FR-14 | Entity mapping explanation | `tools/entity_selector.py` (reason) |
| FR-15 | Material info display | `db/issue_db.py` (material_code, class) |
| FR-16 | Hierarchy representation | `db/seed_data.py` (class_hierarchy field) |

---

## 9. Development Todo List

> **For AI agents**: Work through phases in order. Check off items as completed.
> Each phase produces runnable/testable output before the next begins.

### Phase 0 — Project Setup
- [ ] Create `pyproject.toml` with all dependencies and tool config (ruff, mypy, pytest)
- [ ] Create `.env.example` with `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `DB_PATH`, `CHROMA_PATH`
- [ ] Create `src/material_quality_agent/config.py` using `pydantic-settings`
- [ ] Create all `__init__.py` files to establish package structure
- [ ] Verify `uv sync` works cleanly

### Phase 1 — Data Layer
- [ ] Create `data/sample_data.json` with 5+ components and 20+ quality issues (Korean automotive)
- [ ] Create `src/material_quality_agent/db/seed_data.py` — component and issue records
- [ ] Create `src/material_quality_agent/db/issue_db.py` — SQLite schema + `query_by_filter()` + `get_all()`
- [ ] Create `src/material_quality_agent/vector/embedder.py` — `sentence-transformers` wrapper with `embed()` method
- [ ] Create `src/material_quality_agent/vector/store.py` — ChromaDB collections for components and issues
- [ ] Create `scripts/seed_db.py` — seeds both SQLite and ChromaDB from `seed_data.py`
- [ ] Verify seeding runs without error: `uv run python scripts/seed_db.py`

### Phase 2 — Agent Tools (Claude tool_use)
- [ ] Create `tools/entity_extractor.py` — Claude tool_use → `{"candidate_terms": [...]}`
- [ ] Create `tools/entity_selector.py` — Claude tool_use → `{"selected_component": "...", "reason": "..."}`
- [ ] Create `tools/filter_builder.py` — deterministic: entity → `{"component": "..."}` filter dict
- [ ] Unit test each tool with mocked Claude responses

### Phase 3 — LangGraph Pipeline
- [ ] Create `graph/state.py` — `AgentState` TypedDict with all fields
- [ ] Create `graph/nodes.py` — implement all 7 node functions
- [ ] Create `graph/edges.py` — `should_fallback()` conditional edge for FR-08
- [ ] Create `graph/pipeline.py` — assemble `StateGraph`, add nodes + edges, compile
- [ ] Integration test: run full pipeline with a sample Korean query
- [ ] Create `search/ranker.py` — hybrid score = 0.7 × similarity + 0.3 × structural

### Phase 4 — API Layer
- [ ] Create `api/schemas.py` — `SearchRequest` and `SearchResponse` Pydantic models
- [ ] Create `api/main.py` — FastAPI app with `POST /search` endpoint
- [ ] Add `/health` endpoint
- [ ] Test API: `curl -X POST http://localhost:8000/search -d '{"query": "대시보드 기포"}'`

### Phase 5 — UI Layer
- [ ] Create `ui/app.py` — Streamlit app with three panels:
  - **Panel 1**: Query input
  - **Panel 2**: `🔍 AI 해석 결과` — input terms, mapped component, reason
  - **Panel 3**: `📌 적용 필터` + result cards (score %, cause, solution, material info)
- [ ] Verify demo flow end-to-end in browser

### Phase 6 — Tests
- [ ] Create `tests/conftest.py` — fixtures for mock Anthropic client, in-memory SQLite, temp ChromaDB
- [ ] `tests/test_entity_extractor.py` — test candidate extraction with mock Claude
- [ ] `tests/test_entity_selector.py` — test entity selection with mock candidates
- [ ] `tests/test_pipeline.py` — full graph integration with mocked external services
- [ ] `tests/test_api.py` — FastAPI endpoint tests using `httpx.AsyncClient`
- [ ] All tests pass: `uv run pytest tests/ -v`

### Phase 7 — Polish
- [ ] Add fallback handling for all edge cases (empty query, no vector results, no DB results)
- [ ] Update `README.md` with setup steps, architecture diagram, and demo screenshots section
- [ ] Confirm `ruff check` passes with zero errors
- [ ] Confirm `mypy src/` passes with zero errors
- [ ] Final end-to-end demo run with 3 different Korean queries

---

## 10. Testing Strategy

### What to mock
- `anthropic.AsyncAnthropic` — mock Claude responses to avoid API costs in unit tests
- `chromadb.PersistentClient` — use `chromadb.EphemeralClient()` in tests
- SQLite — use `:memory:` path in conftest

### Integration tests
- `tests/test_pipeline.py` uses real LangGraph with mocked external services
- Should validate state transitions and conditional edges

### Running specific test groups
```bash
uv run pytest tests/test_pipeline.py -v           # pipeline only
uv run pytest tests/ -k "not integration" -v      # skip integration tests
uv run pytest tests/ --cov=src -v                 # with coverage
```

---

## 11. Branch Strategy

- `main` — stable, demo-ready code only
- `master` — initial repo branch (legacy, do not use)
- `claude/<feature>` — AI agent feature branches → PR to `main`
- Branch naming: `claude/phase-N-<description>` (e.g., `claude/phase-1-data-layer`)

### Commit message format
```
<type>: <short description>

<optional body>
```
Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

Example: `feat: implement entity extractor using Claude tool_use (FR-02)`
