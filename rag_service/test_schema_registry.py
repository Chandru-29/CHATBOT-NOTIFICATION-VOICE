from schema_registry import schema_registry


print("\n" + "=" * 60)
print("SCHEMA REGISTRY TEST")
print("=" * 60)


# ============================================================
# TABLES
# ============================================================

print("\nTABLES:")

tables = schema_registry.get_all_tables()

print(tables)

print(f"\nTotal tables: {len(tables)}")


# ============================================================
# SS_PICKLIST COLUMNS
# ============================================================

print("\nSS_PICKLIST COLUMNS:")

picklist_columns = schema_registry.get_columns("SS_PICKLIST")

print(picklist_columns)

print(
    f"\nTotal SS_PICKLIST columns: "
    f"{len(picklist_columns)}"
)


# ============================================================
# TABLE CHECK
# ============================================================

print("\nTABLE CHECK:")

print(
    "SS_PICKLIST exists:",
    schema_registry.table_exists("SS_PICKLIST")
)


# ============================================================
# COLUMN CHECK
# ============================================================

print("\nCOLUMN CHECK:")

print(
    "SS_PICKLIST.status exists:",
    schema_registry.column_exists(
        "SS_PICKLIST",
        "status"
    )
)


# ============================================================
# INVALID COLUMN
# ============================================================

print("\nINVALID COLUMN:")

print(
    "SS_PICKLIST.wrongColumn exists:",
    schema_registry.column_exists(
        "SS_PICKLIST",
        "wrongColumn"
    )
)


# ============================================================
# RELATIONSHIPS
# ============================================================

print("\nRELATIONSHIPS:")

relationships = schema_registry.get_relationships()

if relationships:

    for relationship in relationships:
        print(relationship)

else:
    print("No relationships found.")


# ============================================================
# JOIN PATHS
# ============================================================

print("\nJOIN PATHS:")

join_paths = schema_registry.get_join_paths()

if join_paths:

    for join_path in join_paths:
        print(join_path)

else:
    print("No join paths found.")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Tables        : {len(tables)}")
print(f"Relationships : {len(relationships)}")
print(f"Join Paths    : {len(join_paths)}")

print("=" * 60)