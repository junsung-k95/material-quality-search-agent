from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class SimilarityBreakdown(BaseModel):
    same_component: bool
    issue_similarity: float
    cause_similarity: float


class SearchResult(BaseModel):
    rank: int
    score: float
    component: str
    issue: str
    cause: str
    solution: str
    material_code: str
    material_class: str
    class_hierarchy: str
    similarity_breakdown: SimilarityBreakdown


class QueryInterpretation(BaseModel):
    input_terms: list[str]
    mapped_component: str
    reason: str
    fallback_used: bool


class SearchResponse(BaseModel):
    query_interpretation: QueryInterpretation
    filter_applied: dict
    results: list[SearchResult]
    explanation: str
