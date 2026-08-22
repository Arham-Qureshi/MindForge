from app.pipelines.base_pipeline import execute_chunks
from app.schemas.syllabus_schema import SyllabusPayload


def merge_syllabus_results(results: list[dict]) -> SyllabusPayload:
    if not results:
        return SyllabusPayload(
            course_title="Unknown",
            total_units=0,
            learning_path=[],
            priority_topics=[],
        )

    first = results[0]
    all_units = []
    all_priorities = []

    for r in results:
        all_units.extend(r.get("learning_path", []))
        all_priorities.extend(r.get("priority_topics", []))

    seen_units = {}
    for u in all_units:
        num = u["unit_number"]
        if num not in seen_units:
            seen_units[num] = u

    sorted_units = sorted(seen_units.values(), key=lambda x: x["unit_number"])

    topic_weights: dict[str, float] = {}
    for p in all_priorities:
        t = p["topic"]
        topic_weights[t] = topic_weights.get(t, 0) + p["weightage"]

    total_weight = sum(topic_weights.values())
    if total_weight > 0:
        normalized = [{"topic": t, "weightage": w / total_weight} for t, w in topic_weights.items()]
    else:
        normalized = []

    normalized.sort(key=lambda x: x["weightage"], reverse=True)

    return SyllabusPayload(
        course_title=first.get("course_title", "Unknown"),
        total_units=first.get("total_units", len(sorted_units)),
        learning_path=sorted_units,
        priority_topics=normalized,
    )


def process_syllabus(chunks: list[str]) -> SyllabusPayload:
    results = execute_chunks(chunks, task="syllabus")
    return merge_syllabus_results(results)
