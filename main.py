import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from loguru import logger
from hybrid_search import hybrid_search
from pdf_extractor import extract_text
from llm_service import call_llm, ChatMessage
from cv_to_rdf import map_cv_to_rdf
from generate_cv import generate_tailored_cv

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
    extraction_result = await extract_text(file)
    cv_markdown = extraction_result["text"]
    result = await map_cv_to_rdf(cv_markdown)
    logger.info(result)
    return result

@app.post("/generate-graphrag-cv")
def generate_graphrag_cv(candidate_name: str, job_description: str) -> str:
    return generate_graphrag_cv(candidate_name, job_description)

@app.post("/generate-hybrid-cv")
def generate_hybrid_cv(candidate_name: str, job_description: str) -> str:
    """The core thesis pipeline: Vector Recall -> Graph Precision -> LLM Generation"""
    
    # 1. Retrieval Stage (Hybrid Search)
    logger.info(f"Running hybrid search for {candidate_name}...")
    profile_data = hybrid_search(job_description, candidate_name)
    
    if "message" in profile_data: # Indicates no semantic matches were found
        raise HTTPException(status_code=404, detail=profile_data["message"])
        
    # 2. Generation Stage
    logger.info("Generating tailored CV via LLM...")
    final_cv = generate_tailored_cv(job_description, profile_data)
    
    return final_cv

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
