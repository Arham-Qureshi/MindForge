from app.pipelines.tokens import count_tokens, CHUNK_TOKEN_BUDGET


def test_count_tokens_nonempty():
    assert count_tokens("Hello world, this is a test.") > 3


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_count_tokens_scales_with_length():
    short = count_tokens("word " * 10)
    long = count_tokens("word " * 1000)
    assert long > short * 50


def test_budget_below_groq_tpm():
    assert CHUNK_TOKEN_BUDGET < 8000
