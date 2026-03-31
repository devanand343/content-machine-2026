import streamlit as st
import pandas as pd
import tempfile
import time
import os
import asyncio
import nest_asyncio

# Force use of standard asyncio event loop to prevent uvloop conflicts with nest_asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

nest_asyncio.apply(loop)

from src.db import initialize_collections
from src.ingestion import ingest_pdf
from src.query_generator import process_file_to_dataframe
from src.graph import build_graph, GeneralState, node_draft_article, node_edit_article, node_export_article, node_generate_outline
from src.config import COLLECTIONS

st.set_page_config(page_title="Full Content Machine 2026", layout="wide")

# Initialize Vector DB Collections on Startup
if "db_initialized" not in st.session_state:
    try:
        initialize_collections()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Error initializing database: {e}")

st.title("🤖 Full Content Machine 2026")
st.markdown("Transform topics from a CSV/Excel into human-readable, SEO-optimized content using multi-agent RAG.")

# Sidebar: PDF Ingestion (Task 2)
st.sidebar.header("📁 Knowledge Base Ingestion")
with st.sidebar.form("ingestion_form"):
    st.write("Upload PDFs to enhance context.")
    collection_choice = st.selectbox(
        "Select Collection:",
        options=list(COLLECTIONS.keys()),
        format_func=lambda x: COLLECTIONS[x]
    )
    uploaded_file = st.file_uploader("Upload Knowledge File (PDF/TXT)", type=["pdf", "txt"])
    submit_ingest = st.form_submit_button("Ingest File")
    
    if submit_ingest and uploaded_file is not None:
        with st.spinner(f"Ingesting into {COLLECTIONS[collection_choice]}..."):
            ext = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                res = ingest_pdf(tmp_path, collection_choice)
                st.success(res)
            except Exception as e:
                st.error(f"Ingestion failed: {e}")
            finally:
                os.remove(tmp_path)

# Main Area: Content Generation (Tasks 4 -> 10)
st.header("1. Upload Content Calendar")
content_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

if content_file:
    # Read the data
    try:
        ext = "." + content_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content_file.getvalue())
            tmp_path_calendar = tmp.name
        
        df = process_file_to_dataframe(tmp_path_calendar)
        
        # We process the dataframe in memory, delete the calendar file immediately
        if os.path.exists(tmp_path_calendar):
            os.remove(tmp_path_calendar)
        st.write("Preview of Calendar:")
        st.dataframe(df.head())
        
        # We assume columns "Topic" and "Keyword" exist. Let the user map them.
        cols = df.columns.tolist()
        col1, col2 = st.columns(2)
        topic_col = col1.selectbox("Select Topic Column", cols, index=0)
        keyword_col = col2.selectbox("Select Keyword Column", cols, index=1 if len(cols)>1 else 0)
        
        start_machine = st.button("🚀 Run Content Machine")
        
        # Initialization
        if start_machine:
            st.session_state.processing_queue = df.to_dict('records')
            st.session_state.current_topic_idx = 0
            st.session_state.total_topics = len(df)
            st.session_state.graph = build_graph()
            
            # Rough estimate: ~5 minutes per article
            st.session_state.estimated_time = st.session_state.total_topics * 5
            
    except Exception as e:
        st.error(f"Error loading file: {e}")

# Handle Queue and HITL
if "processing_queue" in st.session_state and st.session_state.current_topic_idx < st.session_state.total_topics:
    st.header("⚙️ Machine Progress")
    progress_val = st.session_state.current_topic_idx / st.session_state.total_topics
    st.progress(progress_val)
    st.write(f"Processed: {st.session_state.current_topic_idx}/{st.session_state.total_topics}. " 
             f"Est. Time remaining: {(st.session_state.total_topics - st.session_state.current_topic_idx) * 5} mins")
    
    current_row = st.session_state.processing_queue[st.session_state.current_topic_idx]
    topic = current_row[topic_col]
    keyword = current_row[keyword_col]
    
    st.subheader(f"Current Topic: {topic}")
    
    if "current_state" not in st.session_state:
        # Initialize node execution
        initial_state = {
            "topic": topic,
            "keyword": keyword,
            "search_intent": current_row.get("Search Intent", "Informational"),
            "outline_approved": False,
            "outline_feedback": ""
        }
        with st.spinner("Executing Phase 1 (Query -> Retrieve Context -> Outline)"):
            app = build_graph()
            # We use an async loop explicitly inside Streamlit sync code
            state = initial_state
            # LangGraph step by step manually or let it run to END. Since we return END from routing on lack of approval...
            # We can invoke it, and it will stop after generate_outline because should_continue_drafting returns END.
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            final_state = app.invoke(initial_state)
            st.session_state.current_state = final_state
            st.rerun()

    else:
        state = st.session_state.current_state
        
        # Since it's stopped after Outline, we render the HITL
        if not state.get("outline_approved", False) and "outline" in state:
            st.info("Human in the Loop: Outline Review")
            st.json([s.model_dump() for s in state["outline"].sections])
            
            feedback = st.text_area("Feedback (Leave blank to approve as is):")
            
            col_a, col_b = st.columns(2)
            if col_a.button("✅ Approve Outline & Continue"):
                state["outline_approved"] = True
                state["outline_feedback"] = ""
                
                with st.spinner("Executing Phase 2 (Draft -> Edit -> Export)"):
                    # Continue graph execution
                    app = build_graph()
                    loop = asyncio.get_event_loop()
                    
                    draft_res = loop.run_until_complete(node_draft_article(state))
                        
                    state.update(draft_res)
                    state.update(node_edit_article(state))
                    state.update(node_export_article(state))
                    
                st.success(f"Article finished and saved to {state.get('html_path')}")
                # Move to next topic
                st.session_state.current_topic_idx += 1
                del st.session_state.current_state
                st.rerun()
                
            if col_b.button("❌ Reject & Regenerate"):
                state["outline_feedback"] = feedback
                state["outline_approved"] = False
                
                with st.spinner("Regenerating Outline..."):
                    # Just call node directly to replace outline
                    state.update(node_generate_outline(state))
                st.session_state.current_state = state
                st.rerun()

elif "processing_queue" in st.session_state and st.session_state.current_topic_idx >= st.session_state.total_topics:
    st.progress(1.0)
    st.balloons()
    st.success("🎉 All articles processed successfully! The machine will safely shut down in 3 seconds...")
    
    import threading
    import signal
    
    def auto_exit():
        time.sleep(3)
        os.kill(os.getpid(), signal.SIGTERM)
        
    threading.Thread(target=auto_exit, daemon=True).start()
