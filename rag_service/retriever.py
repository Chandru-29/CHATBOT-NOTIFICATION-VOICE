import os
import re
import sys

try:
    from rag_service.embedding import embed
    from rag_service.vectorr_store import collection
    from rag_service.knowledge_catalog import catalog
except ImportError:
    from embedding import embed
    from vectorr_store import collection
    from knowledge_catalog import catalog


# ==============================
# 1. Dynamic Table & Synonym Resolution
# ==============================
def resolve_tables(query: str) -> set:
    """
    Extracts relevant table names from user query using both
    dynamically extracted business synonym mappings and table names from catalog.
    Handles singular, plural, and space/underscore variations.
    """
    q = query.lower()
    # Also create a normalized version where underscores and hyphens are spaces
    q_normalized = re.sub(r'[_\\-]', ' ', q)
    tables = set()

    # 1. Check dynamic business term synonyms
    dynamic_terms = catalog.get_business_term_map()
    for keywords, mapped_tables in dynamic_terms.items():
        for kw in keywords:
            kw_clean = kw.lower().strip()
            if not kw_clean:
                continue

            # Stem trailing 's' for flexible singular/plural matching
            kw_stem = kw_clean[:-1] if kw_clean.endswith('s') and len(kw_clean) > 3 else kw_clean
            pattern = rf"\b{re.escape(kw_stem)}(?:s|es)?\b"

            if re.search(pattern, q) or re.search(pattern, q_normalized):
                tables.update(mapped_tables)
                break

    # 2. Check dynamic known tables (both exact and space-separated variations)
    for tbl in catalog.get_known_tables():
        tbl_clean = tbl.lower().strip()
        tbl_spaced = tbl_clean.replace("_", " ")

        # Match exact table name (or plural e.g. users -> user)
        tbl_stem = tbl_clean[:-1] if tbl_clean.endswith('s') and len(tbl_clean) > 3 else tbl_clean
        tbl_pattern = rf"\b{re.escape(tbl_stem)}(?:s|es)?\b"

        if re.search(tbl_pattern, q):
            tables.add(tbl_clean)
        elif tbl_spaced != tbl_clean and re.search(rf"\b{re.escape(tbl_spaced)}(?:s|es)?\b", q_normalized):
            tables.add(tbl_clean)

    return tables


# ==============================
# 2. Query Enhancement 
# ==============================
def enhance_query(query: str, tables):
    """
    Enhances query with vocabulary that mirrors prepare_chunk_for_embedding
    in ingest.py and enforces MySQL dialect conventions.
    """
    context = []

    for t in tables:
        context.append(f"DATABASE TABLE SCHEMA AND COLUMNS FOR {t}")

    if len(tables) > 1:
        context.append("DATABASE RELATIONSHIPS AND FOREIGN KEY JOINS")

    q = query.lower()

    # MySQL date filtering
    if "last 30 days" in q or "past month" in q:
        context.append("filter using cd >= NOW() - INTERVAL 30 DAY")
    elif "last 7 days" in q or "past week" in q:
        context.append("filter using cd >= NOW() - INTERVAL 7 DAY")

    # Status intent mappings from nerolac_new.md
    if "open" in q or "pending" in q:
        context.append("status IN (0, 1, 2) open pending")
    elif "completed" in q or "finished" in q:
        context.append("status = 5 completed")

    # Expiry / shelf life handling
    if "expiry" in q or "expiration" in q:
        context.append("store.shelfLife date filter")

    return query + " " + " ".join(context)


# ==============================
# 3. Detect Type (Metadata-first with robust fallback)
# ==============================
def detect_type(doc: str, meta: dict = None):
    if meta and "type" in meta and meta["type"]:
        return meta["type"]

    d = doc.lower()
    if "type: rules" in d:
        return "rules"
    if "type: logic" in d:
        return "logic"
    if "type: schema" in d:
        return "schema"
    if "type: relationship" in d:
        return "relationship"
    if "type: query" in d:
        return "query"
    if "type: guidance" in d:
        return "guidance"

    return "general"


# ==============================
# 4. Pinned Core Rules & Logic Fetchers
# ==============================
def get_global_rules_and_logic():
    """
    Fetches the critical Global Rules and Global Intent Logic
    directly from Chroma. Guarantees soft deletes (isDeleted = 0), MySQL syntax,
    and reserved table backtick formatting.
    """
    docs = []
    try:
        rules_res = collection.get(where={"type": "rules"}, limit=1)
        if rules_res and rules_res.get("documents"):
            docs.extend(rules_res["documents"])
    except Exception as e:
        print("Note: Could not fetch pinned rules:", e)

    try:
        # Fetch the global intent mapping chunk (table is empty string)
        logic_res = collection.get(
            where={"$and": [{"type": "logic"}, {"table": ""}]},
            limit=1
        )
        if logic_res and logic_res.get("documents"):
            docs.extend(logic_res["documents"])
    except Exception as e:
        print("Note: Could not fetch pinned logic:", e)

    return docs


