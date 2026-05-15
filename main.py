import uvicorn
from fastapi import FastAPI, UploadFile
from loguru import logger
from pdf_extractor import extract_text
from llm_service import call_llm, ChatMessage

app = FastAPI(
    title="Academic CV Generator API",
    version="0.1.0",
    description="Builds a starter academic CV from Wikidata and simple user preferences.",
)

logger.info("Initializing Graphrag GenCV API...")


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile):
    return await extract_text(file)


@app.post("/chat")
async def chat(system_instruction: str, user_prompt: str) -> str:
    messages = [
        ChatMessage(role="system", content=system_instruction),
        ChatMessage(role="user", content=user_prompt),
    ]
    return await call_llm(messages)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
