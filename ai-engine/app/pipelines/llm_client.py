from groq import Groq
from google import genai
from google.genai import types
from app.core.config import settings
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS, INJECTION_GUARD

PROVIDER_ROUTES = {
    "pyq": "gemini",
}


class LLMClient:
    def __init__(self):
        self._groq = Groq(api_key=settings.GROQ_API_KEY)
        self._gemini = genai.Client(api_key=settings.GEMINI_API_KEY)

    def complete(self, task: str, user: str, model: str = None, json_mode: bool = False) -> str:
        system_template = SYSTEM_PROMPTS[task]
        task_desc = TASK_DESCRIPTIONS.get(task, "")

        full_system = system_template.format(
            task_description=task_desc,
            injection_guard=INJECTION_GUARD,
        )

        provider = PROVIDER_ROUTES.get(task, "groq")

        if provider == "gemini":
            return self._complete_gemini(full_system, user, json_mode)

        return self._complete_groq(full_system, user, model, json_mode)

    def _complete_groq(self, system: str, user: str, model: str = None, json_mode: bool = False) -> str:
        kwargs = {
            "model": model or settings.DEFAULT_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"<user_document_content>\n{user}\n</user_document_content>"},
            ],
            "temperature": 0.5,
            "max_tokens": 8192,
            "reasoning_effort": "low",
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._groq.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _complete_gemini(self, system: str, user: str, json_mode: bool = False) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.5,
            max_output_tokens=8192,
            response_mime_type="application/json" if json_mode else None,
        )

        response = self._gemini.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user,
            config=config,
        )
        return response.text


llm_client = LLMClient()
