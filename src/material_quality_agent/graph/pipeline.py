from langgraph.graph import END, StateGraph

from material_quality_agent.graph.edges import should_fallback
from material_quality_agent.graph.nodes import (
    build_filter_node,
    extract_entities_node,
    generate_explanation_node,
    hybrid_rank_node,
    query_issues_node,
    select_entity_node,
    vector_search_node,
)
from material_quality_agent.graph.state import AgentState


def create_pipeline():
    graph = StateGraph(AgentState)

    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("vector_search", vector_search_node)
    graph.add_node("select_entity", select_entity_node)
    graph.add_node("build_filter", build_filter_node)
    graph.add_node("query_issues", query_issues_node)
    graph.add_node("hybrid_rank", hybrid_rank_node)
    graph.add_node("generate_explanation", generate_explanation_node)

    graph.set_entry_point("extract_entities")
    graph.add_edge("extract_entities", "vector_search")
    graph.add_edge("vector_search", "select_entity")
    graph.add_edge("select_entity", "build_filter")

    # Conditional edge: fallback if no issues found
    graph.add_conditional_edges(
        "query_issues",
        should_fallback,
        {"continue": "hybrid_rank", "fallback": "hybrid_rank"},
    )
    graph.add_edge("build_filter", "query_issues")
    graph.add_edge("hybrid_rank", "generate_explanation")
    graph.add_edge("generate_explanation", END)

    return graph.compile()


pipeline = create_pipeline()


async def run_pipeline(query: str) -> AgentState:
    initial_state: AgentState = {
        "user_query": query,
        "candidate_terms": [],
        "vector_candidates": [],
        "selected_component": "",
        "selection_reason": "",
        "filter": {},
        "fallback_used": False,
        "issues": [],
        "ranked_results": [],
        "explanation": "",
    }
    result = await pipeline.ainvoke(initial_state)
    return result
