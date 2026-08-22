def calculate_scores(syllabus: int, pyq: int, notes: int) -> dict:
    total = syllabus + pyq + notes

    scores = {
        "SYLLABUS": syllabus,
        "PYQ": pyq,
        "NOTES": notes,
    }

    max_score = max(scores.values())
    candidates = [k for k, v in scores.items() if v == max_score]
    winner = "NOTES" if len(candidates) > 1 else candidates[0]

    confidence = scores[winner] / total if total > 0 else 0.0

    return {
        "winner": winner,
        "confidence": confidence,
        "metrics": {
            "SYLLABUS": {"count": syllabus, "matched_markers": []},
            "PYQ": {"count": pyq, "matched_markers": []},
            "NOTES": {"count": notes, "matched_markers": []},
        },
    }
