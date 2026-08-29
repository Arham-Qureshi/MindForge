SYLLABUS_PATTERNS = [
    r"\bmodule\s*[0-9ivx]+\b",
    r"\bcourse\s*outcomes?\b",
    r"\bgrading\b",
    r"\bprerequisites?\b",
    r"\bcredits?\b",
    r"\bunit\s*[0-9ivx]+\b",
    r"\bsyllabus\b",
    r"\bcurriculum\b",
]

PYQ_PATTERNS = [
    r"\bq\.?\s*[0-9]+\b",
    r"\bquestion\s*[0-9]+\b",
    r"\[[0-9]+\s*marks?\]",
    r"\btime:\s*[0-9]+\s*hours?\b",
    r"\battempt\s+any\b",
    r"\bsection\s+[a-c]\b",
    r"\bprevious\s+year\b",
    r"\bexam\b",
]

NOTES_PATTERNS = [
    r"\bdefinition\b",
    r"\boverview\b",
    r"\bfor\s+example\b",
    r"\btherefore\b",
    r"\bin\s+summary\b",
    r"\bnote[s]?\b",
    r"\bchapter\b",
    r"\btopic\b",
    # expanded — generic academic notes language (biology, etc.)
    r"\bintroduction\b",
    r"\bconcept\b",
    r"\btheory\b",
    r"\bimportant\b",
    r"\bkey\s+concept\b",
    r"\bprocess\b",
    r"\bfunction\b",
    r"\bstructure\b",
    r"\bstudy\b",
    r"\bexplanation\b",
    r"\bdiagram\b",
    r"\bfigure\b",
    r"\bexample\b",
    r"\bconclusion\b",
]
