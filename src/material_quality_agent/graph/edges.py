from material_quality_agent.graph.state import AgentState


def should_fallback(state: AgentState) -> str:
    """Conditional edge: if no issues found, use fallback (full search)."""
    if not state.get("issues"):
        return "fallback"
    return "continue"