# ==============================
# 5. Targeted Schemas & Relationships Fetcher
# ==============================
def get_targeted_table_docs(tables: set):
    """
    Directly fetches schema, relationship, logic, and query chunks for each resolved table,
    guaranteeing that every target table's schema and constraints are retrieved.
    """
    schemas = []
    relationships = []
    logics = []
    queries = []

    if not tables:
        return schemas, relationships, logics, queries

    for tbl in tables:
        tbl_candidates = [tbl, tbl.lower(), tbl.upper()]

        # 1. Fetch Schema for this specific table
        for candidate in tbl_candidates:
            try:
                res = collection.get(
                    where={"$and": [{"table": candidate}, {"type": "schema"}]},
                    limit=1
                )
                if res and res.get("documents"):
                    schemas.extend(res["documents"])
                    break
            except Exception:
                pass

        # 2. Fetch Relationships for this specific table
        for candidate in tbl_candidates:
            try:
                res = collection.get(
                    where={"$and": [{"table": candidate}, {"type": "relationship"}]},
                    limit=1
                )
                if res and res.get("documents"):
                    relationships.extend(res["documents"])
                    break
            except Exception:
                pass

        # 3. Fetch Logic for this specific table
        for candidate in tbl_candidates:
            try:
                res = collection.get(
                    where={"$and": [{"table": candidate}, {"type": "logic"}]},
                    limit=1
                )
                if res and res.get("documents"):
                    logics.extend(res["documents"])
                    break
            except Exception:
                pass

        # 4. Fetch Query Patterns for this specific table
        for candidate in tbl_candidates:
            try:
                res = collection.get(
                    where={"$and": [{"table": candidate}, {"type": "query"}]},
                    limit=1
                )
                if res and res.get("documents"):
                    queries.extend(res["documents"])
                    break
            except Exception:
                pass

    return schemas, relationships, logics, queries


# ==============================
# 6. Clean & Optimized Retrieve Function
# ==============================
def retrieve(query: str):
    tables = resolve_tables(query)
    enhanced_query = enhance_query(query, tables)
    query_embedding = embed(enhanced_query)

    # ==============================
    # 1. PINNED GLOBAL RULES & LOGIC
    # ==============================
    pinned_docs = get_global_rules_and_logic()

    # ==============================
    # 2. TARGETED MULTI-TABLE FETCH
    # ==============================
    targeted_schemas, targeted_rels, targeted_logics, targeted_queries = get_targeted_table_docs(tables)

    # ==============================
    # 3. GENERAL VECTOR SEARCH
    # ==============================
    vector_docs = []
    vector_metas = []
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=20,
            include=["documents", "metadatas", "distances"]
        )
        vector_docs = results.get("documents", [[]])[0]
        vector_metas = results.get("metadatas", [[]])[0]
    except Exception as e:
        print("Vector query note:", e)

    # ==============================
    # 4. CLASSIFY VECTOR RESULTS USING STORED METADATA
    # ==============================
    vector_schemas = []
    vector_relationships = []
    vector_queries = []
    vector_logic = []
    vector_others = []

    for doc, meta in zip(vector_docs, vector_metas):
        dtype = detect_type(doc, meta)
        if dtype == "schema":
            vector_schemas.append(doc)
        elif dtype == "relationship":
            vector_relationships.append(doc)
        elif dtype == "query":
            vector_queries.append(doc)
        elif dtype in ("logic", "rules"):
            vector_logic.append(doc)
        else:
            vector_others.append(doc)

    # ==============================
    # 5. BALANCED DETERMINISTIC ASSEMBLY
    # ==============================
    final_docs = []

    # Priority 1: Global Rules & Constraints (1 doc)
    final_docs.extend(pinned_docs)

    # Priority 2: Target table schemas first, then fill from vector search (max 3 docs)
    combined_schemas = targeted_schemas + [s for s in vector_schemas if s not in targeted_schemas]
    final_docs.extend(combined_schemas[:3])

    # Priority 3: Table-Specific Intent & Business Logic (max 1 doc)
    combined_logic = targeted_logics + [l for l in vector_logic if l not in targeted_logics]
    final_docs.extend(combined_logic[:1])

    # Priority 4: Foreign Key relationships (max 1 doc)
    combined_rels = targeted_rels + [r for r in vector_relationships if r not in targeted_rels]
    final_docs.extend(combined_rels[:1])

    # Priority 5: SQL Query Patterns (targeted first, then vector search, max 1 doc)
    combined_queries = targeted_queries + [q for q in vector_queries if q not in targeted_queries]
    final_docs.extend(combined_queries[:1])

    # Priority 6: Fill remaining slots up to 8 documents max
    remaining_candidates = (
        combined_schemas[3:] +
        combined_logic[1:] +
        combined_rels[1:] +
        combined_queries[1:] +
        vector_others
    )
    for doc in remaining_candidates:
        if len(final_docs) >= 8:
            break
        final_docs.append(doc)

    # Final deduplication preserving priority order
    seen_final = set()
    final_unique = []
    for doc in final_docs:
        if doc not in seen_final:
            final_unique.append(doc)
            seen_final.add(doc)

    return final_unique[:8]