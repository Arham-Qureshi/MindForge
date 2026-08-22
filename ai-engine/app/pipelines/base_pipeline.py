import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.pipelines.llm_client import llm_client


def _deduplicate(items: list[dict], key: str = "question") -> list[dict]:
    seen = {}
    for item in items:
        k = item.get(key, str(item))
        if k not in seen:
            seen[k] = item
    return list(seen.values())


def execute_chunks(
    chunks: list[str],
    task: str,
    max_workers: int = 5,
) -> list[dict]:
    def process_one(chunk_text: str) -> dict:
        raw = llm_client.complete(task=task, user=chunk_text)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(process_one, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            results.append(future.result())

    return results
