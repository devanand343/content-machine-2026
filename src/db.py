import chromadb
from chromadb.config import Settings
from src.config import CHROMA_DB_DIR, COLLECTIONS

def get_chroma_client():
    """
    Returns a connected client to the local ChromaDB database.
    """
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=Settings(anonymized_telemetry=False))
    return client

def initialize_collections():
    """
    Task 1: Creates three collections in the ChromaDB vector:
    1. StandardInfo: stores files that have standard information, textbook explanations.
    2. CompanyData: stores files that have internal company data, personal experiences.
    3. LocalCodebase: stores the local codebase to fetch code blocks.
    """
    client = get_chroma_client()
    
    # We create collections if they do not exist
    collections = {}
    for key, name in COLLECTIONS.items():
        collection = client.get_or_create_collection(
            name=name,
            metadata={"description": f"Collection for {name}"}
        )
        collections[key] = collection
        
    return collections

if __name__ == "__main__":
    colls = initialize_collections()
    for key, col in colls.items():
        print(f"Initialized collection: {col.name}")
