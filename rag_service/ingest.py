import os
import re
import sys
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from embedding import embed
    from vectorr_store import collection
    from knowledge_catalog import catalog
except ImportError:
    from rag_service.embedding import embed
    from rag_service.vectorr_store import collection
    from rag_service.knowledge_catalog import catalog

print("Using collection:", collection.name)

KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge")
print("Resolved knowledge path:", KNOWLEDGE_PATH)

# ==============================
# 1. Dynamic Known Tables Discovery
# ==============================
def get_known_tables():
    return catalog.get_known_tables()

# Kept for backward compatibility
KNOWN_TABLES = get_known_tables()


# ==============================
# 2. Resilient Smart Chunking
# ==============================
def smart_chunk(content):
    chunks = []

    # Check for table markers (supports '# TABLE:', '## TABLE:', '**# TABLE:**', '# Table:')
    table_split_pattern = r'\n(?=\s*\*{0,2}#+\s*TABLE:\s*)'
    if re.search(table_split_pattern, content, flags=re.IGNORECASE):
        # Split between global section and table sections
        raw_sections = re.split(table_split_pattern, content, flags=re.IGNORECASE)
        global_section = raw_sections[0].strip()

        # Split global rules and intent logic if both exist
        if '## INTENT MAPPING & LOGIC:' in global_section or '## INTENT MAPPING' in global_section:
            parts = re.split(r'##\s*INTENT MAPPING\s*&?\s*LOGIC:', global_section, flags=re.IGNORECASE)
            rules_chunk = parts[0].strip()
            logic_chunk = '# GLOBAL INTENT MAPPING & LOGIC\n\nTYPE: logic\n\n## INTENT MAPPING & LOGIC:\n' + parts[1].strip()
            if rules_chunk:
                chunks.append(rules_chunk)
            if logic_chunk:
                chunks.append(logic_chunk)
        else:
            if global_section:
                chunks.append(global_section)

        # Process each table section into schema, logic, relationships, queries
        for sec in raw_sections[1:]:
            sec = sec.strip()
            if not sec:
                continue
            # Remove trailing section separator '---'
            sec = re.sub(r'\n---\s*$', '', sec).strip()

            tbl_match = re.search(r'^\s*\*{0,2}#+\s*TABLE:\s*([^\r\n*]+)', sec, flags=re.MULTILINE | re.IGNORECASE)
            tbl_name = tbl_match.group(1).strip().replace("`", "").replace("[", "").replace("]", "") if tbl_match else ''
            header_prefix = f'# TABLE: {tbl_name}\n\n'

            # Split sub-sections: logic, relationships, query patterns
            split_pattern = r'\n(?=(?:COMPLETION LOGIC:|INTENT MAPPING & LOGIC:|RELATIONSHIPS:|QUERY PATTERNS:|SAMPLE QUERIES:|BUSINESS LOGIC:))'
            parts = re.split(split_pattern, sec, flags=re.IGNORECASE)

            schema_part = parts[0].strip()
            chunks.append(schema_part)

            for part in parts[1:]:
                part = part.strip()
                if not part:
                    continue
                if not re.match(r'^\s*\*{0,2}#+\s*TABLE:', part, flags=re.IGNORECASE):
                    part = header_prefix + part
                chunks.append(part)
    else:
        # Generic markdown fallback
        current_chunk = []
        for line in content.split("\n"):
            if line.startswith("# "):
                if current_chunk:
                    chunks.append("\n".join(current_chunk).strip())
                    current_chunk = []
            current_chunk.append(line)
        if current_chunk:
            chunks.append("\n".join(current_chunk).strip())

    return chunks


# ==============================
# 3. Dynamic Metadata Extraction
# ==============================
def extract_metadata(chunk: str, filename: str = ""):
    lower = chunk.lower()

    metadata = {
        "type": "general",
        "table": "",
        "tables": "",
        "filename": filename
    }

    # ---- TYPE ----
    if "type: rules" in lower:
        metadata["type"] = "rules"
    elif "type: schema" in lower or "columns:" in lower:
        metadata["type"] = "schema"
    elif "type: relationship" in lower:
        metadata["type"] = "relationship"
    elif "type: query" in lower:
        metadata["type"] = "query"
    elif "type: logic" in lower or "completion logic:" in lower:
        metadata["type"] = "logic"
    elif "type: guidance" in lower:
        metadata["type"] = "guidance"

    # ---- PRIMARY TABLE ----
    table_match = re.search(r"\*{0,2}#+\s*table:\s*([^\r\n*]+)", lower)
    if table_match:
        raw_t = table_match.group(1).strip().replace("`", "").replace("[", "").replace("]", "")
        metadata["table"] = raw_t.split()[0] if raw_t else ""

    # ---- MULTI TABLE DETECTION (Dynamic from Catalog) ----
    active_tables = catalog.get_known_tables()
    found_tables = []
    for t in active_tables:
        if re.search(rf"\b{re.escape(t)}\b", lower):
            found_tables.append(t)

    metadata["tables"] = ",".join(found_tables)

    # FINAL SAFETY (force string)
    metadata = {
        "type": str(metadata["type"]),
        "table": str(metadata["table"]),
        "tables": str(metadata["tables"]),
        "filename": str(metadata["filename"])
    }

    return metadata


