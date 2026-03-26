import logging

from fastapi import FastAPI, HTTPException

from material_quality_agent.api.schemas import (
    QueryInterpretation,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SimilarityBreakdown,
)
from material_quality_agent.config import settings
from material_quality_agent.graph.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Material Quality Search Agent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        state = await run_pipeline(request.query)
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))

    results = []
    for i, r in enumerate(state["ranked_results"], 1):
        results.append(
            SearchResult(
                rank=i,
                score=r["final_score"],
                component=r.get("component", ""),
                issue=r.get("issue", ""),
                cause=r.get("cause", ""),
                solution=r.get("solution", ""),
                material_code=r.get("material_code", ""),
                material_class=r.get("material_class", ""),
                class_hierarchy=r.get("class_hierarchy", ""),
                similarity_breakdown=SimilarityBreakdown(
                    same_component=r.get("similarity_breakdown", {}).get("same_component", False),
                    issue_similarity=r.get("similarity_breakdown", {}).get(
                        "issue_similarity", 0.0
                    ),
                    cause_similarity=r.get("similarity_breakdown", {}).get(
                        "cause_similarity", 0.0
                    ),
                ),
            )
        )

    return SearchResponse(
        query_interpretation=QueryInterpretation(
            input_terms=state["candidate_terms"],
            mapped_component=state["selected_component"],
            reason=state["selection_reason"],
            fallback_used=state["fallback_used"],
        ),
        filter_applied=state["filter"],
        results=results,
        explanation=state["explanation"],
    )
