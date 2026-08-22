from groq import Groq
from app.core.config import settings
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS, INJECTION_GUARD


class LLMClient:
    def __init__(self):
        self._groq = Groq(api_key=settings.GROQ_API_KEY)

    def complete(self, task: str, user: str, model: str = None) -> str:
        system_template = SYSTEM_PROMPTS[task]
        task_desc = TASK_DESCRIPTIONS.get(task, "")

        full_system = system_template.format(
            task_description=task_desc,
            injection_guard=INJECTION_GUARD,
        )

        response = self._groq.chat.completions.create(
            model=model or settings.DEFAULT_LLM_MODEL,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": f"<user_document_content>\n{user}\n</user_document_content>"},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content


llm_client = LLMClient()
