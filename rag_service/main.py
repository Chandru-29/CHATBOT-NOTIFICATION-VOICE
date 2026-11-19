import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from rag_service.retriever import retrieve
from rag_service.ingest import (
    KNOWLEDGE_PATH,
    ingest_single_file,
    ingest_documents,
    get_knowledge_stats
)
from rag_service.knowledge_catalog import catalog
from rag_service.schema_registry import schema_registry

app = FastAPI(title="Mobillor RAG Service")


@app.post("/retrieve")
def retrieve_context(data: dict):
    query = data.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    docs = retrieve(query)
    return {
        "context": docs
    }


@app.post("/api/knowledge/upload")
async def upload_knowledge_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more .md files and incrementally ingest them into ChromaDB,
    then automatically hot-reload knowledge catalog and schema registry.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    os.makedirs(KNOWLEDGE_PATH, exist_ok=True)
    uploaded_files = []
    total_chunks_added = 0

    for file in files:
        filename = os.path.basename(file.filename)
        if not (filename.endswith(".md") or filename.endswith(".markdown")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for '{filename}'. Only .md or .markdown files are allowed."
            )

        destination_path = os.path.join(KNOWLEDGE_PATH, filename)
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            result = ingest_single_file(filename)
            uploaded_files.append(filename)
            total_chunks_added += result["chunks_inserted"]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ingest '{filename}': {str(e)}"
            )

    # Hot-reload in-memory catalog and schema registry
    try:
        catalog.reload(force=True)
        schema_registry.reload()
    except Exception as e:
        print("Warning during hot-reload:", e)

    stats = get_knowledge_stats()
    return {
        "status": "success",
        "message": f"Successfully uploaded and ingested {len(uploaded_files)} file(s). Schema & Catalog hot-reloaded.",
        "uploaded_files": uploaded_files,
        "chunks_added": total_chunks_added,
        "total_db_chunks": stats["total_db_chunks"],
        "active_tables_count": len(catalog.get_known_tables()),
        "active_tables": catalog.get_known_tables()
    }


@app.get("/api/knowledge/files")
def get_knowledge_files():
    """
    Returns the list of current .md files in knowledge directory and total chunks in DB.
    """
    try:
        return get_knowledge_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/tables")
def get_indexed_tables():
    """
    Returns all active database tables and their registered business synonyms.
    """
    try:
        all_tables = catalog.get_known_tables()
        term_map = {}
        for terms, tbls in catalog.get_business_term_map().items():
            term_map[" / ".join(terms)] = tbls

        return {
            "total_tables": len(all_tables),
            "tables": all_tables,
            "business_terms_count": len(term_map),
            "sample_business_terms": dict(list(term_map.items())[:15])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/reindex-all")
def reindex_all_knowledge():
    """
    Clears the existing collection and re-indexes all .md files in the knowledge folder,
    then hot-reloads knowledge catalog and schema registry.
    """
    try:
        result = ingest_documents(clean_existing=True)
        catalog.reload(force=True)
        schema_registry.reload()
        return {
            "status": "success",
            "message": "Full re-indexing and hot-reload completed successfully.",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
