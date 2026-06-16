import openai
from fastapi import HTTPException
from pydantic import BaseModel, Field
from settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["system", "user"])
    content: str = Field(..., examples=["You are an academic CV assistant."])


def get_llm_client() -> openai.OpenAI:
    """Initializes and returns an OpenAI client configured for the selected LLM provider."""
    return openai.OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )


def call_llm(messages: list[ChatMessage]) -> str:
    """Calls the configured LLM provider with the given messages and returns the response content."""
    client = get_llm_client()
    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[message.model_dump() for message in messages],
            response_format={"type": "json_object"} 
        )
    except openai.AuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM authentication failed. Check provider and API key configuration.",
        ) from exc

    if not completion.choices:
        raise HTTPException(
            status_code=502, detail="LLM response did not include any choices"
        )

    message = completion.choices[0].message
    if message is None or message.content is None:
        raise HTTPException(
            status_code=502, detail="LLM response did not include message content"
        )

    return message.content
