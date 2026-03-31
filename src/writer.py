import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.config import CHEAP_MODEL
import json

class Section(BaseModel):
    title: str = Field(description="The title of the section")
    description: str = Field(description="Brief instruction on what to cover in this section")

class Outline(BaseModel):
    sections: list[Section]

def generate_outline(topic: str, keyword: str, search_intent: str = "Informational", context_file: str = "context.txt") -> Outline:
    """
    Task 5: Generates an article outline based on search intent and keyword using an LLM.
    """
    llm = ChatOpenAI(model=CHEAP_MODEL, temperature=0.7)
    
    # Read context if available to frame the outline better
    context = ""
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()[:2000] # Provide first 2000 chars of context for outline help

    prompt = PromptTemplate.from_template(
        "You are an expert Content Strategist. Create a comprehensive article outline "
        "for the following topic.\n\n"
        "Topic: {topic}\nTarget Keyword: {keyword}\nSearch Intent: {search_intent}\n"
        "Context (if any): {context}\n\n"
        "Return the output as a JSON object matching this schema:\n"
        "{{\"sections\": [{{\"title\": \"string\", \"description\": \"string\"}}]}}"
    )
    
    chain = prompt | llm
    result = chain.invoke({
        "topic": topic,
        "keyword": keyword,
        "search_intent": search_intent,
        "context": context
    })
    
    try:
        # Pydantic parsing can be robust with standard string manipulation
        cleaned_json = result.content.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json.replace("```json", "").replace("```", "")
            
        data = json.loads(cleaned_json)
        return Outline(**data)
    except Exception as e:
        print(f"Error parsing outline JSON: {e}")
        # Return a default fallback outline
        return Outline(sections=[
            Section(title="Introduction", description=f"Introduce {topic} and mention {keyword}"),
            Section(title=f"Understanding {keyword}", description="Explain the core concepts"),
            Section(title="Conclusion", description="Wrap up the article")
        ])

async def write_article_section_wise(outline: Outline, context_file: str) -> str:
    """
    Task 6: Writes comprehensive article section-wise based on the outline and retrieved context.
    Uses summarization technique for previous sections to avoid redundancy.
    """
    llm = ChatOpenAI(model=CHEAP_MODEL, temperature=0.7)
    
    context = ""
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()

    full_article = []
    previous_sections_summary = "None yet."
    
    for idx, section in enumerate(outline.sections):
        print(f"Writing section: {section.title}")
        
        system_msg = SystemMessage(content=(
            "You are an expert SEO Content Writer. Write a detailed, human-readable section for an article. "
            "Use the provided context to add personal/authoritative touches and factual standard info.\n"
            f"Context Document:\n---\n{context}\n---\n\n"
            f"Summary of previously written sections (so you avoid repetition):\n{previous_sections_summary}\n"
        ))
        
        human_msg = HumanMessage(content=(
            f"Write the section titled '{section.title}'.\n"
            f"Instructions for this section: {section.description}\n\n"
            "Output the section content in Markdown format (use proper heading sizes like ## or ### etc.)."
        ))
        
        response = llm.invoke([system_msg, human_msg])
        section_content = response.content
        full_article.append(section_content)
        
        # After writing, update the moving summary using a quick LLM call to save tokens
        if idx < len(outline.sections) - 1: # No need to summarize after the last section
            summary_prompt = PromptTemplate.from_template(
                "Summarize the main points covered in the following article section in 2-3 sentences max. "
                "This summary helps the writer of the next section avoid repeating information.\n\nSection:\n{section_text}"
            )
            summary_chain = summary_prompt | llm
            summary_res = summary_chain.invoke({"section_text": section_content})
            
            if previous_sections_summary == "None yet.":
                previous_sections_summary = ""
                
            previous_sections_summary += f"\n- {section.title}: {summary_res.content}"

    final_markdown = "\n\n".join(full_article)
    return final_markdown

