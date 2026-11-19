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
    print("TABLES:", result["tables"])

    if result["errors"]:
        print("ERRORS:")

        for error in result["errors"]:
            print(" -", error)


# ============================================================
# VALID
# ============================================================

test(
    "VALID OPEN PICKLIST",
    """
    SELECT TOP 20
        picklistCode,
        status
    FROM PICKLIST
    WHERE status IN (1,2,3,4)
      AND isDeleted = 0
    """,
    ["PICKLIST"]
)


# ============================================================
# INVALID COLUMN
# ============================================================

test(
    "INVALID COLUMN",
    """
    SELECT TOP 20
        picklistCode,
        wrongColumn
    FROM PICKLIST
    WHERE status IN (1,2,3,4)
      AND isDeleted = 0
    """,
    ["PICKLIST"]
)


# ============================================================
# INVALID TABLE
# ============================================================

test(
    "INVALID TABLE",
    """
    SELECT TOP 20 *
    FROM STOCK
    """,
    ["STOCK"]
)


# ============================================================
# VALID JOIN
# ============================================================

test(
    "VALID JOIN",
    """
    SELECT DISTINCT TOP 20
        p.picklistCode,
        u.name
    FROM PICKLIST p
    JOIN [user] u
        ON p.assignedUser = u.userId
    WHERE p.isDeleted = 0
      AND u.isDeleted = 0
    """,
    ["PICKLIST", "[user]"]
)