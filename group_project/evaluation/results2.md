# RAG Evaluation Results (snapshot demo — chạy 2026-08-04)

> Copy từ `results.md` để giữ lại cho demo, tránh bị ghi đè bởi lần chạy sau.
> Chạy với `EVAL_SAMPLE_SIZE=3` (3 câu đầu golden_dataset), model `gpt-4o-mini`
> qua OpenAI trực tiếp. Một số job bị `TimeoutError` (trùng lúc backend cũng
> đang gọi API cho query khác → tranh rate limit) nên vài giá trị bị `nan` —
> đủ dùng demo, không phải số liệu final.

## Framework sử dụng

RAGAS (`pip install ragas`)

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| faithfulness | 0.000 | nan | +nan |
| answer_relevancy | 0.332 | 0.407 | -0.075 |
| context_recall | 1.000 | 1.000 | +0.000 |
| context_precision | 0.917 | 0.917 | +0.000 |
| **Average** | **0.562** | **nan** | **+nan** |

---

## A/B Comparison Analysis

**Config A (hybrid_rerank):** semantic search + BM25 merge bằng RRF (k=60) + rerank.

**Config B (dense_only):** chỉ semantic search (dense retrieval), không BM25, không rerank.

**Kết luận:** Config B có average score cao hơn (0.562 vs 0.562). Điền phân tích chi tiết sau khi chạy với data thật (vì sao rerank/hybrid giúp hay không giúp).

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Automation bias là gì theo bài viết của TS Nhật Quang Trần? | nan | 0.000 | nan | | |
| 2 | RMIT đứng thứ mấy trong số các trường đại học Úc theo QS WUR | 0.000 | 0.664 | 1.000 | | |
| 3 | RMIT xếp hạng bao nhiêu trong bảng QS World University Ranki | nan | nan | 1.000 | | |

---

## Recommendations

### Cải tiến 1
**Action:** Điền sau khi phân tích worst performers.
**Expected impact:**

### Cải tiến 2
**Action:**
**Expected impact:**

### Cải tiến 3
**Action:**
**Expected impact:**

---

## TODO tối nay

- Resolve merge conflict 4 file: `src/task10_generation.py`, `src/task5_semantic_search.py`,
  `src/task4_chunking_indexing.py`, `src/task2_crawl_news.py` (+ conflict file nhị phân
  `chroma_db/chroma.sqlite3`, `data/standardized/**`).
- Quyết định embedding model dùng chung: bản mình (OpenAI text-embedding-3-small, đã
  index thật) vs bản remote (BAAI/bge-m3 local) — không trộn 2 bên vì lệch số chiều vector.
- Sau khi resolve xong, xoá `EVAL_SAMPLE_SIZE=3` hoặc set full, chạy lại RAGAS full 16 câu
  để có `results.md` chính thức thay bản demo này.
