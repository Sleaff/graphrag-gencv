import uuid
import json
from loguru import logger
from llm_service import call_llm, call_embedding
from vector_service import collection
from SPARQLWrapper import SPARQLWrapper, POST, JSON
from pydantic import BaseModel
from typing import List

GRAPHDB_UPDATE_URL = "http://localhost:7200/repositories/your_repo_name/statements"

# Define the exact structure we want the LLM to extract
class Job(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str
    description: str
    skills: List[str]

class CandidateProfile(BaseModel):
    jobs: List[Job]

def extract_structured_data(raw_text: str) -> dict:
    """Uses the LLM to parse raw CV text into a strict JSON structure."""
    prompt = f"""
    You are an expert CV parser. Extract all work job from the following text.
    Return ONLY a valid JSON object matching this schema:
    {{
        "jobs": [
            {{
                "company": "Company Name",
                "title": "Job Title",
                "start_date": "YYYY-MM",
                "end_date": "YYYY-MM or Present",
                "description": "Detailed description of the role.",
                "skills": ["Skill1", "Skill2"]
            }}
        ]
    }}
    
    Raw Text:
    {raw_text}
    """
    
    logger.info("Extracting structured data via LLM...")
    # Ensure your call_llm function forces JSON output here
    response_text = call_llm(prompt, response_format={"type": "json_object"})
    return json.loads(response_text)

def process_new_profile(candidate_name: str, raw_text: str) -> str:
    """Orchestrates parsing, vector insertion, and graph insertion."""
    
    # 1. Parse the messy text into clean JSON
    structured_data = extract_structured_data(raw_text)
    
    sparql_triples = []
    
    # Base candidate node
    candidate_uri = f"ex:Candidate_{candidate_name.replace(' ', '')}"
    sparql_triples.append(f"{candidate_uri} a ex:Candidate ; ex:name \"{candidate_name}\" .")

    for exp in structured_data.get("jobs", []):
        # Generate a unique ID for this specific job
        exp_id = str(uuid.uuid4())
        exp_uri = f"ex:Job_{exp_id}"
        company_uri = f"ex:Company_{exp['company'].replace(' ', '')}"
        
        # 2. Insert into ChromaDB (Vector Search)
        # We embed the description and store it with the exp_id so we can link it later
        logger.info(f"Generating embedding for job at {exp['company']}...")
        embedding = call_embedding(text=exp["description"])
        
        collection.add(
            embeddings=[embedding],
            documents=[exp["description"]],
            metadatas=[{"candidate": candidate_name, "company": exp["company"]}],
            ids=[exp_id]  # The ID matches the GraphDB URI
        )

        # 3. Build the SPARQL Triples (Graph Search)
        sparql_triples.extend([
            f"{exp_uri} a ex:Job .",
            f"{exp_uri} ex:atCompany {company_uri} .",
            f"{exp_uri} ex:hasTitle \"{exp['title']}\" .",
            f"{candidate_uri} ex:hasJob {exp_uri} ."
        ])
        
        for skill in exp.get("skills", []):
            skill_uri = f"ex:Skill_{skill.replace(' ', '')}"
            sparql_triples.extend([
                f"{skill_uri} a ex:Skill .",
                f"{skill_uri} ex:name \"{skill}\" .",
                f"{exp_uri} ex:usesSkill {skill_uri} ."
            ])

    # Execute the SPARQL Insert
    insert_query = "PREFIX ex: <http://example.org/>\nINSERT DATA {\n" + "\n".join(sparql_triples) + "\n}"
    
    logger.info("Inserting triples into GraphDB...")
    sparql = SPARQLWrapper(GRAPHDB_UPDATE_URL)
    sparql.setMethod(POST)
    sparql.setQuery(insert_query)
    sparql.query()
    
    return f"Successfully ingested profile for {candidate_name} with {len(structured_data.get('jobs', []))} jobs."