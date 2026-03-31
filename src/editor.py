import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.config import EXPENSIVE_MODEL

def edit_and_verify_seo(draft_markdown: str, context_file: str) -> str:
    """
    Task 7: Acts as an editor and SEO verifier.
    Checks for accuracy, ensures no fluff, optimizes for SEO, and checks for entity mapping
    against the given context.
    """
    llm = ChatOpenAI(model=EXPENSIVE_MODEL, temperature=0.2)
    
    context = ""
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()

    prompt = PromptTemplate.from_template(
        "You are an expert SEO Editor and Fact Checker. Review the following article draft against the provided context document.\n"
        "Your Goals:\n"
        "1. Verify Accuracy: Ensure any claims made or internal data mentioned are strictly present in the Context Document. Do not allow AI hallucinations.\n"
        "2. Strip Fluff: Remove unnecessary information, redundant phrases, or overly flowery language.\n"
        "3. SEO Optimization: Ensure keywords are naturally integrated and semantic entity mapping is preserved.\n"
        "4. Format: Return the final optimized article in raw Markdown format, ready to be converted into HTML.\n\n"
        "Context Document:\n---\n{context}\n---\n\n"
        "Draft Article:\n---\n{draft}\n---\n\n"
        "Optimized Final Article (Markdown only):"
    )
    
    chain = prompt | llm
    result = chain.invoke({"context": context, "draft": draft_markdown})
    
    return result.content
