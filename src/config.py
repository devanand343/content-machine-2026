import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

# Collection names
COLLECTIONS = {
    "standard_info": "StandardInfo",
    "company_data": "CompanyData",
    "local_codebase": "LocalCodebase"
}

# Model assignments
CHEAP_MODEL = "gpt-4o-mini"
EXPENSIVE_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"
