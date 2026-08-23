from app.pipelines.base_pipeline import execute_chunks
from app.schemas.pyq_schema import PYQAnalysisPayload


def merge_pyq_results(results: list[dict]) -> PYQAnalysisPayload:
    if not results:
        return PYQAnalysisPayload(topic_frequency=[], predicted_questions=[])

    topic_totals: dict[str, dict] = {}
    all_questions: list[dict] = []

    for r in results:
        for tf in r.get("topic_frequency", []):
            t = tf["topic"]
            if t in topic_totals:
                topic_totals[t]["question_count"] += tf["question_count"]
                topic_totals[t]["raw_percentages"].append(tf["percentage"])
            else:
                topic_totals[t] = {
                    "question_count": tf["question_count"],
                    "raw_percentages": [tf["percentage"]],
                }
        all_questions.extend(r.get("predicted_questions", []))

    total_count = sum(v["question_count"] for v in topic_totals.values())
    topic_frequency = []
    for topic, data in topic_totals.items():
        pct = data["question_count"] / total_count if total_count > 0 else 0.0
        topic_frequency.append({
            "topic": topic,
            "percentage": round(pct, 4),
            "question_count": data["question_count"],
        })
    topic_frequency.sort(key=lambda x: x["question_count"], reverse=True)

    seen: dict[str, dict] = {}
    for q in all_questions:
        key = q["question"]
        if key not in seen or q.get("probability_score", 0) > seen[key].get("probability_score", 0):
            seen[key] = q
    predicted_questions = sorted(seen.values(), key=lambda x: x.get("probability_score", 0), reverse=True)

    return PYQAnalysisPayload(
        topic_frequency=topic_frequency,
        predicted_questions=predicted_questions,
    )


def process_pyq(chunks: list[str]) -> PYQAnalysisPayload:
    results = execute_chunks(chunks, task="pyq")
    return merge_pyq_results(results)
