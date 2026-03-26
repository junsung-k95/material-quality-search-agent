import logging

import anthropic

from material_quality_agent.config import settings

logger = logging.getLogger(__name__)

SELECT_TOOL = {
    "name": "select_entity",
    "description": "후보 부품 목록 중 사용자 질의에 가장 적합한 부품을 선택합니다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "selected_component": {
                "type": "string",
                "description": "선택된 부품 이름",
            },
            "reason": {
                "type": "string",
                "description": "선택 이유 (한국어)",
            },
        },
        "required": ["selected_component", "reason"],
    },
}


async def select_entity(query: str, candidates: list[dict]) -> dict:
    if not candidates:
        return {"selected_component": "", "reason": "후보 부품이 없습니다."}

    candidate_text = "\n".join(
        [f"- {c['name']} (유사도: {c['score']:.2f})" for c in candidates]
    )
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=512,
        tools=[SELECT_TOOL],
        tool_choice={"type": "tool", "name": "select_entity"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"사용자 질의: {query}\n\n"
                    f"후보 부품 목록:\n{candidate_text}\n\n"
                    f"위 후보 중 질의와 가장 관련 있는 부품을 선택하고 이유를 설명하세요."
                ),
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "select_entity":
            return block.input
    logger.warning("No tool_use block found in entity selection response")
    return {"selected_component": candidates[0]["name"], "reason": "기본 선택"}
