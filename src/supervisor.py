"""
Supervisor + Workers song song — pattern nâng cao (Role 1: ghép/điều phối).

Task9.retrieve() gọi semantic_search() rồi lexical_search() TUẦN TỰ (dù docstring
Task 9 ghi "song song" — trên thực tế 2 lệnh gọi chạy nối tiếp nhau). File này bổ
sung 1 supervisor thật sự chạy 2 worker đó song song bằng ThreadPoolExecutor (cả
hai đều I/O-bound: gọi OpenAI embedding API + query ChromaDB, và tính BM25 cục bộ)
rồi tái dùng nguyên vẹn Task 7 (RRF/rerank), Task 8 (PageIndex fallback), Task 9
(ngưỡng fallback, cấu hình) và Task 10 (generation) — không viết lại logic của
các task đó, chỉ thay tầng dispatch retrieval từ tuần tự sang song song.

So sánh tốc độ: chạy trực tiếp file này để in thời gian retrieve() (Task 9,
tuần tự) vs parallel_retrieve() (supervisor, song song) trên cùng bộ câu hỏi.
"""

import time
from concurrent.futures import ThreadPoolExecutor

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search
from .task9_retrieval_pipeline import DEFAULT_TOP_K, RERANK_METHOD, SCORE_THRESHOLD
from .task10_generation import generate_with_citation


def parallel_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Ban sao cua Task9.retrieve(), nhung Worker 1 (semantic_search) va Worker 2
    (lexical_search) duoc Supervisor (ThreadPoolExecutor) phat song song thay vi
    goi tuan tu — giam latency retrieval khi ca hai worker deu cham (embedding
    API co network round-trip; BM25 tren corpus lon co the ton CPU).

    Args, Returns: giong het task9_retrieval_pipeline.retrieve().
    """
    # Worker 1 + Worker 2 chay song song
    with ThreadPoolExecutor(max_workers=2) as executor:
        dense_future = executor.submit(semantic_search, query, top_k * 2)
        sparse_future = executor.submit(lexical_search, query, top_k * 2)
        dense_results = dense_future.result()
        sparse_results = sparse_future.result()

    # Tu day tro di: tai dung nguyen Task 7/8/9 logic (khong viet lai)
    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    for item in merged:
        item["source"] = "hybrid"

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        for item in final_results:
            item.setdefault("source", "hybrid")
    else:
        final_results = merged[:top_k]

    best_score = dense_results[0]["score"] if dense_results else 0.0
    if best_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
        except Exception:
            fallback = None
        if fallback:
            for item in fallback:
                item.setdefault("source", "pageindex")
            return fallback

    return final_results[:top_k]


def parallel_generate_with_citation(query: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    Wrapper generate_with_citation() (Task 10) nhung dung parallel_retrieve() o
    tren thay vi goi retrieve() tuan tu cua Task 9. Ket qua tuong duong, chi khac
    thoi gian retrieval.
    """
    from .task10_generation import (
        MAX_TOKENS, SYSTEM_PROMPT, TEMPERATURE, TOP_P, LLM_MODEL,
        format_context, reorder_for_llm, _format_history, _is_greeting,
    )

    if _is_greeting(query):
        from .task10_generation import GREETING_RESPONSE
        return {"answer": GREETING_RESPONSE, "sources": [], "retrieval_source": "none"}

    chunks = parallel_retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks) if chunks else []
    context = format_context(reordered) if reordered else "(Khong tim thay tai lieu lien quan)"
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"

    import os
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_TOKENS,
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
    }


if __name__ == "__main__":
    from .task9_retrieval_pipeline import retrieve

    test_queries = [
        "What is the tuition fee at RMIT Vietnam?",
        "What scholarships are available for international students?",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")

        t0 = time.perf_counter()
        retrieve(q, top_k=3)
        t_sequential = time.perf_counter() - t0

        t0 = time.perf_counter()
        parallel_retrieve(q, top_k=3)
        t_parallel = time.perf_counter() - t0

        print(f"  Task 9 (tuan tu):        {t_sequential:.3f}s")
        print(f"  Supervisor (song song):  {t_parallel:.3f}s")
