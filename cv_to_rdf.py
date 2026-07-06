from pydantic import BaseModel, Field
from typing import List, Optional
from generate_rdf import create_rdf_graph, upload_to_graphdb
from llm_service import call_llm, ChatMessage
from vector_service import generate_and_store_embedding
import json

def map_to_esco_uri(skill_name: str) -> str | None:
    esco_database = {
        "python": "http://data.europa.eu/esco/skill/ccd0a1d9-afda-43d9-b901-96344886e14d",
        "machine learning": "http://data.europa.eu/esco/skill/3a2d5b45-56e4-4f5a-a55a-4a4a65afdc43",
        "natural language processing": "http://data.europa.eu/esco/skill/fff0e2cd-d0bd-4b02-9daf-158b79d9688a",
        "docker": "http://data.europa.eu/esco/skill/2b7a79e5-84d8-4880-be66-3d9bb05bea17",
        "sparql": "http://data.europa.eu/esco/skill/5da8018b-ae85-4cde-ad93-0394369018f3",
        "fastapi": "http://data.europa.eu/esco/skill/fd33c66c-70c4-40e6-b87c-5495bd3bf26e",
        "software developer": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1"
    }
    return esco_database.get(skill_name.lower().strip())

class Address(BaseModel):
    city: str 
    country: str 
    street: Optional[str] = None
    postal_code: Optional[str] = None 

class Job(BaseModel):
    company: str 
    title: str 
    start: str 
    end: Optional[str] = None 
    description: Optional[str] = None 
    is_current: bool = False 
    career_level: Optional[str] = None
    job_type: Optional[str] = None
    raw_skills: List[str] = Field(default_factory=list)

class Education(BaseModel):
    degree: str 
    institution: str 
    start_date: str 
    end_date: str 
    field_of_study: Optional[str] = None 
    description: Optional[str] = None 

class Course(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    start_date: Optional[str] = None
    finish_date: Optional[str] = None
    has_certification: bool = False
    organized_by: Optional[str] = None

class Patent(BaseModel):
    title: str
    office: Optional[str] = None
    number: Optional[str] = None
    inventor: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    issued_date: Optional[str] = None
    status: Optional[str] = None

class Project(BaseModel):
    name: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    creator: Optional[str] = None
    is_current: bool = False

class Language(BaseModel):
    name: str
    proficiency: Optional[str] = None

class Target(BaseModel):
    job_title: str 
    job_mode: Optional[str] = None 
    relocate: Optional[bool] = None 
    travel: Optional[bool] = None 

class Website(BaseModel):
    url: str 
    website_type: Optional[str] = None

class InstantMessaging(BaseModel):
    name: str
    username: str

class Reference(BaseModel):
    name: str 
    relation: Optional[str] = None

class HonorAward(BaseModel):
    title: str 
    issuer: Optional[str] = None
    date: Optional[str] = None

class Publication(BaseModel):
    title: str 
    publisher: Optional[str] = None
    date: Optional[str] = None

class OtherInfo(BaseModel):
    type: str
    description: str

class CandidateProfile(BaseModel):
    name: str 
    gender: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    drivers_licence: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    phone_mobile: Optional[str] = None
    phone_home: Optional[str] = None
    phone_work: Optional[str] = None
    
    jobs: List[Job] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    courses: List[Course] = Field(default_factory=list)
    patents: List[Patent] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    target: Optional[Target] = None
    address: Optional[Address] = None
    websites: List[Website] = Field(default_factory=list)
    instant_messaging: List[InstantMessaging] = Field(default_factory=list)
    honors: List[HonorAward] = Field(default_factory=list) 
    publications: List[Publication] = Field(default_factory=list) 
    references: List[Reference] = Field(default_factory=list)
    other_info: List[OtherInfo] = Field(default_factory=list)

    class Config:
        populate_by_name = True

async def map_cv_to_rdf(cv_markdown: str) -> str:
    messages = [
        ChatMessage(
            role="system", 
            content="""You are an expert HR parser. Extract the full profile data perfectly aligning with the schema.
IMPORTANT: For the job 'description', ONLY extract the description of the main activities and responsibilities. Do NOT include descriptions of the company itself.
Return ONLY a valid JSON object matching this schema exactly:
{
    "name": "full name", "gender": "...", "nationality": "...", "date_of_birth": "...", "drivers_licence": "...", "short_description": "...", "long_description": "...",
    "phone_mobile": "...", "phone_home": "...", "phone_work": "...",
    "jobs": [{"company": "...", "title": "...", "start": "...", "end": "...", "career_level": "...", "job_type": "...", "raw_skills": ["..."], "description": "...", "is_current": false}],
    "education": [{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "field_of_study": "...", "description": "..."}],
    "courses": [{"title": "...", "description": "...", "url": "...", "start_date": "...", "finish_date": "...", "has_certification": true, "organized_by": "..."}],
    "patents": [{"title": "...", "office": "...", "number": "...", "inventor": "...", "url": "...", "description": "...", "issued_date": "...", "status": "..."}],
    "projects": [{"name": "...", "role": "...", "start_date": "...", "end_date": "...", "description": "...", "url": "...", "creator": "...", "is_current": false}],
    "technical_skills": ["skill1", "skill2"],
    "languages": [{"name": "...", "proficiency": "..."}],
    "target": {"job_title": "...", "job_mode": "...", "relocate": true, "travel": true},
    "address": {"city": "...", "country": "...", "street": "...", "postal_code": "..."},
    "websites": [{"url": "...", "website_type": "..."}],
    "instant_messaging": [{"name": "...", "username": "..."}],
    "honors": [{"title": "...", "issuer": "...", "date": "..."}],
    "publications": [{"title": "...", "publisher": "...", "date": "...", "description": "..."}],
    "references": [{"name": "...", "relation": "..."}],
    "other_info": [{"type": "...", "description": "..."}]
}"""
        ),
        ChatMessage(role="user", content=cv_markdown),
    ]

    candidate_data_json = call_llm(messages)
    
    try:
        if "```json" in candidate_data_json:
            candidate_data_json = candidate_data_json.split("```json")[1].split("```")[0].strip()
        elif "```" in candidate_data_json:
            candidate_data_json = candidate_data_json.split("```")[1].split("```")[0].strip()
            
        parsed_data = json.loads(candidate_data_json)
        candidate_data = CandidateProfile(**parsed_data)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}") from e
    
    candidate_slug = candidate_data.name.replace(" ", "_").lower()
    data_dict = candidate_data.model_dump()

    # Generate Embeddings for textual components
    for idx, job in enumerate(data_dict["jobs"]):
        job["esco_skill_uris"] = [map_to_esco_uri(s) for s in job.get("raw_skills", []) if map_to_esco_uri(s)]
        job["vector_id"] = generate_and_store_embedding(candidate_slug, f"job_{idx}", job.get("description", ""))

    for idx, edu in enumerate(data_dict["education"]):
        edu["vector_id"] = generate_and_store_embedding(candidate_slug, f"edu_{idx}", edu.get("description", ""))

    for idx, proj in enumerate(data_dict["projects"]):
        proj["vector_id"] = generate_and_store_embedding(candidate_slug, f"proj_{idx}", proj.get("description", ""))
        
    for idx, pub in enumerate(data_dict["publications"]):
        pub["vector_id"] = generate_and_store_embedding(candidate_slug, f"pub_{idx}", pub.get("description", "") or pub.get("title", ""))

    for idx, crs in enumerate(data_dict["courses"]):
        crs["vector_id"] = generate_and_store_embedding(candidate_slug, f"course_{idx}", crs.get("description", "") or crs.get("title", ""))

    for idx, pat in enumerate(data_dict["patents"]):
        pat["vector_id"] = generate_and_store_embedding(candidate_slug, f"patent_{idx}", pat.get("description", "") or pat.get("title", ""))

    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    return graph.serialize(format="turtle")


