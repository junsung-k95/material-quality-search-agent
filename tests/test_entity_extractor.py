from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_extract_entities_parses_tool_use():
    """Test that extract_entities correctly parses tool_use response."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_entities"
    mock_block.input = {"candidate_terms": ["대시보드"]}

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from material_quality_agent.tools.entity_extractor import extract_entities

        result = await extract_entities("대시보드 쪽에서 기포가 생김")

    assert result == ["대시보드"]


@pytest.mark.asyncio
async def test_extract_entities_returns_empty_on_missing_tool_use():
    """Test that extract_entities returns empty list when no tool_use block."""
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "대시보드"

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from material_quality_agent.tools.entity_extractor import extract_entities

        result = await extract_entities("대시보드 쪽에서 기포가 생김")

    assert result == []


@pytest.mark.asyncio
async def test_extract_entities_multiple_terms():
    """Test that extract_entities returns multiple candidate terms."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_entities"
    mock_block.input = {"candidate_terms": ["도어", "트림", "패널"]}

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from material_quality_agent.tools.entity_extractor import extract_entities

        result = await extract_entities("도어 트림 패널에 긁힘이 생겼습니다")

    assert result == ["도어", "트림", "패널"]
