from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import numpy as np
import pytest

from material_quality_agent.db.issue_db import init_db, insert_issues
from material_quality_agent.db.seed_data import COMPONENTS, ISSUES


def make_extract_mock(terms: list[str]):
    """Create a mock that returns the specified candidate terms."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_entities"
    mock_block.input = {"candidate_terms": terms}

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


def make_select_mock(component: str, reason: str):
    """Create a mock that returns the specified selected component."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "select_entity"
    mock_block.input = {"selected_component": component, "reason": reason}

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


def make_explanation_mock(text: str):
    """Create a mock that returns a text explanation."""
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = text

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


def make_fake_embedding(dim: int = 384) -> list[float]:
    """Create a deterministic fake embedding vector."""
    rng = np.random.default_rng(42)
    vec = rng.random(dim).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def fake_embed(texts: list[str]) -> list[list[float]]:
    """Return fake embeddings for a list of texts."""
    return [make_fake_embedding() for _ in texts]


def fake_embed_one(text: str) -> list[float]:
    """Return a fake embedding for a single text."""
    return make_fake_embedding()


def seed_ephemeral_chroma(client: chromadb.ClientAPI) -> None:
    """Seed components and issues into an ephemeral ChromaDB client."""
    from material_quality_agent.vector.store import COMPONENT_COLLECTION, ISSUE_COLLECTION

    comp_col = client.get_or_create_collection(COMPONENT_COLLECTION)
    comp_embeddings = fake_embed([c["name"] for c in COMPONENTS])
    comp_col.upsert(
        ids=[c["id"] for c in COMPONENTS],
        embeddings=comp_embeddings,
        metadatas=[{"name": c["name"], "product": c["product"]} for c in COMPONENTS],
        documents=[c["name"] for c in COMPONENTS],
    )

    issue_col = client.get_or_create_collection(ISSUE_COLLECTION)
    texts = [f"{i['issue']} {i['cause']} {i['component']}" for i in ISSUES]
    issue_embeddings = fake_embed(texts)
    issue_col.upsert(
        ids=[i["id"] for i in ISSUES],
        embeddings=issue_embeddings,
        metadatas=[{"component": i["component"], "issue": i["issue"]} for i in ISSUES],
        documents=texts,
    )


@pytest.mark.asyncio
async def test_pipeline_with_mocked_claude(tmp_path):
    """Test the full pipeline with mocked Claude calls and real DBs."""
    db_path = str(tmp_path / "test.db")

    # Seed SQLite
    init_db(db_path)
    insert_issues(db_path, ISSUES)

    # Set up ephemeral ChromaDB
    ephemeral_client = chromadb.EphemeralClient()
    seed_ephemeral_chroma(ephemeral_client)

    # Set up Claude mock responses
    extract_response = make_extract_mock(["대시보드"])
    select_response = make_select_mock("대시보드 커버", "대시보드가 언급되어 선택")
    explanation_response = make_explanation_mock(
        "대시보드 커버에서 기포 문제가 발생했습니다. 수분 과다가 주요 원인입니다."
    )

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=[extract_response, select_response, explanation_response]
    )

    with (
        patch("anthropic.AsyncAnthropic", return_value=mock_client),
        patch("material_quality_agent.config.settings.db_path", db_path),
        patch("material_quality_agent.vector.store.get_client", return_value=ephemeral_client),
        patch("material_quality_agent.vector.store.embed", side_effect=fake_embed),
        patch("material_quality_agent.vector.store.embed_one", side_effect=fake_embed_one),
    ):
        from material_quality_agent.graph.pipeline import run_pipeline

        state = await run_pipeline("대시보드 쪽에서 기포가 생김")

    assert state["candidate_terms"] == ["대시보드"]
    assert state["selected_component"] == "대시보드 커버"
    assert len(state["ranked_results"]) > 0
    assert state["explanation"] != ""


@pytest.mark.asyncio
async def test_pipeline_fallback_when_no_issues(tmp_path):
    """Test that fallback is triggered when filter returns no issues."""
    db_path = str(tmp_path / "test.db")

    # Seed SQLite with issues
    init_db(db_path)
    insert_issues(db_path, ISSUES)

    # Set up ephemeral ChromaDB
    ephemeral_client = chromadb.EphemeralClient()
    seed_ephemeral_chroma(ephemeral_client)

    # Mock with a component that does NOT exist in DB (triggers fallback)
    extract_response = make_extract_mock(["존재하지않는부품"])
    select_response = make_select_mock("존재하지않는부품", "테스트용 선택")
    explanation_response = make_explanation_mock("폴백 검색 결과입니다.")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=[extract_response, select_response, explanation_response]
    )

    with (
        patch("anthropic.AsyncAnthropic", return_value=mock_client),
        patch("material_quality_agent.config.settings.db_path", db_path),
        patch("material_quality_agent.vector.store.get_client", return_value=ephemeral_client),
        patch("material_quality_agent.vector.store.embed", side_effect=fake_embed),
        patch("material_quality_agent.vector.store.embed_one", side_effect=fake_embed_one),
    ):
        from material_quality_agent.graph import pipeline as pipeline_module

        state = await pipeline_module.run_pipeline("존재하지않는부품에서 문제가 생김")

    # Fallback should have been used and results from all issues returned
    assert state["fallback_used"] is True
    assert len(state["ranked_results"]) > 0
