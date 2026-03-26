from typing import TypedDict


class AgentState(TypedDict):
    user_query: str
    candidate_terms: list[str]
    vector_candidates: list[dict]
    selected_component: str
    selection_reason: str
    filter: dict
    fallback_used: bool
    issues: list[dict]
    ranked_results: list[dict]
    explanation: str
