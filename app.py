import streamlit as st
from dotenv import load_dotenv

from rag.chunker import chunk_text
from rag.embedder import embed_texts, embed_query
from rag.store import add_chunks, query, clear
from rag.generator import generate_answer

load_dotenv()

st.set_page_config(page_title="DocuQuery AI", page_icon="📄")
st.title("DocuQuery AI")
st.caption("Upload a document. Ask questions. Get answers with citations.")

# --- Sidebar: Upload ---
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])

    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing..."):
                # Read file
                text = uploaded_file.read().decode("utf-8")
                filename = uploaded_file.name

                # Clear previous data
                clear()

                # Chunk
                chunks = chunk_text(text, filename)

                # Embed
                chunk_texts = [c["text"] for c in chunks]
                embeddings = embed_texts(chunk_texts)

                # Store
                add_chunks(chunks, embeddings)

                st.session_state["doc_loaded"] = True
                st.session_state["filename"] = filename
                st.session_state["num_chunks"] = len(chunks)

            st.success(f"Loaded **{filename}** ({len(chunks)} chunks)")

    if st.session_state.get("doc_loaded"):
        st.info(
            f"Current: **{st.session_state['filename']}** "
            f"({st.session_state['num_chunks']} chunks)"
        )

# --- Main: Q&A ---
if not st.session_state.get("doc_loaded"):
    st.info("Upload a .txt file in the sidebar to get started.")
else:
    question = st.text_input("Ask a question about your document:")

    if question:
        with st.spinner("Searching and generating answer..."):
            # Embed question
            q_embedding = embed_query(question)

            # Search
            results = query(q_embedding)

            # Generate
            answer = generate_answer(question, results)

        st.markdown("### Answer")
        st.markdown(answer)

        # Show retrieved chunks for transparency
        with st.expander("Retrieved chunks (debug)"):
            for i, (doc, meta, dist) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                st.markdown(
                    f"**Chunk {meta['chunk_index']}** "
                    f"(distance: {dist:.4f})"
                )
                st.text(doc[:300] + ("..." if len(doc) > 300 else ""))
                st.divider()
