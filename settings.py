# settings.py
from dotenv import load_dotenv
import os

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "campusai")
LLM_BASE_URL = os.getenv("CAMPUSAI_BASE_URL", "https://api.campusai.compute.dtu.dk/v1")
LLM_MODEL = os.getenv("CAMPUSAI_MODEL", "chat")
LLM_API_KEY = os.getenv("CAMPUSAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("CAMPUSAI_EMBEDDING_MODEL", "embed")
GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200/repositories/ResumeGraph")
ESCO_GRAPHDB_URL = os.getenv("ESCO_GRAPHDB_URL", "http://localhost:7200/repositories/EscoGraph")