import logging
import re

import anthropic

from material_quality_agent.config import settings

logger = logging.getLogger(__name__)

# Korean particles / auxiliary words to strip when running without Claude
_KO_STOPWORDS = {
    "에서", "에서의", "에", "의", "을", "를", "이", "가", "은", "는", "도", "만",
    "와", "과", "랑", "이랑", "로", "으로", "까지", "부터", "에서도",
    "쪽", "쪽에서", "쪽의",
    "생김", "발생", "발생함", "문제", "문제가", "됩니다", "합니다", "있어요",
    "있습니다", "했", "하", "됐", "됩니다", "같아요", "같은", "같습니다",
    "현상", "현상이",
}

EXTRACT_TOOL = {
    "name": "extract_entities",
    "description": "사용자 질의에서 제품/부품으로 추정되는 단어들을 추출합니다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "candidate_terms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "질의에서 추출된 제품/부품 후보 단어 목록",
            }
        },
        "required": ["candidate_terms"],
    },
}


def _extract_entities_fallback(query: str) -> list[str]:
    """Deterministic entity extraction used when ANTHROPIC_API_KEY is not set.
    Splits the query on whitespace/punctuation and removes Korean stopwords."""
    tokens = re.split(r"[\s,./!?]+", query.strip())
    terms = [t for t in tokens if t and t not in _KO_STOPWORDS and len(t) >= 2]
    logger.info("demo_mode entity extraction: %s → %s", query, terms)
    return terms if terms else [query.strip()]


async def extract_entities(query: str) -> list[str]:
    if settings.demo_mode:
        return _extract_entities_fallback(query)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=512,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_entities"},
        messages=[
            {
                "role": "user",
                "content": (
                    "다음 품질 문제 질의에서 제품 또는 부품 이름으로 추정되는 단어를 추출하세요."
                    f"\n\n질의: {query}"
                ),
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_entities":
            return block.input.get("candidate_terms", [])
    logger.warning("No tool_use block found in entity extraction response")
    return []
