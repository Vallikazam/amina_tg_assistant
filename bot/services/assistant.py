from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from bot.db import Database, MessageRow


SYSTEM_PROMPT = """
Ты Amina, дружелюбный и практичный AI-ассистент в Telegram.
Отвечай на русском языке, если пользователь не попросил другой язык.
Будь краткой, полезной и структурированной. Если не знаешь ответ, скажи честно.
Не проси и не сохраняй пароли, токены, ключи API, банковские данные и документы.
""".strip()


class AssistantService:
    def __init__(
        self,
        *,
        db: Database,
        api_key: str,
        model: str,
        history_limit: int,
        max_response_chars: int,
    ) -> None:
        self.db = db
        self.model = model
        self.history_limit = history_limit
        self.max_response_chars = max_response_chars
        self.client = genai.Client(api_key=api_key)

    async def answer(self, *, user_id: int, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            return "Напиши вопрос после команды или просто отправь сообщение."

        history = await self.db.get_recent_messages(
            user_id,
            limit=self.history_limit,
        )
        memories = await self.db.list_memories(user_id)

        await self.db.add_message(user_id, "user", prompt)

        try:
            response_text = await asyncio.to_thread(
                self._generate_content,
                history,
                memories,
                prompt,
            )
        except Exception:
            return (
                "Не получилось получить ответ от AI. "
                "Проверь GEMINI_API_KEY или попробуй ещё раз чуть позже."
            )

        response_text = self._limit_response(response_text)
        await self.db.add_message(user_id, "assistant", response_text)
        return response_text

    def _generate_content(
        self,
        history: list[MessageRow],
        memories: list[str],
        prompt: str,
    ) -> str:
        contents = self._build_contents(history, prompt)
        system_instruction = self._build_system_instruction(memories)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=900,
                temperature=0.7,
            ),
        )

        text = getattr(response, "text", None)
        if not text:
            return "AI вернул пустой ответ. Попробуй переформулировать вопрос."
        return str(text).strip()

    def _build_contents(
        self,
        history: list[MessageRow],
        prompt: str,
    ) -> list[types.Content]:
        contents: list[types.Content] = []

        for message in history:
            role = "model" if message.role == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=message.content)],
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            )
        )
        return contents

    def _build_system_instruction(self, memories: list[str]) -> str:
        if not memories:
            return SYSTEM_PROMPT

        memory_block = "\n".join(f"- {memory}" for memory in memories)
        return (
            f"{SYSTEM_PROMPT}\n\n"
            "Личная память пользователя, которую можно учитывать в ответах:\n"
            f"{memory_block}"
        )

    def _limit_response(self, text: str) -> str:
        text = text.strip()
        if len(text) <= self.max_response_chars:
            return text
        return text[: self.max_response_chars - 20].rstrip() + "\n\n[Ответ сокращён]"

