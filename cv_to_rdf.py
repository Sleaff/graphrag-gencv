from pydantic import BaseModel, Field
from typing import List, Optional
from generate_rdf import create_rdf_graph, upload_to_graphdb
from llm_service import call_llm, ChatMessage
from vector_service import generate_and_store_embedding
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
    raw_skills: List[str]
    description: str = Field(description="Narrative description of responsibilities and achievements.")

class Education(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str
    field_of_study: str
    description: str = Field(description="Description of coursework, thesis, or projects.")

class Language(BaseModel):
    name: str
    proficiency: str

class Target(BaseModel):
    job_title: str = Field(description="The job title the candidate is seeking.")
    job_mode: Optional[str] = Field(description="e.g., Full-time, Part-time.")
    relocate: Optional[bool] = Field(description="Is the candidate willing to relocate?")
    travel: Optional[bool] = Field(description="Is the candidate willing to travel?")

class Address(BaseModel):
    city: str
    country: str

class Website(BaseModel):
    url: str
    website_type: str

class HonorAward(BaseModel):
    title: str
    issuer: str
    date: str

class Publication(BaseModel):
    title: str
    publisher: str
    date: str
    description: str = Field(description="Abstract or summary of the publication.")

class Reference(BaseModel):
    name: str
    relation: str  # e.g., "Professional" or "Personal"
    description: str = "Available upon request" # Defaulting for privacy

class CandidateProfile(BaseModel):
    name: str
    experiences: List[Job]
    education: List[Education]
    technical_skills: List[str]
    languages: List[Language]
    target: Target
    address: Address
    websites: List[Website]
    honors: List[HonorAward]
    publications: List[Publication]
    references: List[Reference]

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
    "experiences": [{"company_name": "...", "job_title": "...", "start_date": "...", "end_date": "...", "raw_skills": ["..."], "description": "..."}],
    "education": [{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "field_of_study": "...", "description": "..."}],
    "technical_skills": ["skill1", "skill2"],
    "languages": [{"name": "...", "proficiency": "..."}],
    "target": {"job_title": "...", "job_mode": "...", "relocate": true, "travel": true},
    "address": {"city": "...", "country": "..."},
    "websites": [{"url": "...", "website_type": "..."}],
    "honors": [{"title": "...", "issuer": "...", "date": "..."}],
    "publications": [{"title": "...", "publisher": "...", "date": "...", "description": "..."}],
    "references": [{"name": "...", "relation": "..."}]
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
    candidate_slug = candidate_data.name.replace(" ", "_").lower()
    data_dict = {
        "name": candidate_data.name,
        "experiences": [],
        "education": [],
        "publications": [],
        "technical_skills": candidate_data.technical_skills,
        "languages": [l.model_dump() for l in candidate_data.languages],
        "target": candidate_data.target.model_dump(),
        "address": candidate_data.address.model_dump() if candidate_data.address else None,
        "websites": [w.model_dump() for w in candidate_data.websites],
        "honors": [h.model_dump() for h in candidate_data.honors],
        "references": [r.model_dump() for r in candidate_data.references]
    }

    # --- VECTOR & ESCO MAPPING FOR JOBS ---
    for idx, job in enumerate(candidate_data.experiences):
        esco_uris = [map_to_esco_uri(s) for s in job.raw_skills if map_to_esco_uri(s)]
        vector_id = generate_and_store_embedding(candidate_slug, f"job_{idx}", job.description)
        
        job_dict = job.model_dump()
        job_dict["esco_skill_uris"] = esco_uris
        job_dict["vector_id"] = vector_id
        data_dict["experiences"].append(job_dict)

    # --- VECTOR MAPPING FOR EDUCATION ---
    for idx, edu in enumerate(candidate_data.education):
        vector_id = generate_and_store_embedding(candidate_slug, f"edu_{idx}", edu.description)
        edu_dict = edu.model_dump()
        edu_dict["vector_id"] = vector_id
        data_dict["education"].append(edu_dict)
        
    # --- VECTOR MAPPING FOR PUBLICATIONS ---
    for idx, pub in enumerate(candidate_data.publications):
        vector_id = generate_and_store_embedding(candidate_slug, f"pub_{idx}", pub.description)
        pub_dict = pub.model_dump()
        pub_dict["vector_id"] = vector_id
        data_dict["publications"].append(pub_dict)

    # Generate and Upload!
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    
    return graph.serialize(format="turtle")

async def generate_rdf_and_vectors(candidate_data: CandidateProfile) -> str:
    """Takes a strictly structured Pydantic model and inserts it into ChromaDB and GraphDB."""
    
    candidate_slug = candidate_data.name.replace(" ", "_").lower()
    
    data_dict = {
        "name": candidate_data.name,
        "experiences": [],
        "education": [],
        "publications": [],
        "technical_skills": candidate_data.technical_skills,
        "languages": [l.model_dump() for l in candidate_data.languages],
        "target": candidate_data.target.model_dump(),
        "address": candidate_data.address.model_dump() if candidate_data.address else None,
        "websites": [w.model_dump() for w in candidate_data.websites],
        "honors": [h.model_dump() for h in candidate_data.honors],
        "references": [r.model_dump() for r in candidate_data.references]
    }

    # --- VECTOR & ESCO MAPPING FOR JOBS ---
    for idx, job in enumerate(candidate_data.experiences):
        esco_uris = [map_to_esco_uri(s) for s in job.raw_skills if map_to_esco_uri(s)]
        vector_id = generate_and_store_embedding(candidate_slug, f"job_{idx}", job.description)
        
        job_dict = job.model_dump()
        job_dict["esco_skill_uris"] = esco_uris
        job_dict["vector_id"] = vector_id
        data_dict["experiences"].append(job_dict)

    # --- VECTOR MAPPING FOR EDUCATION ---
    for idx, edu in enumerate(candidate_data.education):
        vector_id = generate_and_store_embedding(candidate_slug, f"edu_{idx}", edu.description)
        edu_dict = edu.model_dump()
        edu_dict["vector_id"] = vector_id
        data_dict["education"].append(edu_dict)
        
    # --- VECTOR MAPPING FOR PUBLICATIONS ---
    for idx, pub in enumerate(candidate_data.publications):
        vector_id = generate_and_store_embedding(candidate_slug, f"pub_{idx}", pub.description)
        pub_dict = pub.model_dump()
        pub_dict["vector_id"] = vector_id
        data_dict["publications"].append(pub_dict)

    # Generate and Upload!
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    
    return graph.serialize(format="turtle")