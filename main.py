import os
import subprocess
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from loguru import logger
from pydantic import BaseModel

from cv_to_rdf import CandidateProfile, generate_rdf_and_vectors, map_cv_to_rdf
from designs.texDesign import generateDesign1, generateDesign2, generateDesign3
from generate_cv import generate_tailored_cv
from hybrid_search import hybrid_search
from llm_service import ChatMessage, call_llm
from pdf_extractor import extract_text
from pdf_service import generate_and_save_pdf
from query_graph import get_candidate_profile

app = FastAPI(
    title="Graphrag CV Generator API",
    version="0.1.0",
    description="Builds a CV.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def cv_to_rdf(file: UploadFile) -> dict:
    """Endpoint to convert a Markdown CV into RDF Turtle format using the LLM."""
    try:
        logger.info(f"Extracting text from file: {file.filename}")
        extraction_result = await extract_text(file)
        cv_markdown = extraction_result["text"]
        logger.info(f"Extracted CV text: {cv_markdown}")
        logger.info("Using LLM to map CV to RDF...")
        result = await map_cv_to_rdf(cv_markdown)
        logger.info(f"Generated RDF: {result}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error occurred while converting CV to RDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GraphragCVRequest(BaseModel):
    candidate_name: str
    job_description: str
    design_choice: int = 1

@app.post("/generate-graphrag-cv")
def generate_graphrag_cv(request: GraphragCVRequest) -> str:
    """Generates a CV using the Graphrag pipeline: GraphDB + LLM."""
    final_cv = generate_tailored_cv(request.job_description, request.candidate_name, design_choice=request.design_choice)

    return final_cv


class CVRequest(BaseModel):
    candidate_name: str
    job_description: str


@app.post("/generate-hybrid-cv")
def generate_hybrid_cv(request: CVRequest) -> str:
    """The core thesis pipeline: Vector Recall -> Graph Precision -> LLM Generation."""

    logger.info(f"Running hybrid search for {request.candidate_name}...")
    profile_data = hybrid_search(request.job_description, request.candidate_name)

    if "message" in profile_data:
        raise HTTPException(status_code=404, detail=profile_data["message"])

    logger.info("Generating tailored CV via LLM...")
    final_cv = generate_tailored_cv(request.job_description, profile_data)

    return final_cv


@app.post("/ingest-structured-profile")
async def ingest_structured_profile(profile: CandidateProfile):
    """Bypasses the LLM and ingests a perfectly structured profile directly."""
    logger.info(f"Received manual profile entry for {profile.name}")
    try:
        rdf_output = await generate_rdf_and_vectors(profile)
        logger.info(rdf_output)

        return {
            "status": "success",
            "message": f"Successfully saved {profile.name} to GraphDB and ChromaDB.",
        }
    except Exception as e:
        logger.error(f"Manual ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download-pdf/{design_id}")
async def download_pdf(design_id: int, profile: CandidateProfile):
    pdf_path = generate_and_save_pdf(profile, design_id)
    return FileResponse(pdf_path, media_type="application/pdf", filename="cv.pdf")


class LatexRequest(BaseModel):
    latex: str


def cleanup_files(*filenames):
    """Helper function to delete temporary files."""
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)


@app.post("/compile-latex")
async def compile_latex(request_data: LatexRequest, background_tasks: BackgroundTasks):
    """Compiles LaTeX code into a PDF and returns the PDF file"""
    unique_id = str(uuid.uuid4())
    tex_filename = f"cv_{unique_id}.tex"
    pdf_filename = f"cv_{unique_id}.pdf"

    try:
        with open(tex_filename, "w", encoding="utf-8") as f:
            f.write(request_data.latex)

        subprocess.run(["tectonic", "-Z", "shell-escape", tex_filename], check=True)

        if not os.path.exists(pdf_filename):
            raise FileNotFoundError("PDF was not generated.")

        background_tasks.add_task(cleanup_files, tex_filename, pdf_filename)

        return FileResponse(
            pdf_filename, media_type="application/pdf", filename="cv.pdf"
        )

    except subprocess.CalledProcessError:
        cleanup_files(tex_filename)
        raise HTTPException(
            status_code=500, detail="LaTeX compilation failed. Check LaTeX syntax."
        )
    except Exception as e:
        cleanup_files(tex_filename, pdf_filename)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-latex/{design_id}", response_class=PlainTextResponse)
async def generate_latex(
    design_id: int, profile: CandidateProfile, language: str = "en"
):
    try:
        if design_id == 1:
            latex_code = generateDesign1(profile, language)
        elif design_id == 2:
            latex_code = generateDesign2(profile, language)
        else:
            latex_code = generateDesign3(profile, language)

        return latex_code
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-candidates")
async def list_candidates():
    """Returns a list of all candidate names from the database."""
    # TODO: implement actual logic
    return ["Kenneth Plum Toft", "Jane Doe"]


@app.get("/get-profile/{candidate_name}")
async def get_profile(candidate_name: str):
    """Retrieves a full candidate profile from the database."""
    profile_data = get_candidate_profile(candidate_name)
    logger.info(f"Retrieved profile for {candidate_name}: {profile_data}")
    return profile_data


@app.get("/get-profile-test/{candidate_name}")
async def get_profile_test(candidate_name: str):
    """Retrieves a full candidate profile from the database."""
    return {
        "name": candidate_name,
        "city": "Copenhagen",
        "country": "Denmark",
        "technical_skills": [{"name": "Python"}, {"name": "GraphRAG"}],
        "languages": [{"name": "English", "proficiency": "Fluent"}],
        "experiences": [
            {
                "company_name": "Dictus ApS",
                "job_title": "Software Developer",
                "start_date": "2024",
                "end_date": "2026",
                "raw_skills": "Python, ASR",
                "description": "Developed ASR system.",
            }
        ],
        "education": [
            {
                "degree": "MSc Computer Science",
                "institution": "DTU",
                "start_date": "2024",
                "end_date": "2026",
                "field_of_study": "AI",
                "description": "Specializing in AI and Algorithms.",
            }
        ],
        "publications": [],
        "websites": [],
        "honors": [],
        "references": [],
    }
