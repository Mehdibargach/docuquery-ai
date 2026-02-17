import streamlit as st
from dotenv import load_dotenv

from rag.parser import parse_file
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
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "csv"])

    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing..."):
                # Parse file (routes to correct parser)
                result = parse_file(uploaded_file)

                # Check for unsupported file type
                if result is None:
                    ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else "unknown"
                    st.error(f"Unsupported file format: .{ext}. Please upload a .txt, .pdf, or .csv file.")
                    st.stop()

                filename = result.filename

                # Warn if PDF has very little text (likely scanned)
                if result.file_type == "pdf" and len(result.text.strip()) < 100:
                    st.warning("This PDF contains very little extractable text. "
                               "It may be a scanned/image-based PDF.")

                # Clear previous data
                clear()

                # Chunk (CSV provides pre-built chunks)
                if result.file_type == "csv":
                    chunks = result.chunks
                else:
                    chunks = chunk_text(result.text, result.filename,
                                        file_type=result.file_type,
                                        page_map=result.page_map)

                # Check for empty file
                if not chunks:
                    st.warning("This file appears to be empty or contains no extractable text. "
                               "Please upload a file with content.")
                    st.stop()

                # Embed
                chunk_texts = [c["text"] for c in chunks]
                embeddings = embed_texts(chunk_texts)

                # Store
                add_chunks(chunks, embeddings)

                st.session_state["doc_loaded"] = True
                st.session_state["filename"] = filename
                st.session_state["num_chunks"] = len(chunks)
                st.session_state["file_type"] = result.file_type

            st.success(f"Loaded **{filename}** ({len(chunks)} chunks)")

    if st.session_state.get("doc_loaded"):
        st.info(
            f"Current: **{st.session_state['filename']}** "
            f"({st.session_state['num_chunks']} chunks)"
        )

# --- Main: Q&A ---
if not st.session_state.get("doc_loaded"):
    st.info("Upload a document (.txt, .pdf, or .csv) in the sidebar to get started.")
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
                file_type = meta.get("file_type", "txt")

                if file_type == "pdf":
                    page_start = meta.get("page_start")
                    page_end = meta.get("page_end")
                    if page_start and page_end and page_start != page_end:
                        location = f"Pages {page_start}-{page_end}"
                    elif page_start:
                        location = f"Page {page_start}"
                    else:
                        location = ""
                    label = f"**Chunk {meta['chunk_index']}** — {location} (distance: {dist:.4f})"

                elif file_type == "csv":
                    row_start = meta.get("row_start")
                    row_end = meta.get("row_end")
                    label = f"**Chunk {meta['chunk_index']}** — Rows {row_start}-{row_end} (distance: {dist:.4f})"

                else:
                    label = f"**Chunk {meta['chunk_index']}** (distance: {dist:.4f})"

                st.markdown(label)
                st.text(doc[:300] + ("..." if len(doc) > 300 else ""))
                st.divider()
