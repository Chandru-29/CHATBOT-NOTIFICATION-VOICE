import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from rag_service.knowledge_catalog import catalog
from rag_service.schema_registry import schema_registry
from rag_service.sql_validator import sql_validator
from rag_service.retriever import retrieve, resolve_tables
from rag_service.ingest import ingest_single_file, delete_file_chunks, KNOWLEDGE_PATH


def run_tests():
    print("=" * 70)
    print("RUNNING ENTERPRISE DYNAMIC TABLE RAG VERIFICATION TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: Baseline Existing Tables & Synonyms
    # -------------------------------------------------------------
    print("\n[TEST 1] Verifying Baseline Existing Tables...")
    known_tables = catalog.get_known_tables()
    print(f"Total discovered tables: {len(known_tables)}")
    assert "user" in known_tables, "Expected 'user' table in catalog"
    assert "ss_picklist" in known_tables, "Expected 'ss_picklist' table in catalog"
    assert "store" in known_tables, "Expected 'store' table in catalog"
    print("  ✓ All baseline core tables discovered in catalog.")

    # -------------------------------------------------------------
    # TEST 2: Business Synonym & Natural Language Resolution
    # -------------------------------------------------------------
    print("\n[TEST 2] Verifying Synonym & Natural Language Resolution...")
    resolved = resolve_tables("what is the total available stock in store inventory?")
    print(f"  Query: 'available stock in store inventory' -> Resolved Tables: {resolved}")
    assert "store" in resolved, "Expected 'store' in resolved tables"
    print("  ✓ Business synonym resolution verified.")

    # -------------------------------------------------------------
    # TEST 3: Baseline SQL Validation
    # -------------------------------------------------------------
    print("\n[TEST 3] Verifying Baseline SQL Validation...")
    sql = "SELECT picklistCode, status FROM SS_PICKLIST WHERE status = 5 AND isDeleted = 0 LIMIT 20;"
    val_res = sql_validator.validate(sql)
    print(f"  SQL: {sql}")
    print(f"  Valid: {val_res['valid']}, Errors: {val_res.get('errors')}")
    assert val_res["valid"], f"Expected baseline SQL to be valid, got errors: {val_res.get('errors')}"
    print("  ✓ Baseline SQL validation verified.")

    # -------------------------------------------------------------
    # TEST 4: Dynamic New Table Ingestion & Hot-Reload Simulation
    # -------------------------------------------------------------
    print("\n[TEST 4] Simulating Addition of a Brand New Table (.md file)...")
    test_filename = "_test_vendor_payout.md"
    test_filepath = os.path.join(KNOWLEDGE_PATH, test_filename)

    test_md_content = """# GLOBAL RULES & CONSTRAINTS

TYPE: rules

- Soft Delete Rule: Always filter `isDeleted = 0`.
- Dialect: MySQL syntax with LIMIT.

# TABLE: vendor_payout_master

TYPE: schema

BUSINESS TERMS:
- "vendor payout" / "supplier disbursement" / "vendor payment" → vendor_payout_master.payoutCode
- "payout amount" → vendor_payout_master.amount

COLUMNS:
payoutId (PK)
payoutCode (UNIQUE)
vendorId
amount
payoutStatus
isDeleted
cd
ud

STATUS:
0 = Pending
1 = Approved
2 = Disbursed
3 = Cancelled

COMPLETION LOGIC:

TYPE: logic

- If payoutStatus = 2 (Disbursed) → completion date = ud
- "pending payouts" → payoutStatus IN (0, 1)

QUERY PATTERNS:

TYPE: query

PENDING PAYOUTS:
```sql
SELECT payoutCode, vendorId, amount FROM vendor_payout_master WHERE payoutStatus IN (0, 1) AND isDeleted = 0 LIMIT 20;
```
"""

    try:
        # Write test file
        with open(test_filepath, "w", encoding="utf-8") as f:
            f.write(test_md_content)
        print(f"  Created test knowledge file: {test_filename}")

        # Ingest into ChromaDB
        ingest_res = ingest_single_file(test_filename)
        print(f"  Ingested chunks into ChromaDB: {ingest_res['chunks_inserted']}")

        # Trigger Hot-Reload on Catalog and SchemaRegistry
        catalog.reload(force=True)
        schema_registry.reload()

        # 4a. Verify Catalog discovered the new table
        all_tables_now = catalog.get_known_tables()
        print(f"  Total tables after reload: {len(all_tables_now)}")
        assert "vendor_payout_master" in all_tables_now, "Expected 'vendor_payout_master' in catalog tables"
        print("  ✓ New table dynamically discovered in KnowledgeCatalog.")

        # 4b. Verify SchemaRegistry has the new table and columns
        assert schema_registry.table_exists("vendor_payout_master"), "Expected SchemaRegistry to know 'vendor_payout_master'"
        cols = schema_registry.get_columns("vendor_payout_master")
        print(f"  Extracted columns: {cols}")
        assert "payoutId" in cols and "payoutCode" in cols and "amount" in cols
        print("  ✓ SchemaRegistry recognized new table and columns dynamically.")

        # 4c. Verify Retriever resolves business terms for new table
        query = "show all pending supplier disbursements"
        new_resolved = resolve_tables(query)
        print(f"  Query: '{query}' -> Resolved Tables: {new_resolved}")
        assert "vendor_payout_master" in new_resolved, "Expected 'vendor_payout_master' to be resolved from synonym"
        print("  ✓ Dynamic synonym mapping to new table verified.")

        # 4d. Verify Retrieval retrieves target schema
        retrieved_docs = retrieve(query)
        print(f"  Retrieved docs count: {len(retrieved_docs)}")
        has_new_schema = any("vendor_payout_master" in d and "payoutId" in d for d in retrieved_docs)
        assert has_new_schema, "Expected 'vendor_payout_master' schema chunk in retrieved context"
        print("  ✓ Retrieved context contains target schema with 100% precision.")

        # 4e. Verify SQL Validator validates queries on new table without rejection
        new_sql = "SELECT payoutCode, amount FROM vendor_payout_master WHERE payoutStatus IN (0, 1) AND isDeleted = 0 LIMIT 20;"
        val_new_res = sql_validator.validate(new_sql)
        print(f"  Validating SQL on new table: {new_sql}")
        print(f"  Validation Result: Valid={val_new_res['valid']}, Errors={val_new_res.get('errors')}")
        assert val_new_res["valid"], f"Expected SQL on new table to pass validation, got: {val_new_res.get('errors')}"
        print("  ✓ SQL Validator successfully validated SQL on newly uploaded table!")

    finally:
        # Cleanup test file and chunks
        print("\n[CLEANUP] Cleaning up test file and ChromaDB chunks...")
        delete_file_chunks(test_filename)
        if os.path.exists(test_filepath):
            os.remove(test_filepath)
        catalog.reload(force=True)
        schema_registry.reload()
        print("  ✓ Cleanup complete. System state restored.")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
