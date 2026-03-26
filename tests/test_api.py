from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from material_quality_agent.api.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_search_empty_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/search", json={"query": ""})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_whitespace_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/search", json={"query": "   "})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_returns_response_structure():
    """Test that /search returns the correct response structure with mocked pipeline."""
    mock_state = {
        "user_query": "대시보드 기포",
        "candidate_terms": ["대시보드"],
        "vector_candidates": [{"id": "comp-001", "name": "대시보드 커버", "score": 0.9}],
        "selected_component": "대시보드 커버",
        "selection_reason": "대시보드가 언급됨",
        "filter": {"component": "대시보드 커버"},
        "fallback_used": False,
        "issues": [],
        "ranked_results": [
            {
                "id": "issue-001",
                "component": "대시보드 커버",
                "issue": "표면 기포 발생",
                "cause": "수분 과다 흡수",
                "solution": "건조 공정 최적화",
                "material_code": "MAT-PL-00123",
                "material_class": "플라스틱 수지",
                "class_hierarchy": "원자재 > 플라스틱 > 플라스틱 수지",
                "final_score": 0.85,
                "similarity_score": 0.8,
                "structural_score": 1.0,
                "similarity_breakdown": {
                    "same_component": True,
                    "issue_similarity": 0.8,
                    "cause_similarity": 0.72,
                },
            }
        ],
        "explanation": "대시보드 커버의 기포 문제입니다.",
    }

    with patch(
        "material_quality_agent.api.main.run_pipeline",
        new=AsyncMock(return_value=mock_state),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/search", json={"query": "대시보드 기포"})

    assert response.status_code == 200
    data = response.json()
    assert "query_interpretation" in data
    assert "filter_applied" in data
    assert "results" in data
    assert "explanation" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["component"] == "대시보드 커버"
