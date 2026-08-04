"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import json
from pathlib import Path

from rank_bm25 import BM25Okapi

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
NEWS_LANDING_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def _load_corpus() -> list[dict]:
    """
    Đọc corpus từ data/standardized/ (output Task 3). Nếu chưa có (Task 3
    chưa chạy), fallback đọc trực tiếp field 'content_markdown' trong
    data/landing/news/*.json để module vẫn dùng được độc lập.
    """
    corpus = []

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        doc_type = "legal" if "legal" in str(md_file) else "news"
        corpus.append({
            "content": text,
            "metadata": {"source": md_file.name, "type": doc_type},
        })

    if corpus:
        return corpus

    for json_file in NEWS_LANDING_DIR.glob("*.json"):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        text = data.get("content_markdown", "").strip()
        if not text:
            continue
        corpus.append({
            "content": text,
            "metadata": {
                "source": json_file.name,
                "type": "news",
                "title": data.get("title", ""),
                "url": data.get("url", ""),
            },
        })

    return corpus


CORPUS: list[dict] = _load_corpus()
_BM25_INDEX = None


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def _get_index():
    global _BM25_INDEX
    if _BM25_INDEX is None and CORPUS:
        _BM25_INDEX = build_bm25_index(CORPUS)
    return _BM25_INDEX


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not CORPUS:
        return []

    bm25 = _get_index()
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results = []
    for idx in ranked_indices[:top_k]:
        if scores[idx] <= 0:
            continue
        results.append({
            "content": CORPUS[idx]["content"],
            "score": float(scores[idx]),
            "metadata": CORPUS[idx]["metadata"],
        })
    return results


if __name__ == "__main__":
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
