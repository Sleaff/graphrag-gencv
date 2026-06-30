from loguru import logger
from vector_service import collection
from query_graph import get_candidate_profile, GRAPHDB_URL
from llm_service import call_embedding
from SPARQLWrapper import SPARQLWrapper, JSON

def hybrid_search(job_description: str, candidate_name: str):
    """Orchestrates the semantic search and filters the result via GraphDB."""
    logger.info(f"Starting hybrid search for '{candidate_name}'...")
    
    # --- NEW: Truncate to avoid ContextWindowExceededError ---
    # 350 words is safely under the 512 token limit for most tokenizers
    safe_job_description = " ".join(job_description.split()[:250])
    logger.debug(f"Truncated job description to {len(safe_job_description.split())} words for embedding.")
    
    # 1. Semantic Step
    logger.debug("Generating embedding for job description...")
    query_embedding = call_embedding(text=safe_job_description) # Pass the safe version
    
    logger.debug("Querying ChromaDB for semantic matches...")
    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    
    if not results["ids"] or not results["ids"][0]:
        logger.warning("No semantic matches found in ChromaDB.")
        return {"message": "No semantic matches found."}
        
    candidate_doc_ids = results["ids"][0]
    logger.info(f"Found {len(candidate_doc_ids)} semantic matches: {candidate_doc_ids}")
    
    # 2. Graph Step
    logger.debug("Filtering Knowledge Graph using semantic matches...")
    hybrid_results = get_hybrid_profile(candidate_name, candidate_doc_ids)
    
    # 3. Data Extraction
    if hybrid_results["results"]["bindings"]:
        logger.success("Graph constraints met. Retrieving full candidate profile.")
        return get_candidate_profile(candidate_name)
    else:
        logger.warning("Vectors matched, but Graph constraints failed (no relevant work history).")
        return {"message": "No semantically relevant work history found for this candidate."}

def get_hybrid_profile(candidate_name: str, vector_ids: list[str]):
    """Queries GraphDB to verify if the candidate has any work history linked to semantic matches."""
    
    vector_filter = ", ".join([f"'{vid}'" for vid in vector_ids])
    sparql = SPARQLWrapper(GRAPHDB_URL)
    
    query = f"""
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    
    SELECT DISTINCT ?cv WHERE {{
        ?cv my0:aboutPerson ?person .
        ?person my0:firstName "{candidate_name}" .
        
        ?cv my0:hasWorkHistory ?work .
        ?work my0:hasVectorReference ?vectorId .
        
        FILTER (?vectorId IN ({vector_filter}))
    }}
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()