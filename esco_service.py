import json

from loguru import logger
from SPARQLWrapper import JSON, SPARQLWrapper

from llm_service import ChatMessage, call_llm
from settings import ESCO_GRAPHDB_URL


def sparql_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def parse_json_object(value: str) -> dict:
    text = (value or "").strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object.")
    return parsed


def get_esco_skill_uri_from_db(raw_skill: str, limit: int = 5) -> list[dict]:
    """Retrieves skill URIs for a single skill from GraphDB."""
    normalized_skill = raw_skill.lower().strip()
    if not normalized_skill:
        return []

    sparql = SPARQLWrapper(ESCO_GRAPHDB_URL)
    query = f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT ?uri ?label ?parentLabel WHERE {{
        ?uri a <http://data.europa.eu/esco/model#Skill> ;
             skos:prefLabel ?label .
        OPTIONAL {{
            ?uri skos:broader ?parentUri .
            ?parentUri skos:prefLabel ?parentLabel .
            FILTER(LANG(?parentLabel) = "" || LANGMATCHES(LANG(?parentLabel), "en"))
        }}
        FILTER(LANG(?label) = "" || LANGMATCHES(LANG(?label), "en"))
        FILTER(CONTAINS(LCASE(STR(?label)), {sparql_string(normalized_skill)}))
    }} LIMIT {max(1, int(limit))}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        candidates_by_uri = {}
        for binding in results["results"]["bindings"]:
            uri = binding["uri"]["value"]
            candidate = candidates_by_uri.setdefault(
                uri,
                {
                    "uri": uri,
                    "label": binding["label"]["value"],
                    "parent": "",
                },
            )
            parent_label = binding.get("parentLabel", {}).get("value", "")
            if parent_label and not candidate["parent"]:
                candidate["parent"] = parent_label

        candidates = list(candidates_by_uri.values())
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

    final_mapping = {}
    to_rank = {}

    for skill, candidates in all_candidates.items():
        if not candidates:
            final_mapping[skill] = "NONE"
            continue

        exact_matches = [
            candidate
            for candidate in candidates
            if candidate["label"].strip().casefold() == skill.strip().casefold()
        ]
        if len(exact_matches) == 1:
            final_mapping[skill] = exact_matches[0]["uri"]
        else:
            to_rank[skill] = candidates

    logger.info(
        f"Auto-mapped: {len(final_mapping)} | Requires LLM ranking: {len(to_rank)}"
    )

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

    response = call_llm(
        [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=json.dumps(to_rank)),
        ]
    )

    try:
        llm_results = parse_json_object(response)
        valid_uris = {
            skill: {candidate["uri"] for candidate in candidates}
            for skill, candidates in to_rank.items()
        }
        for skill in to_rank:
            uri = llm_results.get(skill, "NONE")
            if uri in valid_uris[skill]:
                final_mapping[skill] = uri
                logger.info(f"LLM mapped '{skill}' -> {uri}")
            else:
                final_mapping[skill] = "NONE"
                logger.warning(f"LLM could not map skill: '{skill}'")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse LLM mapping response: {e}")
        for skill in to_rank:
            final_mapping[skill] = "NONE"

    return final_mapping


def enrich_skills_with_hierarchy(mapped_skills: dict, plus: bool = False) -> dict:
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

        query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?parentLabel WHERE {{
            <{uri}> skos:broader{"+" if plus else ""} ?parentUri .
            ?parentUri skos:prefLabel ?parentLabel .
            FILTER(LANG(?parentLabel) = "" || LANGMATCHES(LANG(?parentLabel), "en"))
        }}
        """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        try:
            results = sparql.query().convert()
            parents = [
                b["parentLabel"]["value"] for b in results["results"]["bindings"]
            ]

            enriched_profile[raw_skill] = {"uri": uri, "parents": parents}
            logger.debug(
                f"Enriched '{raw_skill}' with {len(parents)} parent categories."
            )
        except Exception as e:
            logger.error(f"Failed to fetch parents for '{raw_skill}' ({uri}): {e}")
            enriched_profile[raw_skill] = {"uri": uri, "parents": []}

    return enriched_profile


if __name__ == "__main__":
    test_skills = [
        "Python",
        "React",
        "Data Analysis",
        "Software Development",
        "Full Stack",
        "UnknownSkill",
    ]
    mapping = batch_map_skills_to_esco(test_skills)
    logger.success(f"Final mapping complete: {json.dumps(mapping, indent=2)}")
    logger.info(
        f"Enriched skill hierarchy: {json.dumps(enrich_skills_with_hierarchy(mapping), indent=2)}"
    )
