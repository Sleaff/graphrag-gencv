# settings.py
from dotenv import load_dotenv
import os

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "campusai")
LLM_BASE_URL = os.getenv("CAMPUSAI_BASE_URL", "https://api.campusai.compute.dtu.dk/v1")
LLM_MODEL = os.getenv("CAMPUSAI_MODEL", "Gemma 4")
LLM_API_KEY = os.getenv("CAMPUSAI_API_KEY", "")
