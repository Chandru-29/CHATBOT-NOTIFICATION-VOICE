from sql_validator import sql_validator


def test(name, sql, tables):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    result = sql_validator.validate(
        sql,
        retrieved_tables=tables
    )

    print("VALID:", result["valid"])
    print("TABLES:", result.get("tables", []))

    if result["errors"]:

        print("ERRORS:")

        for error in result["errors"]:
            print(" -", error)


# ============================================================
# VALID OPEN PICKLIST
# ============================================================

test(
    "VALID OPEN PICKLIST",
    """
    SELECT
        picklistCode,
        status
    FROM SS_PICKLIST
    WHERE status IN (1,2,3,4)
      AND isDeleted = 0
    LIMIT 20
    """,
    ["SS_PICKLIST"]
)


# ============================================================
# INVALID COLUMN
# ============================================================

test(
    "INVALID COLUMN",
    """
    SELECT
        picklistCode,
        wrongColumn
    FROM SS_PICKLIST
    WHERE status IN (1,2,3,4)
      AND isDeleted = 0
    LIMIT 20
    """,
    ["SS_PICKLIST"]
)


# ============================================================
# INVALID TABLE
# ============================================================

test(
    "INVALID TABLE",
    """
    SELECT *
    FROM STOCK
    LIMIT 20
    """,
    ["STOCK"]
)


# ============================================================
# VALID JOIN
# ============================================================

test(
    "VALID JOIN",
    """
    SELECT DISTINCT
        p.picklistCode,
        u.name
    FROM SS_PICKLIST p
    JOIN `user` u
        ON p.assignedUser = u.userId
    WHERE p.isDeleted = 0
      AND u.isDeleted = 0
    LIMIT 20
    """,
    ["SS_PICKLIST", "user"]
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 60)
print("SQL VALIDATOR TEST COMPLETED")
print("=" * 60)