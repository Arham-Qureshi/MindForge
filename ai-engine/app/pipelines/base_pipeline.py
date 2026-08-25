import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel
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
    schema: type[BaseModel] | None = None,
    max_workers: int = 5,
    max_retries: int = 3,
) -> list[dict]:
    def process_one(chunk_text: str) -> dict:
        for attempt in range(max_retries):
            try:
                raw = llm_client.complete(task=task, user=chunk_text, json_mode=True)
                data = json.loads(raw.content)
                if schema:
                    validated = schema.model_validate(data)
                    return validated.model_dump()
                return data
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return {}

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(process_one, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            results.append(future.result())

    return [r for r in results if r]
