import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from src.config import CHROMA_DB_DIR, COLLECTIONS, EMBEDDING_MODEL, CHEAP_MODEL, EXPENSIVE_MODEL
from src.db import get_chroma_client

def retrieve_and_rerank(queries: list[str], output_filename: str = "context.txt"):
    """
    Task 3: Search ChromaDB across all queries, use LLM prompt as a re-ranker/synthesizer, 
    and return a consolidated text file.
    """
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    all_retrieved_docs = []
    
    # 1. Fetch from Chroma DB using dense representations
    # loop over all collections
    for col_key, col_name in COLLECTIONS.items():
        try:
            vectorstore = Chroma(
                client=get_chroma_client(),
                collection_name=col_name,
                embedding_function=embeddings
            )
            
            # Hybrid-like approach natively with MMR (Maximal Marginal Relevance) 
            # and semantic similarity to get diverse and relevant chunks
            retriever_mmr = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3})
            retriever_sim = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
            
            for query in queries:
                docs_mmr = retriever_mmr.invoke(query)
                docs_sim = retriever_sim.invoke(query)
                all_retrieved_docs.extend(docs_mmr + docs_sim)
                
        except Exception as e:
            # Collection might be empty or not created yet
            print(f"Skipping collection {col_name}: {e}")
            continue

    if not all_retrieved_docs:
        print("No documents found across collections.")
        # Create an empty file just so it exists
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("No internal data found. You must rely on standard web knowledge.")
        return output_filename

    # Remove duplicates
    unique_docs = {doc.page_content: doc for doc in all_retrieved_docs}.values()
    
    # 2. Re-rank and synthesize using LLM Prompt
    # GPT-4o as the prompt re-ranker and synthesizer (Task 3 requested better models GPT-4o)
    llm = ChatOpenAI(model=EXPENSIVE_MODEL, temperature=0.1)
    
    prompt = PromptTemplate.from_template(
        "You are an expert AI agent responsible for re-ranking and synthesizing retrieved context.\n"
        "Given the following user search queries and retrieved context snippets, re-order them based on relevance, "
        "throw away fluff, and write a well-documented single comprehensive text summary that captures all important facts.\n\n"
        "Queries: {queries}\n\n"
        "Context Snippets:\n{context}\n\n"
        "Synthesized Document:"
    )
    
    context_str = "\n\n---\n\n".join([doc.page_content for doc in unique_docs])
    chain = prompt | llm
    
    result = chain.invoke({"queries": ", ".join(queries), "context": context_str})
    
    # 3. Save to a single output text file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(result.content)
        
    return output_filename

