from unittest.mock import AsyncMock

import pytest

from material_quality_agent.db.seed_data import COMPONENTS, ISSUES


@pytest.fixture
def mock_anthropic_client(mocker):
    mock = AsyncMock()
    mocker.patch("anthropic.AsyncAnthropic", return_value=mock)
    return mock


@pytest.fixture
def in_memory_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    return db_path


@pytest.fixture
def sample_components():
    return COMPONENTS[:3]


@pytest.fixture
def sample_issues():
    return ISSUES[:5]