async def generate_rdf_and_vectors(candidate_data: CandidateProfile) -> str:
    """Takes a strictly structured Pydantic model and inserts it into ChromaDB and GraphDB."""
    candidate_slug = candidate_data.name.replace(" ", "_").lower()
    data_dict = candidate_data.model_dump()

    # --- VECTOR & ESCO MAPPING FOR JOBS ---
    for idx, job in enumerate(data_dict["jobs"]):
        job["esco_skill_uris"] = [map_to_esco_uri(s) for s in job.get("raw_skills", []) if map_to_esco_uri(s)]
        job["vector_id"] = generate_and_store_embedding(candidate_slug, f"job_{idx}", job.get("description", ""))

    # --- VECTOR MAPPING FOR EDUCATION ---
    for idx, edu in enumerate(data_dict["education"]):
        edu["vector_id"] = generate_and_store_embedding(candidate_slug, f"edu_{idx}", edu.get("description", ""))

    # --- VECTOR MAPPING FOR PROJECTS ---
    for idx, proj in enumerate(data_dict["projects"]):
        proj["vector_id"] = generate_and_store_embedding(candidate_slug, f"proj_{idx}", proj.get("description", ""))
        
    # --- VECTOR MAPPING FOR PUBLICATIONS ---
    for idx, pub in enumerate(data_dict["publications"]):
        pub["vector_id"] = generate_and_store_embedding(candidate_slug, f"pub_{idx}", pub.get("description", "") or pub.get("title", ""))

    # --- VECTOR MAPPING FOR COURSES ---
    for idx, crs in enumerate(data_dict["courses"]):
        crs["vector_id"] = generate_and_store_embedding(candidate_slug, f"course_{idx}", crs.get("description", "") or crs.get("title", ""))

    # --- VECTOR MAPPING FOR PATENTS ---
    for idx, pat in enumerate(data_dict["patents"]):
        pat["vector_id"] = generate_and_store_embedding(candidate_slug, f"patent_{idx}", pat.get("description", "") or pat.get("title", ""))

    # Generate and Upload!
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    
    return graph.serialize(format="turtle")