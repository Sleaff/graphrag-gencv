import json
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from esco_service import batch_map_skills_to_esco, enrich_skills_with_hierarchy
from generate_rdf import create_rdf_graph, upload_to_graphdb
from llm_service import ChatMessage, call_llm
from vector_service import delete_candidate_embeddings, generate_and_store_embedding


class Address(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None


class Job(BaseModel):
    company: str
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None
    is_current: Optional[bool] = False
    career_level: Optional[str] = None
    job_type: Optional[str] = None
    raw_skills: List[str] = Field(default_factory=list)
    address: Optional[Address] = None


class Education(BaseModel):
    degree: str
    institution: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
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
    is_current: Optional[bool] = False


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
    description: Optional[str] = None


class OtherInfo(BaseModel):
    type: str
    description: str


class CandidateProfile(BaseModel):
    name: str
    gender: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[Address] = None
    drivers_licence: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    email: Optional[str] = None
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
    websites: List[Website] = Field(default_factory=list)
    instant_messaging: List[InstantMessaging] = Field(default_factory=list)
    honors: List[HonorAward] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    other_info: List[OtherInfo] = Field(default_factory=list)

    class Config:
        populate_by_name = True


def prepare_candidate_data(candidate_data: CandidateProfile) -> dict:
    candidate_slug = candidate_data.name.replace(" ", "_").lower()
    data_dict = candidate_data.model_dump()

    all_raw_skills = set(data_dict.get("technical_skills", []))
    for job in data_dict.get("jobs", []):
        all_raw_skills.update(job.get("raw_skills", []))

    all_raw_skills_list = list(all_raw_skills)
    if all_raw_skills_list:
        logger.info(f"Batch mapping {len(all_raw_skills_list)} unique skills...")
        mapped_skills = batch_map_skills_to_esco(all_raw_skills_list)
        logger.info("Enriching skills with ESCO hierarchy...")
        enriched_skills = enrich_skills_with_hierarchy(mapped_skills)
    else:
        enriched_skills = {}

    data_dict["technical_skills"] = [
        {"name": skill, "esco_data": enriched_skills.get(skill)}
        for skill in data_dict.get("technical_skills", [])
    ]

    for job in data_dict.get("jobs", []):
        job["esco_skills"] = [
            {"name": skill, "esco_data": enriched_skills.get(skill)}
            for skill in job.get("raw_skills", [])
        ]
        job.pop("raw_skills", None)

    delete_candidate_embeddings(candidate_slug)

    for idx, job in enumerate(data_dict["jobs"]):
        job["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"job_{idx}",
            job.get("description", "") or job.get("title", ""),
        )

    for idx, edu in enumerate(data_dict["education"]):
        edu["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"edu_{idx}",
            edu.get("description", "") or edu.get("degree", ""),
        )

    for idx, proj in enumerate(data_dict["projects"]):
        proj["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"proj_{idx}",
            proj.get("description", "") or proj.get("name", ""),
        )

    for idx, pub in enumerate(data_dict["publications"]):
        pub["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"pub_{idx}",
            pub.get("description", "") or pub.get("title", ""),
        )

    for idx, crs in enumerate(data_dict["courses"]):
        crs["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"course_{idx}",
            crs.get("description", "") or crs.get("title", ""),
        )

    for idx, pat in enumerate(data_dict["patents"]):
        pat["vector_id"] = generate_and_store_embedding(
            candidate_slug,
            f"patent_{idx}",
            pat.get("description", "") or pat.get("title", ""),
        )

    return data_dict


async def map_cv_to_rdf(cv_markdown: str) -> str:
    messages = [
        ChatMessage(
            role="system",
            content="""You are an expert HR parser. Extract the full profile data perfectly aligning with the schema.
IMPORTANT: For the job 'description', ONLY extract the description of the main activities and responsibilities. Do NOT include descriptions of the company itself.
IMPORTANT: Only include a reference when an actual person's name is explicitly provided. Statements such as 'References are available upon request' are not references and must return an empty 'references' array.
IMPORTANT: Extract named or substantial academic work, including Master's theses, Bachelor's projects, capstone projects, and academic research projects, into the "projects" array, even when it appears inside an Education section.
Return ONLY a valid JSON object matching this schema exactly:
{
    "name": "full name", "gender": "...", "nationality": "...", "date_of_birth": "...", "drivers_licence": "...", "short_description": "...", "long_description": "...",
    "email": "...",
    "phone_mobile": "...", "phone_home": "...", "phone_work": "...",
    "jobs": [{"company": "...", "title": "...", "start": "...", "end": "...", "career_level": "...", "job_type": "...", "raw_skills": ["..."], "description": "...", "is_current": false, "address": {"city": "...", "country": "...", "street": "...", "postal_code": "..."}}],
    "education": [{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "field_of_study": "...", "description": "..."}],
    "courses": [{"title": "...", "description": "...", "url": "...", "start_date": "...", "finish_date": "...", "has_certification": true, "organized_by": "..."}],
    "patents": [{"title": "...", "office": "...", "number": "...", "inventor": "...", "url": "...", "description": "...", "issued_date": "...", "status": "..."}],
    "projects": [{"name": "...", "role": "...", "start_date": "...", "end_date": "...", "description": "...", "url": "...", "creator": "...", "is_current": false}],
    "technical_skills": ["skill1", "skill2"],
    "languages": [{"name": "...", "proficiency": "..."}],
    "address": {"city": "...", "country": "...", "street": "...", "postal_code": "..."},
    "websites": [{"url": "...", "website_type": "..."}],
    "instant_messaging": [{"name": "...", "username": "..."}],
    "honors": [{"title": "...", "issuer": "...", "date": "..."}],
    "publications": [{"title": "...", "publisher": "...", "date": "...", "description": "..."}],
    "references": [{"name": "...", "relation": "..."}],
    "other_info": [{"type": "...", "description": "..."}]
}""",
        ),
        ChatMessage(role="user", content=cv_markdown),
    ]

    candidate_data_json = call_llm(messages)
    logger.debug(f"LLM returned candidate data: {candidate_data_json}")

    if not candidate_data_json:
        raise ValueError("LLM returned empty candidate data.")

    try:
        if "```json" in candidate_data_json:
            candidate_data_json = (
                candidate_data_json.split("```json")[1].split("```")[0].strip()
            )
        elif "```" in candidate_data_json:
            candidate_data_json = (
                candidate_data_json.split("```")[1].split("```")[0].strip()
            )

        parsed_data = json.loads(candidate_data_json)
        candidate_data = CandidateProfile(**parsed_data)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}") from e

    data_dict = prepare_candidate_data(candidate_data)
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    return graph.serialize(format="turtle")


async def generate_rdf_and_vectors(candidate_data: CandidateProfile) -> str:
    """Takes a strictly structured Pydantic model and inserts it into ChromaDB and GraphDB."""
    data_dict = prepare_candidate_data(candidate_data)
    graph = create_rdf_graph(data_dict)
    upload_to_graphdb(graph)
    return graph.serialize(format="turtle")
