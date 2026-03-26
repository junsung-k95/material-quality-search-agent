def hybrid_rank(
    issues: list[dict],
    similarity_scores: dict[str, float],
    selected_component: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Final Score = 0.7 * embedding_similarity + 0.3 * structural_score
    structural_score = 1.0 if same component, 0.0 otherwise
    """
    ranked = []
    for issue in issues:
        sim = similarity_scores.get(issue["id"], 0.0)
        structural = 1.0 if issue.get("component") == selected_component else 0.0
        final_score = 0.7 * sim + 0.3 * structural
        ranked.append(
            {
                **issue,
                "similarity_score": round(sim, 4),
                "structural_score": round(structural, 4),
                "final_score": round(final_score, 4),
                "similarity_breakdown": {
                    "same_component": issue.get("component") == selected_component,
                    "issue_similarity": round(sim, 4),
                    "cause_similarity": round(sim * 0.9, 4),  # approximation for demo
                },
            }
        )
    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked[:top_k]
