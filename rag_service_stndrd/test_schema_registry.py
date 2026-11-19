from schema_registry import schema_registry


print("\nTABLES:")
print(schema_registry.get_all_tables())


print("\nPICKLIST COLUMNS:")
print(
    schema_registry.get_columns("PICKLIST")
)


print("\nTABLE CHECK:")
print(
    schema_registry.table_exists("PICKLIST")
)


print("\nCOLUMN CHECK:")
print(
    schema_registry.column_exists(
        "PICKLIST",
        "status"
    )
)


print("\nINVALID COLUMN:")
print(
    schema_registry.column_exists(
        "PICKLIST",
        "wrongColumn"
    )
)


print("\nRELATIONSHIPS:")
for relationship in schema_registry.get_relationships():
    print(relationship)