# ==============================
# 4. Context-Enriched Embedding
# ==============================
def prepare_chunk_for_embedding(chunk: str, metadata: dict) -> str:
    ctype = metadata.get("type", "general")
    table = metadata.get("table", "")

    if ctype == "rules":
        return f"CRITICAL SQL GENERATION RULES, CONSTRAINTS, AND BUSINESS MAPPINGS:\n{chunk}"
    elif ctype == "logic":
        return f"BUSINESS AND COMPLETION LOGIC RULES FOR {table}:\n{chunk}" if table else f"BUSINESS AND COMPLETION LOGIC RULES:\n{chunk}"
    elif ctype == "query":
        return f"SQL QUERY PATTERNS AND EXAMPLE QUERIES FOR {table}:\n{chunk}"
    elif ctype == "relationship":
        return f"DATABASE RELATIONSHIPS AND FOREIGN KEY JOINS FOR {table}:\n{chunk}"
    elif ctype == "schema":
        return f"DATABASE TABLE SCHEMA AND COLUMNS FOR {table}:\n{chunk}"

    return chunk


# ==============================
# 5. File-Level Helpers & Ingestion
# ==============================
def delete_file_chunks(filename: str) -> int:
    """
    Deletes all existing chunks for a given file from the Chroma collection.
    Matches by metadata 'filename' or ID prefix '{filename}_'.
    """
    try:
        matched_ids = set()

        # 1. Search by metadata
        try:
            res = collection.get(where={"filename": filename})
            if res and res.get("ids"):
                matched_ids.update(res["ids"])
        except Exception:
            pass

        # 2. Safety fallback: Search by ID prefix (ids are formatted as f"{filename}_{i}")
        try:
            all_data = collection.get()
            for cid in all_data.get("ids", []):
                if cid.startswith(f"{filename}_"):
                    matched_ids.add(cid)
        except Exception:
            pass

        if matched_ids:
            collection.delete(ids=list(matched_ids))
            print(f"Deleted {len(matched_ids)} existing chunks for '{filename}'")
            return len(matched_ids)
        return 0
    except Exception as e:
        print(f"Error deleting chunks for {filename}:", e)
        return 0


def ingest_single_file(filename: str, clean_file_chunks: bool = True) -> dict:
    """
    Ingests or updates a single markdown knowledge file in the Chroma collection.
    """
    file_path = os.path.join(KNOWLEDGE_PATH, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge file '{filename}' not found at {file_path}")

    if clean_file_chunks:
        delete_file_chunks(filename)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pre-reload catalog to discover any new tables immediately
    catalog.reload(force=True)

    chunks = smart_chunk(content)
    print(f"\nProcessing '{filename}': {len(chunks)} chunks found")

    inserted_count = 0
    for i, chunk in enumerate(chunks):
        try:
            metadata = extract_metadata(chunk, filename=filename)
            embedding_text = prepare_chunk_for_embedding(chunk, metadata)
            embedding = embed(embedding_text)

            # Upsert chunk into collection
            collection.upsert(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[f"{filename}_{i}"]
            )

            inserted_count += 1
            if i < 4 or i % 30 == 0:
                print(f"  [{filename} Chunk {i:3d}] type={metadata['type']:<12} table={metadata['table']:<20}")

        except Exception as e:
            print(f"Error inserting chunk {i} of {filename}:", e)

    return {
        "filename": filename,
        "chunks_inserted": inserted_count,
        "total_db_chunks": collection.count()
    }


def ingest_documents(clean_existing: bool = True) -> dict:
    """
    Full ingestion pipeline for all markdown files in the knowledge directory.
    """
    print("\nKnowledge files:", os.listdir(KNOWLEDGE_PATH))

    if clean_existing:
        try:
            existing_count = collection.count()
            if existing_count > 0:
                print(f"Clearing existing {existing_count} documents from collection for fresh ingestion...")
                all_ids = collection.get().get("ids", [])
                if all_ids:
                    collection.delete(ids=all_ids)
                print("Collection cleared.")
        except Exception as e:
            print("Note on clearing collection:", e)

    processed_files = []
    total_inserted = 0

    for file in os.listdir(KNOWLEDGE_PATH):
        if file.endswith(".md") or file.endswith(".markdown"):
            result = ingest_single_file(file, clean_file_chunks=not clean_existing)
            processed_files.append(file)
            total_inserted += result["chunks_inserted"]

    print("\nKnowledge ingested successfully!")
    print("Total chunks inserted:", total_inserted)
    print("Total documents stored in collection:", collection.count())

    return {
        "status": "success",
        "processed_files": processed_files,
        "total_chunks_inserted": total_inserted,
        "total_db_chunks": collection.count()
    }


def get_knowledge_stats() -> dict:
    """
    Returns metadata about files currently stored in KNOWLEDGE_PATH
    along with chunk count in ChromaDB.
    """
    files_info = []
    if os.path.exists(KNOWLEDGE_PATH):
        all_db_data = collection.get(include=["metadatas"])
        all_metas = all_db_data.get("metadatas", [])
        all_ids = all_db_data.get("ids", [])

        # Count chunks per file
        chunk_count_map = {}
        for m, cid in zip(all_metas, all_ids):
            fname = m.get("filename") if m else ""
            if not fname and "_" in cid:
                fname = cid.rsplit("_", 1)[0]
            if fname:
                chunk_count_map[fname] = chunk_count_map.get(fname, 0) + 1

        for f in sorted(os.listdir(KNOWLEDGE_PATH)):
            if f.endswith(".md") or f.endswith(".markdown"):
                fpath = os.path.join(KNOWLEDGE_PATH, f)
                stat = os.stat(fpath)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                files_info.append({
                    "filename": f,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified_at": mtime,
                    "chunks_in_db": chunk_count_map.get(f, 0)
                })

    return {
        "total_files": len(files_info),
        "total_db_chunks": collection.count(),
        "files": files_info
    }


if __name__ == "__main__":
    ingest_documents()