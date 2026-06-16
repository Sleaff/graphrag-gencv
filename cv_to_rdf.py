from pydantic import BaseModel, Field
from typing import List, Optional
from generate_rdf import create_rdf_graph, upload_to_graphdb
from llm_service import call_llm, ChatMessage
import json

# --- 1. ESCO Mapping Bridge ---
def map_to_esco_uri(skill_name: str) -> str | None:
    """Temporary mock mapper for ESCO URIs."""
    esco_database = {
        "python": "http://data.europa.eu/esco/skill/ccd0a1d9-afda-43d9-b901-96344886e14d",
        "machine learning": "http://data.europa.eu/esco/skill/3a2d5b45-56e4-4f5a-a55a-4a4a65afdc43",
        "natural language processing": "http://data.europa.eu/esco/skill/fff0e2cd-d0bd-4b02-9daf-158b79d9688a",
        "docker": "http://data.europa.eu/esco/skill/2b7a79e5-84d8-4880-be66-3d9bb05bea17",
        "sparql": "http://data.europa.eu/esco/skill/5da8018b-ae85-4cde-ad93-0394369018f3",
        "fastapi": "http://data.europa.eu/esco/skill/fd33c66c-70c4-40e6-b87c-5495bd3bf26e", # Fallback
        "software developer": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1"
    }
    return esco_database.get(skill_name.lower().strip())

# --- 2. Pydantic Schemas ---
class Job(BaseModel):
    company_name: str = Field(description="Name of the company, e.g., Dictus ApS")
    job_title: str = Field(description="The role, e.g., Software Developer")
    start_date: str
    end_date: Optional[str]
    raw_skills: List[str] = Field(description="Explicit skills, tools, or frameworks mentioned.")

class Education(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str
    field_of_study: str

class Language(BaseModel):
    name: str
    proficiency: str

class CandidateProfile(BaseModel):
    name: str
    experiences: List[Job]
    education: List[Education]
    technical_skills: List[str]
    languages: List[Language]

# --- 3. Main Pipeline ---
async def map_cv_to_rdf(cv_markdown: str) -> str:
    """Passes the entire markdown to the LLM for strict Pydantic extraction."""
    
    messages = [
        ChatMessage(
            role="system", 
            content="""You are an expert HR parser. Extract the full profile data.
Return ONLY a valid JSON object matching this schema:
{
    "name": "full name",
    "experiences": [{"company_name": "...", "job_title": "...", "start_date": "...", "end_date": "...", "raw_skills": ["..."]}],
    "education": [{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "field_of_study": "..."}],
    "technical_skills": ["skill1", "skill2"],
    "languages": [{"name": "...", "proficiency": "..."}]
}"""
        ),
        ChatMessage(role="user", content=cv_markdown),
    ]

    candidate_data_json = call_llm(messages)
    
    try:
        # Safeguard: Strip markdown formatting if the LLM wraps the response
        if "```json" in candidate_data_json:
            candidate_data_json = candidate_data_json.split("```json")[1].split("```")[0].strip()
        elif "```" in candidate_data_json:
            candidate_data_json = candidate_data_json.split("```")[1].split("```")[0].strip()
            
        parsed_data = json.loads(candidate_data_json)
        candidate_data = CandidateProfile(**parsed_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM response was not valid JSON: {candidate_data_json}") from e
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response into CandidateProfile: {e}") from e
    
    # Transform the Pydantic object back into the dictionary format your generate_rdf.py expects
    data_dict = {
        "name": candidate_data.name,
        "experiences": [],
        "education": [e.model_dump() for e in candidate_data.education],
        "technical_skills": candidate_data.technical_skills,
        "languages": [l.model_dump() for l in candidate_data.languages]
    }

    for job in candidate_data.experiences:
        esco_uris = []
        # Pass the extracted raw skills through the mock ESCO database
        for raw_skill in job.raw_skills:
            uri = map_to_esco_uri(raw_skill)
            if uri:
                esco_uris.append(uri)
                
        data_dict["experiences"].append({
            "company_name": job.company_name,
            "job_title": job.job_title,
            "start_date": job.start_date,
            "end_date": job.end_date if job.end_date else "",
            "esco_skill_uris": esco_uris # Mapped ESCO URIs
        })

    # Generate and Upload!
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    
    return graph.serialize(format="turtle")