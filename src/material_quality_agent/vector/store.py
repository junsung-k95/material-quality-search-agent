import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from material_quality_agent.vector.embedder import embed, embed_one

logger = logging.getLogger(__name__)

COMPONENT_COLLECTION = "components"
ISSUE_COLLECTION = "issues"


def get_client(chroma_path: str) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=chroma_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def seed_components(chroma_path: str, components: list[dict]) -> None:
    client = get_client(chroma_path)
    col = client.get_or_create_collection(COMPONENT_COLLECTION)
    embeddings = embed([c["name"] for c in components])
    col.upsert(
        ids=[c["id"] for c in components],
        embeddings=embeddings,
        metadatas=[{"name": c["name"], "product": c["product"]} for c in components],
        documents=[c["name"] for c in components],
    )
    logger.info("Seeded %d components into ChromaDB", len(components))


def seed_issues(chroma_path: str, issues: list[dict]) -> None:
    client = get_client(chroma_path)
    col = client.get_or_create_collection(ISSUE_COLLECTION)
    texts = [f"{i['issue']} {i['cause']} {i['component']}" for i in issues]
    embeddings = embed(texts)
    col.upsert(
        ids=[i["id"] for i in issues],
        embeddings=embeddings,
        metadatas=[{"component": i["component"], "issue": i["issue"]} for i in issues],
        documents=texts,
    )
    logger.info("Seeded %d issues into ChromaDB", len(issues))


def search_components(chroma_path: str, query: str, top_k: int = 5) -> list[dict]:
    client = get_client(chroma_path)
    col = client.get_or_create_collection(COMPONENT_COLLECTION)
    query_embedding = embed_one(query)
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_embeddings=[query_embedding], n_results=min(top_k, count))
    candidates = []
    for doc_id, metadata, distance in zip(
        results["ids"][0], results["metadatas"][0], results["distances"][0]
    ):
        score = max(0.0, 1.0 - distance)
        candidates.append({"id": doc_id, "name": metadata["name"], "score": round(score, 4)})
    return candidates


def search_issues(
    chroma_path: str,
    query: str,
    issue_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    client = get_client(chroma_path)
    col = client.get_or_create_collection(ISSUE_COLLECTION)
    query_embedding = embed_one(query)
    where = {"id": {"$in": issue_ids}} if issue_ids and len(issue_ids) >= 1 else None
    n = min(top_k, col.count())
    if n == 0:
        return []
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=n,
        where=where,
    )
    scored = []
    for doc_id, metadata, distance in zip(
        results["ids"][0], results["metadatas"][0], results["distances"][0]
    ):
        score = max(0.0, 1.0 - distance)
        scored.append({"id": doc_id, "score": round(score, 4), **metadata})
    return scored
