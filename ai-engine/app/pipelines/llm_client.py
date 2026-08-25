from dataclasses import dataclass

from groq import Groq
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

import groq as groq_sdk

from app.core.config import settings
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS, INJECTION_GUARD
from app.pipelines.tokens import count_tokens

PROVIDER_ROUTES = {
    "pyq": "gemini",
}

# output reserves sized so input + reserve stays under Groq free-tier 8K TPM
MAX_OUTPUT_TOKENS = {
    "syllabus": 2500,
    "notes": 3000,
    "pyq": 3000,
}
DEFAULT_OUTPUT_RESERVE = 2000


@dataclass
class LLMResult:
    content: str
    total_tokens: int


class LLMError(Exception):
    def __init__(
        self,
        status: int,
        message: str,
        provider: str,
        retryable: bool,
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.message = message
        self.provider = provider
        self.retryable = retryable
        self.retry_after = retry_after


def _retry_after_from_headers(headers) -> float | None:
    if not headers:
        return None
    try:
        raw = headers.get("retry-after")
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _is_transient_4xx(err) -> bool:
    # json_validate_failed is the model fumbling formatting — a retry usually fixes it.
    # Real 4xx (bad key, bad request shape) stay fatal.
    try:
        body = err.body or err.response.json()
        return body.get("error", {}).get("code") == "json_validate_failed"
    except Exception:
        return False


class LLMClient:
    def __init__(self):
        self._groq = Groq(api_key=settings.GROQ_API_KEY)
        self._gemini = genai.Client(api_key=settings.GEMINI_API_KEY)

    def estimate_request_tokens(self, task: str, user: str) -> int:
        system = SYSTEM_PROMPTS[task].format(
            task_description=TASK_DESCRIPTIONS.get(task, ""),
            injection_guard=INJECTION_GUARD,
        )
        reserve = MAX_OUTPUT_TOKENS.get(task, DEFAULT_OUTPUT_RESERVE)
        return count_tokens(system) + count_tokens(f"<user_document_content>\n{user}\n</user_document_content>") + reserve + 50

    def complete(self, task: str, user: str, model: str = None, json_mode: bool = False) -> LLMResult:
        system_template = SYSTEM_PROMPTS[task]
        task_desc = TASK_DESCRIPTIONS.get(task, "")

        full_system = system_template.format(
            task_description=task_desc,
            injection_guard=INJECTION_GUARD,
        )
        reserve = MAX_OUTPUT_TOKENS.get(task, DEFAULT_OUTPUT_RESERVE)

        provider = PROVIDER_ROUTES.get(task, "groq")
        if provider == "gemini":
            return self._complete_gemini(full_system, user, json_mode, reserve)
        return self._complete_groq(full_system, user, model, json_mode, reserve)

    def _complete_groq(self, system: str, user: str, model: str, json_mode: bool, reserve: int) -> LLMResult:
        kwargs = {
            "model": model or settings.DEFAULT_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"<user_document_content>\n{user}\n</user_document_content>"},
            ],
            "temperature": 0.5,
            "max_tokens": reserve,
            "reasoning_effort": "low",
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self._groq.chat.completions.create(**kwargs)
        except groq_sdk.RateLimitError as e:
            raise LLMError(
                429,
                str(e),
                "groq",
                retryable=True,
                retry_after=_retry_after_from_headers(getattr(e.response, "headers", None)),
            )
        except groq_sdk.APIStatusError as e:
            status = getattr(e, "status_code", 500)
            raise LLMError(status, str(e), "groq", retryable=status >= 500 or _is_transient_4xx(e))

        usage = getattr(response.usage, "total_tokens", 0) or 0
        return LLMResult(content=response.choices[0].message.content, total_tokens=usage)

    def _complete_gemini(self, system: str, user: str, json_mode: bool, reserve: int) -> LLMResult:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.5,
            max_output_tokens=reserve,
            response_mime_type="application/json" if json_mode else None,
        )

        try:
            response = self._gemini.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user,
                config=config,
            )
        except genai_errors.ClientError as e:
            if e.code == 429:
                raise LLMError(429, str(e), "gemini", retryable=True, retry_after=30.0)
            raise LLMError(e.code, str(e), "gemini", retryable=False)
        except genai_errors.ServerError as e:
            raise LLMError(e.code, str(e), "gemini", retryable=True, retry_after=10.0)

        usage = getattr(response.usage_metadata, "total_token_count", 0) or 0
        return LLMResult(content=response.text, total_tokens=usage)


llm_client = LLMClient()
