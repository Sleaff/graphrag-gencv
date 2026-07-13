import chromadb
from loguru import logger

from llm_service import call_embedding

client = chromadb.PersistentClient(path="./vector_data")
collection = client.get_or_create_collection(name="candidate_narratives")


def delete_candidate_embeddings(candidate_slug: str):
    """Removes stale embeddings before a candidate profile is replaced."""
    collection.delete(where={"candidate": candidate_slug})


def generate_and_store_embedding(candidate_slug: str, job_idx: str, description: str):
    """Generates an embedding and saves it locally."""
    if not description:
        logger.warning(
            f"No description provided for {candidate_slug} {job_idx}. Using default."
        )
        description = "No description provided."

    logger.debug(f"Generating embedding for {candidate_slug} ({job_idx})...")
    embedding = call_embedding(text=description)
    doc_id = f"{candidate_slug}_{job_idx}"

    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[{"candidate": candidate_slug, "job_idx": job_idx}],
    )
    logger.info(f"Stored vector {doc_id} in ChromaDB.")
    return doc_id
