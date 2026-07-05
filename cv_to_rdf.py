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

class Address(BaseModel):
    city: str  # alias="city"
    country: str  # alias="country"
    street: Optional[str] = None
    postal_code: Optional[str] = None  # alias="postalCode"

class Job(BaseModel):
    company: str  # alias="organizationName"
    title: str  # alias="jobTitle"
    start: str  # alias="startDate"
    end: Optional[str] = None  # alias="endDate"
    description: Optional[str] = None  # alias="jobDescription"
    is_current: bool = False  # alias="isCurrent"
    raw_skills: List[str] = Field(default_factory=list)

class Education(BaseModel):
    degree: str  # alias="degreeType"
    institution: str 
    start_date: str  # alias="eduStartDate"
    end_date: str  # alias="eduGradDate"
    field_of_study: Optional[str] = None  # alias="eduMajor"
    description: Optional[str] = None  # alias="eduDescription"

class Language(BaseModel):
    name: str
    proficiency: Optional[str] = None

class Target(BaseModel):
    job_title: str  # alias="targetJobTitle"
    job_mode: Optional[str] = None  # alias="targetJobMode"
    relocate: Optional[bool] = None  # alias="targetConditionWillRelocate"
    travel: Optional[bool] = None  # alias="targetConditionWillTravel"

class Website(BaseModel):
    url: str 
    website_type: Optional[str] = None

class Reference(BaseModel):
    name: str  # alias="referenceBy", Ontology points referenceBy to a Person
    relation: Optional[str] = None

# Ontology groups awards/publications into 'OtherInfo'
class HonorAward(BaseModel):
    title: str  # alias="otherInfoDescription"
    issuer: Optional[str] = None
    date: Optional[str] = None

class Publication(BaseModel):
    title: str  # alias="otherInfoDescription"
    publisher: Optional[str] = None
    date: Optional[str] = None

class CandidateProfile(BaseModel):
    name: str 
    jobs: List[Job]  # alias="jobs"
    education: List[Education]  # alias="education"
    technical_skills: List[str]  # alias="skills"
    languages: List[Language]  # alias="languages"
    target: Target  # alias="target"
    address: Address  # alias="address"
    websites: List[Website] = Field(default_factory=list)  # alias="websites"
    honors: List[HonorAward] = Field(default_factory=list)  # alias="honors"
    publications: List[Publication] = Field(default_factory=list)  # alias="publications"
    references: List[Reference] = Field(default_factory=list)  # alias="references"

    class Config:
        populate_by_name = True

# --- 3. Main Pipeline ---
async def map_cv_to_rdf(cv_markdown: str) -> str:
    """Passes the entire markdown to the LLM for strict Pydantic extraction."""
    
    messages = [
        ChatMessage(
            role="system", 
            content="""You are an expert HR parser. Extract the full profile data.
Return ONLY a valid JSON object matching this schema exactly:
{
    "name": "full name",
    "jobs": [{"company": "...", "title": "...", "start": "...", "end": "...", "raw_skills": ["..."], "description": "...", "is_current": false}],
    "education": [{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "field_of_study": "...", "description": "..."}],
    "technical_skills": ["skill1", "skill2"],
    "languages": [{"name": "...", "proficiency": "..."}],
    "target": {"job_title": "...", "job_mode": "...", "relocate": true, "travel": true},
    "address": {"city": "...", "country": "...", "street": "...", "postal_code": "..."},
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
        "jobs": [],
        "education": [],
        "publications": [],
        "technical_skills": candidate_data.technical_skills,
        "languages": [l.model_dump() for l in candidate_data.languages],
        "target": candidate_data.target.model_dump() if candidate_data.target else None,
        "address": candidate_data.address.model_dump() if candidate_data.address else None,
        "websites": [w.model_dump() for w in candidate_data.websites],
        "honors": [h.model_dump() for h in candidate_data.honors],
        "references": [r.model_dump() for r in candidate_data.references]
    }

    # --- VECTOR & ESCO MAPPING FOR JOBS ---
    for idx, job in enumerate(candidate_data.jobs):
        raw_skills = getattr(job, "raw_skills", [])
        esco_uris = [map_to_esco_uri(s) for s in raw_skills if map_to_esco_uri(s)]
        
        desc = getattr(job, "description", "") or ""
        vector_id = generate_and_store_embedding(candidate_slug, f"job_{idx}", desc)
        
        job_dict = job.model_dump()
        job_dict["esco_skill_uris"] = esco_uris
        job_dict["vector_id"] = vector_id
        data_dict["jobs"].append(job_dict)

    # --- VECTOR MAPPING FOR EDUCATION ---
    for idx, edu in enumerate(candidate_data.education):
        desc = getattr(edu, "description", "") or ""
        vector_id = generate_and_store_embedding(candidate_slug, f"edu_{idx}", desc)
        
        edu_dict = edu.model_dump()
        edu_dict["vector_id"] = vector_id
        data_dict["education"].append(edu_dict)
        
    # --- VECTOR MAPPING FOR PUBLICATIONS ---
    for idx, pub in enumerate(candidate_data.publications):
        desc = getattr(pub, "description", "") or getattr(pub, "title", "")
        vector_id = generate_and_store_embedding(candidate_slug, f"pub_{idx}", desc)
        
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
        "jobs": [],
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
    for idx, job in enumerate(candidate_data.jobs):
        raw_skills = getattr(job, "raw_skills", [])
        esco_uris = [map_to_esco_uri(s) for s in raw_skills if map_to_esco_uri(s)]
        
        desc = getattr(job, "description", "") or ""
        vector_id = generate_and_store_embedding(candidate_slug, f"job_{idx}", desc)
        
        job_dict = job.model_dump()
        job_dict["esco_skill_uris"] = esco_uris
        job_dict["vector_id"] = vector_id
        data_dict["jobs"].append(job_dict)

    # --- VECTOR MAPPING FOR EDUCATION ---
    for idx, edu in enumerate(candidate_data.education):
        desc = getattr(edu, "description", "") or ""
        vector_id = generate_and_store_embedding(candidate_slug, f"edu_{idx}", desc)
        
        edu_dict = edu.model_dump()
        edu_dict["vector_id"] = vector_id
        data_dict["education"].append(edu_dict)
        
    # --- VECTOR MAPPING FOR PUBLICATIONS ---
    for idx, pub in enumerate(candidate_data.publications):
        desc = getattr(pub, "description", "") or getattr(pub, "title", "")
        vector_id = generate_and_store_embedding(candidate_slug, f"pub_{idx}", desc)
        
        pub_dict = pub.model_dump()
        pub_dict["vector_id"] = vector_id
        data_dict["publications"].append(pub_dict)

    # Generate and Upload!
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    
    return graph.serialize(format="turtle")