import os
import asyncio
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from src.query_generator import generate_search_queries
from src.retriever import retrieve_and_rerank
from src.writer import generate_outline, write_article_section_wise, Outline
from src.editor import edit_and_verify_seo
from src.exporter import export_as_html

# Define State Schema
class GeneralState(TypedDict):
    topic: str
    keyword: str
    search_intent: str
    # Context
    queries: list[str]
    context_file: str
    # Drafting
    outline: Optional[Outline]
    outline_feedback: str # In case of rejection
    outline_approved: bool # Human in loop toggle
    article_draft: str
    final_article: str
    html_path: str

# Node Functions
def node_generate_queries(state: GeneralState):
    print("Graph: Generating Search Queries (Task 4)")
    queries = generate_search_queries(state["topic"], state["keyword"])
    return {"queries": queries}

def node_retrieve_context(state: GeneralState):
    print("Graph: Retrieving and Synthesizing Context (Task 3)")
    context_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"context_{hash(state['topic'])}.txt")
    retrieve_and_rerank(state["queries"], context_file)
    return {"context_file": context_file}

def node_generate_outline(state: GeneralState):
    print("Graph: Generating Outline (Task 5)")
    # Passes context file
    raw_outline = generate_outline(
        state["topic"], 
        state["keyword"], 
        state.get("search_intent", "Informational"), 
        state["context_file"]
    )
    
    # If there is rejection feedback, theoretically we should handle it in prompt. 
    # For now, we will override or update the outline accordingly.
    
    return {"outline": raw_outline, "outline_approved": False} # Resets approval

# HITL Router
def should_continue_drafting(state: GeneralState):
    if state.get("outline_approved", False):
        return "draft_article"
    elif state.get("outline_feedback", "") != "":
        # Back to outline generation
        return "generate_outline"
    else:
        # Pause for human approval
        return END

async def node_draft_article(state: GeneralState):
    print("Graph: Drafting Article Section-by-Section (Task 6)")
    draft = await write_article_section_wise(state["outline"], state["context_file"])
    return {"article_draft": draft}

def node_edit_article(state: GeneralState):
    print("Graph: Editing and SEO Verifying (Task 7)")
    final = edit_and_verify_seo(state["article_draft"], state["context_file"])
    return {"final_article": final}

def node_export_article(state: GeneralState):
    print("Graph: Exporting to HTML (Task 8)")
    path = export_as_html(state["final_article"], state["topic"])
    
    # Cleanup context file
    if os.path.exists(state["context_file"]):
        os.remove(state["context_file"])
        
    return {"html_path": path}

# Compile Graph
def build_graph():
    workflow = StateGraph(GeneralState)
    
    # Add Nodes
    workflow.add_node("generate_queries", node_generate_queries)
    workflow.add_node("retrieve_context", node_retrieve_context)
    workflow.add_node("generate_outline", node_generate_outline)
    # Using async wrapper for drafting
    workflow.add_node("draft_article", node_draft_article)
    workflow.add_node("edit_article", node_edit_article)
    workflow.add_node("export_article", node_export_article)
    
    # Add Edges
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_outline")
    
    # Conditional edge from generate_outline
    # The interrupt happens implicitly: if Streamlit gets the output and state["outline_approved"] is False, it will stop
    # because there is no edge leading out unless conditions are met. Streamlit will handle the pause explicitly by executing 
    # step-by-step or using the built-in interrupt in updated LangGraph.
    
    workflow.add_conditional_edges(
        "generate_outline",
        should_continue_drafting,
        {
            "draft_article": "draft_article",
            "generate_outline": "generate_outline",
            END: END
        }
    )
    
    workflow.add_edge("draft_article", "edit_article")
    workflow.add_edge("edit_article", "export_article")
    workflow.add_edge("export_article", END)
    
    app = workflow.compile()
    return app

if __name__ == "__main__":
    app = build_graph()
    print("Compiled successfully!")
