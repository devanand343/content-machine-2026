import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.config import CHEAP_MODEL
import json

def process_file_to_dataframe(file_path: str) -> pd.DataFrame:
    """Read CSV or Excel into a pandas DataFrame."""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

def generate_search_queries(topic: str, keyword: str) -> list[str]:
    """
    Task 4: Generates a series of questions and queries based on the topic and keyword
    using GPT-4o-mini (Task 5, 6, 4 use cheaper model).
    """
    llm = ChatOpenAI(model=CHEAP_MODEL, temperature=0.7)
    
    prompt = PromptTemplate.from_template(
        "You are an expert SEO researcher. Given the topic and target keyword, generated a JSON array "
        "of 3-5 diverse search queries and questions that capture the search intent. These will be used to search "
        "our internal vector database.\n\n"
        "Topic: {topic}\n"
        "Keyword: {keyword}\n\n"
        "Return ONLY a JSON list of strings, e.g. [\"query1\", \"query2\"]."
    )
    
    chain = prompt | llm
    result = chain.invoke({"topic": topic, "keyword": keyword})
    
    try:
        queries = json.loads(result.content.strip("```json\n").strip("```"))
        if isinstance(queries, list):
            return queries
    except Exception as e:
        print(f"Failed to parse queries: {e}")
        # fallback
        return [f"What is {topic}?", f"Best practices for {keyword}"]
    
    return [topic, keyword]

