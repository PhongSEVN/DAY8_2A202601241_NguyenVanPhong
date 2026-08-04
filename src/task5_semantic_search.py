"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer
    try:
        from .task4_chunking_indexing import EMBEDDING_MODEL
    except ImportError:
        from task4_chunking_indexing import EMBEDDING_MODEL

    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_collection():
    import chromadb
    try:
        from .task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME
    except ImportError:
        from task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not isinstance(query, str) or not query.strip():
        return []
    if top_k <= 0:
        return []

    model = _get_embedding_model()
    query_vector = model.encode(
        query.strip(), normalize_embeddings=True
    ).tolist()

    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for content, metadata, distance in zip(documents, metadatas, distances):
        output.append({
            "content": content,
            "score": round(max(0.0, 1.0 - float(distance)), 4),
            "metadata": metadata or {},
        })

    return sorted(output, key=lambda item: item["score"], reverse=True)


if __name__ == "__main__":
    # Test
    results = semantic_search("what is the tuition fee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
