import uvicorn
from fastapi import FastAPI, UploadFile
from loguru import logger
from pdf_extractor import extract_text
from llm_service import call_llm, ChatMessage
from cv_to_rdf import map_cv_to_rdf

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
def chat(system_instruction: str, user_prompt: str) -> str:
    messages = [
        ChatMessage(role="system", content=system_instruction),
        ChatMessage(role="user", content=user_prompt),
    ]
    return call_llm(messages)

@app.post("/cv-to-rdf")
async def cv_to_rdf(file: UploadFile) -> str:
    """Endpoint to convert a Markdown CV into RDF Turtle format using the LLM."""

    cv_markdown = await extract_text(file)
    result = map_cv_to_rdf(cv_markdown)
    logger.info(result)
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
