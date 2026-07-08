import openai
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from settings import EMBEDDING_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


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
            response_format={"type": "json_object"},
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


def call_embedding(text: str) -> list[float]:
    """Generates embeddings for the given text using the configured LLM provider."""
    client = get_llm_client()
    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding API Error: {str(e)}")
        raise HTTPException(
            status_code=502, detail=f"Embedding generation failed: {str(e)}"
        ) from e


def create_baseline_cv_llm(profile: dict, job_description: str) -> str:
    """Generates a baseline CV in Markdown format using the LLM based on the candidate profile and job description."""
    system_prompt = (
        "You are an expert CV generator. You are provided with a candidate's profile "
        "and a job description. Generate a concise, professional CV in Markdown format "
        "tailored to the job description. Highlight relevant skills and experiences."
    )
    user_prompt = (
        f"Candidate Profile:\n{profile}\n\nJob Description:\n{job_description}"
    )

    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt),
    ]

    return call_llm(messages)
