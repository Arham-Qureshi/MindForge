# Classifier Research — Optimized for MindForge (Syllabus / PYQ / Notes)

**Date:** 2026-08-29
**Status:** Research only (no engine swap yet)
**Goal:** <5ms p50, >95% accuracy, offline, zero LLM cost, reuse existing `fastembed` install

## 1. Current Baseline

**File:** `ai-engine/app/classifiers/heuristic_engine.py:38-51` + `regex_patterns.py` + `score_calculator.py`

- 3 bags × 8 regex, `MAX_INPUT_CHARS 5000`, plain count, `winner/total` confidence, tie→NOTES
- `test_classifier.py:99-160` hand-samples → ~85-88% (lexical heavy, fails on paraphrase / mixed docs)
- <1ms, no deps, no training

**Problem você flagged `ViewSwitcher.tsx:30`:** needs more promising + still fast.

## 2. Candidates Researched (papers + benchmarks above)

| # | Algorithm | Accuracy (reported) | Latency | Cost / Deps | Notes for MindForge |
|---|-----------|---------------------|---------|-------------|---------------------|
| 1 | **Weighted regex** (same bags + per-pattern weight + position bonus) | 90-92% (est) | <1ms | zero | Quick win, still keyword-bound |
| 2 | **TF-IDF + Naive Bayes** (SQM-NB framework, 2026 paper) | 98-100% on syllabus-Q mapping, 0.55 on message triage | 5-10ms + fit | sklearn, needs 40 docs | Strong lexical, good for Syllabus/PYQ keywords |
| 3 | **TF-IDF + Logistic / SVM** (RAGRouter-Bench 7.7k, BBC News) | 93.2% acc, 0.928 F1 (TF-IDF+SVM); 98.4% BBC | 5-10ms | sklearn | TF-IDF beats MiniLM by 3pts for type routing — surface keywords dominate syllabus/pyq |
| 4 | **FastEmbed cosine centroid** (`BAAI/bge-small-en-v1.5` — already in `chunker.py:5`) | 96-98% est | ~30ms cold, 5ms warm | fastembed, 120MB model | Robust to paraphrase, reuses install |
| 5 | **Hybrid regex → embed fallback** | 96-98% + <5ms avg | <1ms fast path 80%, 30ms fallback 20% | fastembed + regex | Best avg latency, highest robustness — **RECOMMENDED** |
| 6 | **BiLSTM / BERT** | 98.5% / 99.2% | 20min train, 50-600ms infer | torch, GPU | Overkill for 3 classes, not local-first |
| 7 | **LLM fallback** (`LogIQ` pattern: regex → embed → Groq) | 99.7% combined (500 regex 100%, 571 BERT 0.989) | 300ms + LLM cost | Groq API | Not needed for 3-way, adds cost/latency |

**Sparse wins consistently:** 73-dataset study — tf-idf/feat-hash beats Word2Vec/GloVe/FastText/ELMo/Flair on 61/73 (+3-5% F1), especially for <5 class, keyword-separable tasks like syllabus vs pyq.

## 3. Recommendation — Hybrid (regex fast path + FastEmbed tie-break)

**Why for MindForge:**
- 3 classes are keyword-separable (module/unit/syllabus vs q./marks/time vs definition/chapter) → regex nails 80%
- Remaining 20% ambiguous (mixed docs, paraphrased) → embed centroid fixes without LLM
- Reuses `fastembed` already installed for chunker → zero new dep
- Offline, zero token cost, <5ms avg (regex <1ms, embed 30ms only on 20%)

**Architecture:**
```
text[:5000] → regex counts → confidence = winner/total
  if confidence >= 0.7 and margin >= 2 → return regex winner
  else → embed(text) cosine to 3 centroids → winner = argmax cosine, confidence = (cos_max - cos_2nd) normalized
```
- Centroids: offline `scripts/build_centroids.py` embeds 40 labeled docs (synthesize from `docs/PRD`+`IMP/` if no set) → `app/classifiers/centroids.json` (3×384 dim)
- Keep `ClassificationResult` shape, add `method: "regex" | "embed"` for observability
- Thresholds tunable via `ai-engine/app/core/config.py`

**Data needed:**
- 40 docs (15 syllabus, 15 PYQ, 10 notes) — can synthesize: syllabus = module/unit/credits text, PYQ = q./marks/time/attempt, notes = definition/for example/therefore
- Store centroids, not raw docs → privacy kept

## 4. Evaluation Plan (before swapping engine)

1. Build 40-doc set, run baseline → confusion matrix, F1 per class, p50 latency
2. Train TF-IDF+LR and embed centroids on same 40, 5-fold cross-val
3. Compare hybrid vs baseline on same set, measure fallback rate, latency, confidence calibration
4. Gate: if hybrid >=95% and p50 <5ms, approve engine swap; else keep weighted regex

## 5. Implementation Sketch (when approved)

- `app/classifiers/regex_patterns.py` — keep, add weights dict
- `app/classifiers/centroids.json` — new, gitignored until built
- `app/classifiers/heuristic_engine.py` — add `classify_embedding()` and `classify_document()` branching
- `scripts/build_centroids.py` — new, offline only
- `tests/test_classifier.py` — add 40-doc accuracy + latency budget tests
- No `llm_client` or gateway change

## 6. Tradeoff to confirm

- **Q you answered:** synthesize 40 if no labeled set → yes, proceed with synthesis
- **Target:** <5ms p50, >95% accuracy — as you said

Next step when you exit plan mode: run `scripts/build_centroids.py` on synthesized 40 and deliver benchmark table before engine swap.
