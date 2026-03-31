import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from src.config import CHROMA_DB_DIR, COLLECTIONS, EMBEDDING_MODEL
from src.db import get_chroma_client

def ingest_pdf(file_path: str, collection_key: str):
    """
    Task 2: Takes a PDF file path and a collection key (standard_info, company_data, local_codebase).
    Splits the PDF using RecursiveCharacterTextSplitter and saves chunks into ChromaDB.
    """
    if collection_key not in COLLECTIONS:
        raise ValueError(f"Invalid collection_key. Must be one of {list(COLLECTIONS.keys())}")
    
    collection_name = COLLECTIONS[collection_key]
    
    # 1. Load File (Support PDF and TXT)
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, autodetect_encoding=True)
    
    docs = loader.load()
    
    # 2. Split with Overlap
    # Use RecursiveCharacterTextSplitter as requested
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    splits = text_splitter.split_documents(docs)
    
    # 3. Store into ChromaDB
    # We initialize the embedding model
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    # Use Chroma integration in Langchain to add documents
    vectorstore = Chroma(
        client=get_chroma_client(),
        collection_name=collection_name,
        embedding_function=embeddings
    )
    
    # Add documents (LangChain's Chroma wrapper automatically persists on insertion in new versions, 
    # but we just call add_documents)
    vectorstore.add_documents(documents=splits)
    
    return f"Successfully ingested {len(splits)} chunks into {collection_name}."

