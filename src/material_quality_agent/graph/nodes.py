import logging

import anthropic

from material_quality_agent.config import settings
from material_quality_agent.db.issue_db import get_all, query_by_filter
from material_quality_agent.graph.state import AgentState
from material_quality_agent.search.ranker import hybrid_rank
from material_quality_agent.tools.entity_extractor import extract_entities
from material_quality_agent.tools.entity_selector import select_entity
from material_quality_agent.tools.filter_builder import build_filter
from material_quality_agent.vector.store import search_components, search_issues

logger = logging.getLogger(__name__)


async def extract_entities_node(state: AgentState) -> dict:
    query = state["user_query"]
    logger.info("extract_entities_node: query=%s", query)
    candidate_terms = await extract_entities(query)
    logger.info("Extracted candidate terms: %s", candidate_terms)
    return {"candidate_terms": candidate_terms}


async def vector_search_node(state: AgentState) -> dict:
    query = state["user_query"]
    candidate_terms = state.get("candidate_terms", [])
    search_query = " ".join(candidate_terms) if candidate_terms else query
    logger.info("vector_search_node: search_query=%s", search_query)
    candidates = search_components(settings.chroma_path, search_query, top_k=settings.top_k)
    logger.info("Vector search candidates: %s", candidates)
    return {"vector_candidates": candidates}


async def select_entity_node(state: AgentState) -> dict:
    query = state["user_query"]
    candidates = state.get("vector_candidates", [])
    logger.info("select_entity_node: %d candidates", len(candidates))
    result = await select_entity(query, candidates)
    return {
        "selected_component": result.get("selected_component", ""),
        "selection_reason": result.get("reason", ""),
    }


async def build_filter_node(state: AgentState) -> dict:
    selected_component = state.get("selected_component", "")
    logger.info("build_filter_node: selected_component=%s", selected_component)
    filter_dict = build_filter(selected_component)
    return {"filter": filter_dict}


async def query_issues_node(state: AgentState) -> dict:
    filter_dict = state.get("filter", {})
    logger.info("query_issues_node: filter=%s", filter_dict)
    issues = query_by_filter(settings.db_path, filter_dict)
    fallback_used = False
    if not issues:
        logger.info("No issues found with filter, falling back to get_all")
        issues = get_all(settings.db_path)
        fallback_used = True
    logger.info("Found %d issues (fallback=%s)", len(issues), fallback_used)

    # Get similarity scores for these issues from vector store
    issue_ids = [i["id"] for i in issues]
    query = state["user_query"]
    scored_issues = search_issues(
        settings.chroma_path,
        query,
        issue_ids=issue_ids if len(issue_ids) > 1 else None,
        top_k=len(issue_ids) if issue_ids else settings.top_k,
    )
    # Build similarity score map
    sim_map: dict[str, float] = {s["id"]: s["score"] for s in scored_issues}
    # Attach scores to issues
    for issue in issues:
        issue["_similarity_score"] = sim_map.get(issue["id"], 0.0)

    return {"issues": issues, "fallback_used": fallback_used}


async def hybrid_rank_node(state: AgentState) -> dict:
    issues = state.get("issues", [])
    selected_component = state.get("selected_component", "")
    logger.info("hybrid_rank_node: %d issues, component=%s", len(issues), selected_component)
    similarity_scores = {i["id"]: i.get("_similarity_score", 0.0) for i in issues}
    ranked = hybrid_rank(issues, similarity_scores, selected_component, top_k=settings.top_k)
    return {"ranked_results": ranked}


async def generate_explanation_node(state: AgentState) -> dict:
    ranked_results = state.get("ranked_results", [])
    selected_component = state.get("selected_component", "")
    user_query = state.get("user_query", "")

    if not ranked_results:
        return {"explanation": "관련된 품질 이슈를 찾을 수 없습니다."}

    top_issues_text = "\n".join(
        [
            (
                f"{i + 1}. 문제: {r.get('issue', '')}, "
                f"원인: {r.get('cause', '')}, "
                f"해결: {r.get('solution', '')}"
            )
            for i, r in enumerate(ranked_results[:3])
        ]
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "다음 자동차 내장재 품질 검색 결과를 바탕으로 간결한 한국어 설명을 작성하세요."
                    f"\n\n사용자 질의: {user_query}\n"
                    f"관련 부품: {selected_component}\n\n"
                    f"상위 검색 결과:\n{top_issues_text}\n\n"
                    f"2-3 문장으로 핵심 원인과 해결 방향을 요약하세요."
                ),
            }
        ],
    )
    explanation = ""
    for block in response.content:
        if hasattr(block, "text"):
            explanation = block.text
            break

    logger.info("Generated explanation: %s", explanation[:100] if explanation else "")
    return {"explanation": explanation}
