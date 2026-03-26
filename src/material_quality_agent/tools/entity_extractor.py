import logging

import anthropic

from material_quality_agent.config import settings

logger = logging.getLogger(__name__)

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


async def extract_entities(query: str) -> list[str]:
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
