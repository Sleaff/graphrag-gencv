import re
from dataclasses import dataclass
import json
from fastapi import HTTPException
from generate_rdf import create_rdf_graph, upload_to_graphdb
from loguru import logger
from llm_service import call_llm, ChatMessage


HEADING_RE = re.compile(r"^#{1,6}\s+(?P<title>.+?)\s*$")
SECTION_ALIASES = {
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "education": "education",
    "skills": "skills",
    "technical skills": "skills",
    "projects": "projects",
}

@dataclass
class ParsedCV:
    sections: dict[str, str]

def split_markdown_sections(markdown: str) -> ParsedCV:
    """Splits raw markdown into standardized section blocks."""
    section_map = {}
    current_section = "summary"
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match:
            title = " ".join(heading_match.group("title").strip().lower().split())
            current_section = SECTION_ALIASES.get(title, title)
            section_map.setdefault(current_section, [])
            continue
        section_map.setdefault(current_section, []).append(line)
    return ParsedCV(sections={k: "\n".join(v) for k, v in section_map.items()})

async def extract_section_data_internal(section_name: str, text: str) -> dict:
    """Helper that formats the prompt and calls the LLM internally using your existing setup."""
    system_instruction = "You are a JSON data extraction API. Output ONLY raw JSON matching the requested schema. No markdown wrapping."
    user_prompt = f"""
    Extract entity details from this CV text under the section '{section_name}':
    "{text}"
    
    Format the output exactly like this JSON structure:
    {{
      "entities": [
        {{
          "type": "WorkHistory | Education | Skill | Project",
          "title": "Job title, degree name, skill name, or project name",
          "organization": "Company or School name if applicable",
          "start_date": "YYYY-MM-DD or empty string",
          "end_date": "YYYY-MM-DD or empty string",
          "description": "Details, roles, responsibilities, or tasks",
          "esco_hint": "If type is Skill, suggest the closest official lower-case ESCO skill label"
        }}
      ]
    }}
    """
    
    messages = [
        ChatMessage(role="system", content=system_instruction),
        ChatMessage(role="user", content=user_prompt),
    ]
    
    try:
        # Utilizing your existing internal call_llm wrapper
        response_text = call_llm(messages)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        return json.loads(response_text.strip())
    except Exception as e:
        logger.warning(f"LLM section extraction failed for {section_name}: {e}")
        return {"entities": []}
    
async def map_cv_to_rdf(cv_markdown: str) -> str:
    """The main pipeline function called by FastAPI."""
    
    # 1. We'll extract the 'experience' section as a test
    parsed_cv = split_markdown_sections(cv_markdown)
    experience_text = parsed_cv.sections.get("experience", "")
    
    if not experience_text:
        return "No experience section found to convert."

    # 2. Get the JSON from the LLM
    logger.info("Extracting JSON via LLM...")
    llm_json_output = await extract_section_data_internal("experience", experience_text)
    
    # 3. Reformat the LLM output to match what generate_rdf.py expects
    candidate_data = {
        "name": "Unknown Candidate", # You can extract the real name from the 'summary' section later
        "experiences": []
    }
    
    for entity in llm_json_output.get("entities", []):
        if entity["type"].lower() == "workhistory" or "experience" in entity["type"].lower():
            candidate_data["experiences"].append({
                "job_title": entity.get("title", "Unknown Role"),
                "company_name": entity.get("organization", "Unknown Company"),
                "start_date": entity.get("start_date", "YYYY-MM"),
                "end_date": entity.get("end_date", ""),
                "esco_skill_uris": [] # Add real linking logic here later
            })

    # 4. Generate the Graph and Upload!
    logger.info("Converting JSON to RDF...")
    graph = create_rdf_graph(candidate_data)
    upload_to_graphdb(graph)
    
    # Return the raw RDF string so you can see it in your API response
    return graph.serialize(format="turtle")