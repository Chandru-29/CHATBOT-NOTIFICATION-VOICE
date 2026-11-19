from rag_service_stndrd.embedding import embed
from rag_service_stndrd.vectorr_store import collection


# ==============================
# 1. Resolve Tables
# ==============================

def resolve_tables(query: str):

    q = query.lower()

    tables = set()

    # picklist intent
    if "picklist" in q:
        tables.update([
            "picklist",
            "picklistitem",
            "picklistview"
        ])

    # item intent
    if "item" in q:
        tables.update([
            "item",
            "skuitem"
        ])

    # stock / inventory
    if "stock" in q or "inventory" in q:
        tables.add("sulocation")

    # location intent
    if "location" in q:
        tables.add("location")

    # picklist + location → full join chain
    if "picklist" in q and "location" in q:
        tables.update([
            "picklist",
            "picklistview",
            "sulocation",
            "location"
        ])

    # grn
    if "grn" in q:
        tables.add("grn")

    # user
    if "user" in q or "assigned" in q:
        tables.add("[user]")

    return tables


# ==============================
# 2. Query Enhancement
# ==============================

def enhance_query(query: str, tables):

    context = []

    for t in tables:

        context.append(
            f"{t} schema columns relationships"
        )

    if len(tables) > 1:

        context.append(
            "join relationships foreign keys"
        )

    # MySQL time awareness
    if "last 30 days" in query.lower():

        context.append(
            "filter using "
            "cd >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        )

    return (
        query
        + " "
        + " ".join(context)
    )


# ==============================
# 3. Detect Type
# ==============================

def detect_type(doc: str):

    d = doc.lower()

    if "type: schema" in d:
        return "schema"

    if "type: relationship" in d:
        return "relationship"

    if "type: query" in d:
        return "query"

    if "type: logic" in d:
        return "logic"

    if "type: guidance" in d:
        return "guidance"

    return "general"


# ==============================
# 4. Retrieve
# ==============================

def retrieve(query: str):

    tables = resolve_tables(query)

    # ==============================
    # Detect primary table
    # ==============================

    primary_table = None

    q = query.lower()

    if "picklist" in q:

        primary_table = "picklist"

    elif "item" in q:

        primary_table = "item"

    elif "grn" in q:

        primary_table = "grn"


    # ==============================
    # Enhance query
    # ==============================

    enhanced_query = enhance_query(
        query,
        tables
    )


    # ==============================
    # Generate embedding
    # ==============================

    query_embedding = embed(
        enhanced_query
    )


    # ==============================
    # Primary table search
    # ==============================

    primary_docs = []

    if primary_table:

        try:

            primary_results = collection.query(

                query_embeddings=[
                    query_embedding
                ],

                n_results=10,

                where={
                    "table": primary_table
                }

            )

            primary_docs = (
                primary_results
                .get("documents", [[]])[0]
            )

        except Exception as e:

            print(
                "Primary table retrieval failed:",
                repr(e)
            )

            primary_docs = []


    # ==============================
    # General search
    # ==============================

    try:

        results = collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=30

        )

        docs = (
            results
            .get("documents", [[]])[0]
        )

    except Exception as e:

        print(
            "General retrieval failed:",
            repr(e)
        )

        return []


    # ==============================
    # Combine
    # ==============================

    docs = primary_docs + docs


    if not docs:

        return []


    # ==============================
    # Classification
    # ==============================

    schema_docs = []
    query_docs = []
    relationship_docs = []
    other_docs = []


    for doc in docs:

        dtype = detect_type(doc)

        if dtype == "schema":

            schema_docs.append(doc)

        elif dtype == "query":

            query_docs.append(doc)

        elif dtype == "relationship":

            relationship_docs.append(doc)

        else:

            other_docs.append(doc)


    # ==============================
    # Deterministic Assembly
    # ==============================

    final_docs = []


    # ------------------------------
    # 1. Primary table schema
    # ------------------------------

    if primary_table:

        for doc in schema_docs:

            if (
                f"table: {primary_table}"
                in doc.lower()
            ):

                final_docs.append(doc)


    # ------------------------------
    # 2. Other schemas
    # ------------------------------

    for doc in schema_docs:

        if len(final_docs) >= 4:
            break

        if doc not in final_docs:

            final_docs.append(doc)


    # ------------------------------
    # 3. Relationships
    # ------------------------------

    for doc in relationship_docs:

        if len(final_docs) >= 6:
            break

        if doc not in final_docs:

            final_docs.append(doc)


    # ------------------------------
    # 4. Query patterns
    # ------------------------------

    for doc in query_docs:

        if len(final_docs) >= 8:
            break

        if doc not in final_docs:

            final_docs.append(doc)


    # ------------------------------
    # 5. Fill remaining
    # ------------------------------

    for doc in other_docs:

        if len(final_docs) >= 8:
            break

        if doc not in final_docs:

            final_docs.append(doc)


    # ==============================
    # Remove duplicates
    # ==============================

    seen = set()

    unique_docs = []


    for doc in final_docs:

        if doc not in seen:

            unique_docs.append(doc)

            seen.add(doc)


    # ==============================
    # Final result
    # ==============================

    return unique_docs[:8]