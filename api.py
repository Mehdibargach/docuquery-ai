"""FastAPI backend for DocuQuery AI — exposes RAG pipeline via REST endpoints."""

import io
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from rag.parser import parse_file
from rag.chunker import chunk_text
from rag.embedder import embed_texts, embed_query
from rag.store import add_chunks, query, clear
from rag.generator import generate_answer

load_dotenv()

app = FastAPI(title="DocuQuery AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://docuquery-ai-5rfb.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.lovable(project)?\.com|https://.*\.lovable\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class _UploadFileAdapter:
    """Adapter to make FastAPI's UploadFile compatible with parse_file().

    parse_file() expects an object with .name, .read(), and .seek() — like
    Streamlit's UploadedFile. FastAPI's UploadFile has .filename instead of
    .name, and async methods. This adapter provides a sync interface over
    the already-read bytes.
    """

    def __init__(self, filename: str, content: bytes):
        self.name = filename
        self._buffer = io.BytesIO(content)

    def read(self) -> bytes:
        return self._buffer.read()

    def seek(self, pos: int) -> None:
        self._buffer.seek(pos)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    adapted = _UploadFileAdapter(file.filename, content)

    result = parse_file(adapted)
    if result is None:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "unknown"
        raise HTTPException(status_code=400, detail=f"Unsupported file format: .{ext}")

    if result.file_type == "pdf" and len(result.text.strip()) < 100:
        pass  # scanned PDF warning — frontend will handle

    clear()

    if result.file_type == "csv":
        chunks = result.chunks
    else:
        chunks = chunk_text(
            result.text, result.filename,
            file_type=result.file_type,
            page_map=result.page_map,
        )

    if not chunks:
        raise HTTPException(status_code=400, detail="File appears to be empty or contains no extractable text.")

    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_texts(chunk_texts)
    add_chunks(chunks, embeddings)

    return {
        "filename": result.filename,
        "file_type": result.file_type,
        "num_chunks": len(chunks),
        "status": "ready",
    }


@app.post("/query")
def query_document(req: QueryRequest):
    q_embedding = embed_query(req.question)

    t0 = time.time()
    results = query(q_embedding)
    answer = generate_answer(req.question, results)
    latency = time.time() - t0

    sources = []
    for meta in results["metadatas"][0]:
        source = {
            "chunk_index": meta.get("chunk_index"),
            "page_start": meta.get("page_start"),
            "page_end": meta.get("page_end"),
            "row_start": meta.get("row_start"),
            "row_end": meta.get("row_end"),
            "distance": None,
            "text_preview": None,
        }
        sources.append(source)

    for i, dist in enumerate(results["distances"][0]):
        if i < len(sources):
            sources[i]["distance"] = round(dist, 4)

    for i, doc in enumerate(results["documents"][0]):
        if i < len(sources):
            sources[i]["text_preview"] = doc[:150]

    return {
        "answer": answer,
        "latency": round(latency, 1),
        "sources": sources,
    }
