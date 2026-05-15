import argparse
import json
from pathlib import Path
import httpx
from loguru import logger
from llm_service import call_llm, ChatMessage

def map_cv_to_rdf(cv_markdown: str, base_uri: str = "http://example.org/cv/") -> str:
    """Uses the LLM to dynamically map a Markdown CV into a resume2rdf RDF Turtle layout."""
    
    system_instruction = (
        "You are an expert semantic engineer specializing in the resume2rdf ontology and ESCO taxonomy. "
        "Your task is to parse a markdown CV and generate clean, valid RDF triples in Terse RDF Triple Language (Turtle) syntax. "
        "Output ONLY valid Turtle code. Do not wrap it in markdown code blocks like ```turtle."
    )

    user_prompt = f"""
    Analyze the following Markdown CV and translate it completely into RDF Turtle syntax using the resume2rdf schema layout.
    
    CRITICAL STRUCTURE & PREFIX RULES:
    - Base URI: <{base_uri}>
    - Use Prefix `my0:` for [http://example.com/resume2rdf_ontology.rdf#](http://example.com/resume2rdf_ontology.rdf#)
    - Use Prefix `myvalue0:` for [http://example.com/resume2rdf_value_ontology.rdf#](http://example.com/resume2rdf_value_ontology.rdf#)
    - Use Prefix `esco:` for [http://data.europa.eu/esco/model](http://data.europa.eu/esco/model)
    
    ONTOLOGY MAP INSTRUCTIONS:
    1. Entrypoint: Create a main instance `my0:CV`. Link it to the person using `my0:aboutPerson`.
    2. Core Structural Classes:
       - Work History -> Use `my0:WorkHistory`, connected via `my0:hasWorkHistory`. Define `my0:jobTitle`, `my0:jobDescription`, `my0:startDate`, `my0:endDate`, and `my0:employedIn` (linking to a `my0:Company`).
       - Education -> Use `my0:Education` (subclass of `esco:Qualification`), connected via `my0:hasEducation`.
       - Projects -> Use `my0:Project`, connected via `my0:hasProject`.
       - Skills -> Use `my0:Skill` (equivalent to `esco:Skill`), connected via `my0:hasSkill`. Use `my0:skillName` and `my0:skillDescription`. If a skill is a language, map it as `my0:LanguageSkill`.
       - Awards -> Use `my0:HonorAward`, connected via `my0:hasHonorAward`.
    3. Literal Formatting:
       - Standard strings must have language tags (e.g., "John"^xsd:string or "Developer"@en).
       - Dates must use xsd:date format ("YYYY-MM-DD"^^xsd:date).
       - Booleans must be plain true/false tokens.
       
    Markdown CV Data to Map:
    ---
    {cv_markdown}
    ---
    """

    logger.info("Sending CV payload to the LLM endpoint for RDF structural mapping...")
    messages = [
        ChatMessage(role="system", content=system_instruction),
        ChatMessage(role="user", content=user_prompt),
    ]
    raw_turtle = call_llm(messages)
    
    # Strip any accidental markdown formatting or code block wrapper text if generated
    raw_turtle = raw_turtle.replace("```turtle", "").replace("```", "").strip()
    return raw_turtle

def main():
    parser = argparse.ArgumentParser(description="Map Markdown CV data to resume2rdf Turtle graph via LLM API.")
    parser.add_argument("-i", "--input", required=True, help="Path to input markdown CV file")
    parser.add_argument("-o", "--output", help="Path to output .ttl file. Defaults to <input>.ttl")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".ttl")

    if not input_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {input_path}")

    cv_content = input_path.read_text(encoding="utf-8")
    
    try:
        turtle_output = map_cv_to_rdf(cv_content)
        output_path.write_text(turtle_output, encoding="utf-8")
        logger.success(f"RDF Turtle payload successfully written to {output_path}")
    except Exception as e:
        logger.critical(f"Pipeline mapping failed: {e}")

if __name__ == "__main__":
    main()