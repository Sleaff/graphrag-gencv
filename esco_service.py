import json
from SPARQLWrapper import SPARQLWrapper, JSON
from settings import ESCO_GRAPHDB_URL
from llm_service import call_llm, ChatMessage
from loguru import logger

def get_esco_skill_uri_from_db(raw_skill: str, limit: int = 5) -> list[dict]:
    """Retrieves skill URIs for a single skill from GraphDB."""
    sparql = SPARQLWrapper(ESCO_GRAPHDB_URL)
    query = f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?uri ?label ?parentLabel WHERE {{
        ?uri a <http://data.europa.eu/esco/model#Skill> ;
             skos:prefLabel ?label ;
             skos:broader ?parentUri .
        ?parentUri skos:prefLabel ?parentLabel .
        FILTER(CONTAINS(LCASE(?label), "{raw_skill.lower().strip()}"))
    }} LIMIT {limit}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        candidates = [
            {"uri": b["uri"]["value"], "label": b["label"]["value"], "parent": b["parentLabel"]["value"]}
            for b in results["results"]["bindings"]
        ]
        logger.debug(f"Retrieved {len(candidates)} candidates for: '{raw_skill}'")
        return candidates
    except Exception as e:
        logger.error(f"SPARQL query failed for '{raw_skill}': {e}")
        return []

def batch_map_skills_to_esco(raw_skills: list[str]) -> dict:
    """
    1. Sequential Retrieval: Queries DB for each skill.
    2. Parallel Ranking: Uses one LLM call to resolve all ambiguities.
    """
    logger.info(f"Starting batch mapping for {len(raw_skills)} skills.")
    
    all_candidates = {}
    for skill in raw_skills:
        all_candidates[skill] = get_esco_skill_uri_from_db(skill)
    
    to_rank = {s: c for s, c in all_candidates.items() if len(c) > 1}
    final_mapping = {s: c[0]["uri"] for s, c in all_candidates.items() if len(c) == 1}

    for s, c in all_candidates.items():
        if len(c) == 0:
            final_mapping[s] = "NONE"
    
    logger.info(f"Auto-mapped: {len(final_mapping)} | Requires LLM ranking: {len(to_rank)}")
    
    if not to_rank:
        logger.success("All skills resolved via database.")
        return final_mapping

    logger.info(f"Sending {len(to_rank)} skills to LLM for disambiguation.")
    system_prompt = (
        "You are an expert HR mapping engine. You are provided with raw skills and "
        "multiple candidate ESCO matches (including their parent categories). "
        "Select the best URI for each skill. If no match is a good fit, return 'NONE'. "
        "Output strictly as a JSON object: {'raw_skill': 'uri_or_none'}."
    )
    
    response = call_llm([
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=json.dumps(to_rank))
    ])
    
    try:
        llm_results = json.loads(response)
        for skill, uri in llm_results.items():
            if uri != "NONE":
                final_mapping[skill] = uri
                logger.info(f"LLM mapped '{skill}' -> {uri}")
            else:
                logger.warning(f"LLM could not map skill: '{skill}'")
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM mapping response")
        
    return final_mapping

def enrich_skills_with_hierarchy(mapped_skills: dict, plus: bool = True) -> dict:
    """
    Takes the resolved mapped skills and retrieves their parent categories.
    Uses the skos:broader+ property path to get all levels of parents.
    """
    enriched_profile = {}
    sparql = SPARQLWrapper(ESCO_GRAPHDB_URL)
    
    for raw_skill, uri in mapped_skills.items():
        if uri == "NONE":
            enriched_profile[raw_skill] = {"uri": None, "parents": []}
            continue
            
        # can use skos:broader+ to get all ancestors
        query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?parentLabel WHERE {{
            <{uri}> skos:broader{"+"if plus else ""} ?parentUri .
            ?parentUri skos:prefLabel ?parentLabel .
            FILTER(LANG(?parentLabel) = "en")
        }}
        """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        try:
            results = sparql.query().convert()
            parents = [b["parentLabel"]["value"] for b in results["results"]["bindings"]]
            
            enriched_profile[raw_skill] = {
                "uri": uri,
                "parents": parents
            }
            logger.debug(f"Enriched '{raw_skill}' with {len(parents)} parent categories.")
        except Exception as e:
            logger.error(f"Failed to fetch parents for '{raw_skill}' ({uri}): {e}")
            enriched_profile[raw_skill] = {"uri": uri, "parents": []}
            
    return enriched_profile


if __name__ == "__main__":
    test_skills = ["Python", "React", "Data Analysis", "Software Development", "Full Stack", "UnknownSkill"]
    mapping = batch_map_skills_to_esco(test_skills)
    logger.success(f"Final mapping complete: {json.dumps(mapping, indent=2)}")
    logger.info(f"Enriched skill hierarchy: {json.dumps(enrich_skills_with_hierarchy(mapping), indent=2)}")