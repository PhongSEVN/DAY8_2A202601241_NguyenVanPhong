# RAG Evaluation Results

## Framework sử dụng

RAGAS (`pip install ragas`)

---

## Trạng thái

> Chưa chạy thật — pipeline (`src/task9_retrieval_pipeline.py`, `src/task10_generation.py`)
> đang phụ thuộc Task 5-8 (chưa implement) nên `generate_with_citation()` còn raise
> `NotImplementedError`. `eval_pipeline.py` đã code đầy đủ (RAGAS 4 metrics + A/B
> hybrid_rerank vs dense_only) và đã smoke-test cơ chế export bằng data giả — chỉ cần
> chạy `python -m group_project.evaluation.eval_pipeline` sau khi:
> 1. Task 4 index xong `chroma_db/`
> 2. Task 5-8 implement xong
> 3. `.env` có `OPENROUTER_API_KEY` hợp lệ
>
> Script sẽ tự ghi đè phần dưới bằng số liệu thật.

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | | | |
| Answer Relevance | | | |
| Context Recall | | | |
| Context Precision | | | |
| **Average** | | | |

---

## A/B Comparison Analysis

**Config A (hybrid_rerank):** semantic search + BM25 merge bằng RRF (k=60) + rerank.

**Config B (dense_only):** chỉ semantic search (dense retrieval), không BM25, không rerank.

**Kết luận:**
> Điền sau khi chạy với data thật.

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

---

## Recommendations

### Cải tiến 1
**Action:**
**Expected impact:**

### Cải tiến 2
**Action:**
**Expected impact:**

### Cải tiến 3
**Action:**
**Expected impact:**
