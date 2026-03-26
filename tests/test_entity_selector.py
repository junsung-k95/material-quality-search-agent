from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_select_entity_parses_tool_use():
    """Test that select_entity correctly parses tool_use response."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "select_entity"
    mock_block.input = {
        "selected_component": "대시보드 커버",
        "reason": "질의에서 대시보드가 언급되었고 유사도가 가장 높습니다.",
    }

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    candidates = [
        {"id": "comp-001", "name": "대시보드 커버", "score": 0.95},
        {"id": "comp-002", "name": "도어 트림 패널", "score": 0.60},
    ]

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from material_quality_agent.tools.entity_selector import select_entity

        result = await select_entity("대시보드 쪽에서 기포가 생김", candidates)

    assert result["selected_component"] == "대시보드 커버"
    assert "reason" in result


@pytest.mark.asyncio
async def test_select_entity_empty_candidates():
    """Test that select_entity handles empty candidates gracefully."""
    from material_quality_agent.tools.entity_selector import select_entity

    result = await select_entity("대시보드 쪽에서 기포가 생김", [])

    assert result["selected_component"] == ""
    assert "후보 부품이 없습니다" in result["reason"]


@pytest.mark.asyncio
async def test_select_entity_fallback_on_missing_tool_use():
    """Test that select_entity falls back to first candidate when no tool_use block."""
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "대시보드 커버를 선택합니다."

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    candidates = [
        {"id": "comp-001", "name": "대시보드 커버", "score": 0.95},
    ]

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from material_quality_agent.tools.entity_selector import select_entity

        result = await select_entity("대시보드 쪽에서 기포가 생김", candidates)

    assert result["selected_component"] == "대시보드 커버"
