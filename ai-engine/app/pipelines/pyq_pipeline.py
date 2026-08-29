from app.pipelines.base_pipeline import execute_chunks
from app.schemas.pyq_schema import PYQAnalysisPayload
from app.schemas.pyq_paper_schema import BlueprintPayload, BlueprintRow, ExamPaper, ExamPaperSection, ExamPaperQuestion


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


def build_blueprint(topic_frequency: list[dict], total_marks: int = 80) -> BlueprintPayload:
    if not topic_frequency:
        return BlueprintPayload(total_marks=total_marks, rows=[])
    # marks = round(percentage * total_marks), adjust last to sum 80
    rows: list[BlueprintRow] = []
    running = 0
    for i, tf in enumerate(topic_frequency):
        is_last = i == len(topic_frequency) - 1
        marks = round(tf["percentage"] * total_marks) if not is_last else total_marks - running
        # bloom breakdown placeholder — will be refined by predicted_questions distribution
        rows.append(
            BlueprintRow(
                topic=tf["topic"],
                percentage=tf["percentage"],
                question_count=tf["question_count"],
                marks=max(1, marks),
                bloom_breakdown={"Apply": 0, "Analyze": 0, "Evaluate": 0},
            )
        )
        running += rows[-1].marks
    # if rounding overshoot, adjust
    if rows and sum(r.marks for r in rows) != total_marks:
        rows[-1].marks += total_marks - sum(r.marks for r in rows)
    return BlueprintPayload(total_marks=total_marks, rows=rows)


def build_exam_paper(
    topic_frequency: list[dict],
    predicted_questions: list[dict],
    blueprint: BlueprintPayload | None = None,
    title: str = "Predicted Question Paper",
) -> ExamPaper:
    # take top 10 HOT questions sorted by probability, split 5+5
    sorted_qs = sorted(predicted_questions, key=lambda x: x.get("probability_score", 0), reverse=True)[:10]
    # pad if less than 10
    while len(sorted_qs) < 10:
        sorted_qs.append(
            {"question": f"Sample question {len(sorted_qs)+1} on {topic_frequency[0]['topic'] if topic_frequency else 'General'}", "bloom_level": "Apply", "expected_marks": 8, "probability_score": 0.5, "topic": topic_frequency[0]["topic"] if topic_frequency else "General"}
        )
    sections: list[ExamPaperSection] = []
    for sec_idx, sec_name in enumerate(["Section A", "Section B"]):
        sec_qs = sorted_qs[sec_idx * 5 : (sec_idx + 1) * 5]
        q_objs = []
        for j, q in enumerate(sec_qs):
            q_objs.append(
                ExamPaperQuestion(
                    q_no=j + 1 + sec_idx * 5,
                    question=q["question"],
                    topic=q.get("topic", topic_frequency[0]["topic"] if topic_frequency else "General"),
                    bloom_level=q.get("bloom_level", "Apply"),  # type: ignore
                    expected_marks=q.get("expected_marks", 8),
                    probability_score=q.get("probability_score", 0.5),
                )
            )
        sections.append(
            ExamPaperSection(
                name=sec_name,
                instructions="Attempt any 3 of 5" if sec_idx == 0 else "Attempt any 2 of 5",
                questions=q_objs,
            )
        )
    return ExamPaper(
        title=title,
        time="3 Hours",
        max_marks=80,
        instructions="Attempt any 5 of 8 questions. Q1 and Q2 are compulsory.",
        sections=sections,
    )


def process_pyq(chunks: list[str]) -> PYQAnalysisPayload:
    results = execute_chunks(chunks, task="pyq")
    return merge_pyq_results(results)
