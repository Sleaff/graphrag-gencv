from loguru import logger
import chromadb
from llm_service import call_embedding

client = chromadb.PersistentClient(path="./vector_data")
collection = client.get_or_create_collection(name="candidate_narratives")

def generate_and_store_embedding(candidate_slug: str, job_idx: str, description: str):
    """Generates an embedding and saves it locally."""
    if not description:
        logger.warning(f"No description provided for {candidate_slug} {job_idx}. Using default.")
        description = "No description provided."
        
    logger.debug(f"Generating embedding for {candidate_slug} ({job_idx})...")
    embedding = call_embedding(model="embed", text=description) 
    doc_id = f"{candidate_slug}_{job_idx}"
    
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[{"candidate": candidate_slug, "job_idx": job_idx}]
    )
    logger.info(f"Stored vector {doc_id} in ChromaDB.")
    return doc_id