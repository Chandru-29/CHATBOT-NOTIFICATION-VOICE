import sqlglot
from sqlglot import exp

from rag_service_stndrd.schema_registry import schema_registry

class SQLValidator:

    def __init__(self, registry):
        self.registry = registry

    def validate(self, sql: str, retrieved_tables=None):

        errors = []

        if not sql or not sql.strip():
            return {
                "valid": False,
                "errors": ["Empty SQL"]
            }

        sql = sql.strip()

        # =========================================================
        # 1. READ-ONLY CHECK
        # =========================================================

        try:
            statements = sqlglot.parse(sql, dialect="tsql")
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"SQL syntax error: {str(e)}"]
            }

        if len(statements) != 1:
            errors.append("Only one SQL statement is allowed.")

        expression = statements[0]

        if not isinstance(expression, exp.Select):
            errors.append(
                "Only SELECT queries are allowed."
            )

        # =========================================================
        # 2. FORBIDDEN OPERATIONS
        # =========================================================

        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.Merge,
            exp.TruncateTable,
        )

        for node in expression.walk():

            if isinstance(node, forbidden):
                errors.append(
                    f"Forbidden SQL operation: "
                    f"{type(node).__name__}"
                )

        # =========================================================
        # 3. EXTRACT TABLES
        # =========================================================

        sql_tables = set()

        for table in expression.find_all(exp.Table):

            table_name = table.name

            if table_name:
                sql_tables.add(
                    table_name.replace("[", "")
                    .replace("]", "")
                    .lower()
                )

        # =========================================================
        # 4. VALIDATE TABLES AGAINST GLOBAL SCHEMA
        # =========================================================

        for table in sql_tables:

            if not self.registry.table_exists(table):

                errors.append(
                    f"Table does not exist in schema: {table}"
                )

        # =========================================================
        # 5. VALIDATE AGAINST RAG RETRIEVED TABLES
        # =========================================================

        if retrieved_tables:

            normalized_retrieved = {
                t.replace("[", "")
                .replace("]", "")
                .lower()
                for t in retrieved_tables
            }

            for table in sql_tables:

                if table not in normalized_retrieved:

                    errors.append(
                        f"Table '{table}' was not present "
                        f"in retrieved RAG knowledge."
                    )

        # =========================================================
        # 6. COLUMN VALIDATION
        # =========================================================

        aliases = {}

        for table in expression.find_all(exp.Table):

            table_name = (
                table.name
                .replace("[", "")
                .replace("]", "")
            )

            alias = table.alias

            if alias:
                aliases[alias.lower()] = table_name
            else:
                aliases[table_name.lower()] = table_name

        for column in expression.find_all(exp.Column):

            column_name = column.name

            if not column_name:
                continue

            table_alias = column.table

            # Ignore *
            if column_name == "*":
                continue

            # -----------------------------------------------------
            # Qualified column
            # -----------------------------------------------------

            if table_alias:

                actual_table = aliases.get(
                    table_alias.lower()
                )

                if not actual_table:
                    errors.append(
                        f"Unknown table alias: {table_alias}"
                    )
                    continue

                if not self.registry.column_exists(
                    actual_table,
                    column_name
                ):

                    errors.append(
                        f"Column '{column_name}' does not exist "
                        f"in table '{actual_table}'."
                    )

            # -----------------------------------------------------
            # Unqualified column
            # -----------------------------------------------------

            else:

                matching_tables = []

                for table in sql_tables:

                    if self.registry.column_exists(
                        table,
                        column_name
                    ):
                        matching_tables.append(table)

                if not matching_tables:

                    errors.append(
                        f"Column '{column_name}' does not exist "
                        f"in any referenced table."
                    )

        # =========================================================
        # 7. TOP 20 CHECK
        # =========================================================

        if not expression.args.get("limit"):

            errors.append(
                "Query must contain TOP 20 or an equivalent "
                "row limit."
            )

        # =========================================================
        # 8. DISTINCT + TOP SYNTAX
        # =========================================================

        sql_upper = sql.upper()

        if "DISTINCT" in sql_upper:

            if "TOP" in sql_upper:

                import re

                if not re.search(
                    r"SELECT\s+DISTINCT\s+TOP\s+\d+",
                    sql_upper
                ):

                    errors.append(
                        "Invalid DISTINCT + TOP syntax. "
                        "Use SELECT DISTINCT TOP N."
                    )

        # =========================================================
        # RESULT
        # =========================================================

        if errors:

            return {
                "valid": False,
                "errors": errors,
                "tables": sorted(sql_tables)
            }

        return {
            "valid": True,
            "errors": [],
            "tables": sorted(sql_tables)
        }


sql_validator = SQLValidator(schema_registry)