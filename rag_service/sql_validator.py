# import sqlglot
# from sqlglot import exp

# from rag_service.schema_registry import schema_registry


# class SQLValidator:

#     def __init__(self, registry):
#         self.registry = registry

#     def validate(self, sql: str, retrieved_tables=None):

#         errors = []

#         if not sql or not sql.strip():
#             return {
#                 "valid": False,
#                 "errors": ["Empty SQL"]
#             }

#         sql = sql.strip()

#         # =========================================================
#         # 1. READ-ONLY CHECK
#         # =========================================================

#         try:
#             statements = sqlglot.parse(sql, dialect="tsql")
#         except Exception as e:
#             return {
#                 "valid": False,
#                 "errors": [f"SQL syntax error: {str(e)}"]
#             }

#         if len(statements) != 1:
#             errors.append("Only one SQL statement is allowed.")

#         expression = statements[0]

#         if not isinstance(expression, exp.Select):
#             errors.append(
#                 "Only SELECT queries are allowed."
#             )

#         # =========================================================
#         # 2. FORBIDDEN OPERATIONS
#         # =========================================================

#         forbidden = (
#             exp.Insert,
#             exp.Update,
#             exp.Delete,
#             exp.Drop,
#             exp.Create,
#             exp.Alter,
#             exp.Merge,
#             exp.TruncateTable,
#         )

#         for node in expression.walk():

#             if isinstance(node, forbidden):
#                 errors.append(
#                     f"Forbidden SQL operation: "
#                     f"{type(node).__name__}"
#                 )

#         # =========================================================
#         # 3. EXTRACT TABLES
#         # =========================================================

#         sql_tables = set()

#         for table in expression.find_all(exp.Table):

#             table_name = table.name

#             if table_name:
#                 sql_tables.add(
#                     table_name.replace("[", "")
#                     .replace("]", "")
#                     .lower()
#                 )

#         # =========================================================
#         # 4. VALIDATE TABLES AGAINST GLOBAL SCHEMA
#         # =========================================================

#         for table in sql_tables:

#             if not self.registry.table_exists(table):

#                 errors.append(
#                     f"Table does not exist in schema: {table}"
#                 )

#         # =========================================================
#         # 5. VALIDATE AGAINST RAG RETRIEVED TABLES
#         # =========================================================

#         if retrieved_tables:

#             normalized_retrieved = {
#                 t.replace("[", "")
#                 .replace("]", "")
#                 .lower()
#                 for t in retrieved_tables
#             }

#             for table in sql_tables:

#                 if table not in normalized_retrieved:

#                     errors.append(
#                         f"Table '{table}' was not present "
#                         f"in retrieved RAG knowledge."
#                     )

#         # =========================================================
#         # 6. COLUMN VALIDATION
#         # =========================================================

#         aliases = {}

#         for table in expression.find_all(exp.Table):

#             table_name = (
#                 table.name
#                 .replace("[", "")
#                 .replace("]", "")
#             )

#             alias = table.alias

#             if alias:
#                 aliases[alias.lower()] = table_name
#             else:
#                 aliases[table_name.lower()] = table_name

#         for column in expression.find_all(exp.Column):

#             column_name = column.name

#             if not column_name:
#                 continue

#             table_alias = column.table

#             # Ignore *
#             if column_name == "*":
#                 continue

#             # -----------------------------------------------------
#             # Qualified column
#             # -----------------------------------------------------

#             if table_alias:

#                 actual_table = aliases.get(
#                     table_alias.lower()
#                 )

#                 if not actual_table:
#                     errors.append(
#                         f"Unknown table alias: {table_alias}"
#                     )
#                     continue

#                 if not self.registry.column_exists(
#                     actual_table,
#                     column_name
#                 ):

#                     errors.append(
#                         f"Column '{column_name}' does not exist "
#                         f"in table '{actual_table}'."
#                     )

#             # -----------------------------------------------------
#             # Unqualified column
#             # -----------------------------------------------------

#             else:

#                 matching_tables = []

#                 for table in sql_tables:

#                     if self.registry.column_exists(
#                         table,
#                         column_name
#                     ):
#                         matching_tables.append(table)

#                 if not matching_tables:

#                     errors.append(
#                         f"Column '{column_name}' does not exist "
#                         f"in any referenced table."
#                     )

#         # =========================================================
#         # 7. TOP 20 CHECK
#         # =========================================================

#         if not expression.args.get("limit"):

#             errors.append(
#                 "Query must contain TOP 20 or an equivalent "
#                 "row limit."
#             )

#         # =========================================================
#         # 8. DISTINCT + TOP SYNTAX
#         # =========================================================

#         sql_upper = sql.upper()

#         if "DISTINCT" in sql_upper:

#             if "TOP" in sql_upper:

#                 import re

#                 if not re.search(
#                     r"SELECT\s+DISTINCT\s+TOP\s+\d+",
#                     sql_upper
#                 ):

#                     errors.append(
#                         "Invalid DISTINCT + TOP syntax. "
#                         "Use SELECT DISTINCT TOP N."
#                     )

#         # =========================================================
#         # RESULT
#         # =========================================================

#         if errors:

#             return {
#                 "valid": False,
#                 "errors": errors,
#                 "tables": sorted(sql_tables)
#             }

#         return {
#             "valid": True,
#             "errors": [],
#             "tables": sorted(sql_tables)
#         }


# sql_validator = SQLValidator(schema_registry)











# import sqlglot
# from sqlglot import exp

# from schema_registry import schema_registry


# class SQLValidator:

#     def __init__(self, registry):
#         self.registry = registry

#     def validate(self, sql: str, retrieved_tables=None):

#         errors = []

#         if not sql or not sql.strip():
#             return {
#                 "valid": False,
#                 "errors": ["Empty SQL"]
#             }

#         sql = sql.strip()

#         # =========================================================
#         # 1. READ-ONLY CHECK
#         # =========================================================

#         try:
#             statements = sqlglot.parse(
#                 sql,
#                 dialect="mysql"
#             )
#         except Exception as e:
#             return {
#                 "valid": False,
#                 "errors": [
#                     f"SQL syntax error: {str(e)}"
#                 ]
#             }

#         if len(statements) != 1:
#             errors.append(
#                 "Only one SQL statement is allowed."
#             )

#         expression = statements[0]

#         if not isinstance(expression, exp.Select):
#             errors.append(
#                 "Only SELECT queries are allowed."
#             )

#         # =========================================================
#         # 2. FORBIDDEN OPERATIONS
#         # =========================================================

#         forbidden = (
#             exp.Insert,
#             exp.Update,
#             exp.Delete,
#             exp.Drop,
#             exp.Create,
#             exp.Alter,
#             exp.Merge,
#             exp.TruncateTable,
#         )

#         for node in expression.walk():

#             if isinstance(node, forbidden):
#                 errors.append(
#                     f"Forbidden SQL operation: "
#                     f"{type(node).__name__}"
#                 )

#         # =========================================================
#         # 3. EXTRACT TABLES
#         # =========================================================

#         sql_tables = set()

#         for table in expression.find_all(exp.Table):

#             table_name = table.name

#             if table_name:
#                 sql_tables.add(
#                     table_name.replace("[", "")
#                     .replace("]", "")
#                     .lower()
#                 )

#         # =========================================================
#         # 4. VALIDATE TABLES AGAINST GLOBAL SCHEMA
#         # =========================================================

#         for table in sql_tables:

#             if not self.registry.table_exists(table):

#                 errors.append(
#                     f"Table does not exist in schema: {table}"
#                 )

#         # =========================================================
#         # 5. VALIDATE AGAINST RAG RETRIEVED TABLES
#         # =========================================================

#         if retrieved_tables:

#             normalized_retrieved = {
#                 t.replace("[", "")
#                 .replace("]", "")
#                 .lower()
#                 for t in retrieved_tables
#             }

#             for table in sql_tables:

#                 if table not in normalized_retrieved:

#                     errors.append(
#                         f"Table '{table}' was not present "
#                         f"in retrieved RAG knowledge."
#                     )

#         # =========================================================
#         # 6. COLUMN VALIDATION
#         # =========================================================

#         aliases = {}

#         for table in expression.find_all(exp.Table):

#             table_name = (
#                 table.name
#                 .replace("[", "")
#                 .replace("]", "")
#             )

#             alias = table.alias

#             if alias:
#                 aliases[alias.lower()] = table_name
#             else:
#                 aliases[table_name.lower()] = table_name

#         for column in expression.find_all(exp.Column):

#             column_name = column.name

#             if not column_name:
#                 continue

#             table_alias = column.table

#             # Ignore *
#             if column_name == "*":
#                 continue

#             # -----------------------------------------------------
#             # Qualified column
#             # -----------------------------------------------------

#             if table_alias:

#                 actual_table = aliases.get(
#                     table_alias.lower()
#                 )

#                 if not actual_table:

#                     errors.append(
#                         f"Unknown table alias: {table_alias}"
#                     )

#                     continue

#                 if not self.registry.column_exists(
#                     actual_table,
#                     column_name
#                 ):

#                     errors.append(
#                         f"Column '{column_name}' does not exist "
#                         f"in table '{actual_table}'."
#                     )

#             # -----------------------------------------------------
#             # Unqualified column
#             # -----------------------------------------------------

#             else:

#                 matching_tables = []

#                 for table in sql_tables:

#                     if self.registry.column_exists(
#                         table,
#                         column_name
#                     ):

#                         matching_tables.append(table)

#                 if not matching_tables:

#                     errors.append(
#                         f"Column '{column_name}' does not exist "
#                         f"in any referenced table."
#                     )

#         # =========================================================
#         # 7. LIMIT CHECK
#         # =========================================================

#         if not expression.args.get("limit"):

#             errors.append(
#                 "Query must contain LIMIT 20 or an "
#                 "equivalent row limit."
#             )

#         # =========================================================
#         # 8. DISTINCT + LIMIT CHECK
#         # =========================================================

#         sql_upper = sql.upper()

#         if "DISTINCT" in sql_upper:

#             if "LIMIT" in sql_upper:

#                 import re

#                 if not re.search(
#                     r"LIMIT\s+\d+",
#                     sql_upper
#                 ):

#                     errors.append(
#                         "Invalid DISTINCT + LIMIT syntax. "
#                         "Use SELECT DISTINCT ... LIMIT N."
#                     )

#         # =========================================================
#         # RESULT
#         # =========================================================

#         if errors:

#             return {
#                 "valid": False,
#                 "errors": errors,
#                 "tables": sorted(sql_tables)
#             }

#         return {
#             "valid": True,
#             "errors": [],
#             "tables": sorted(sql_tables)
#         }


# sql_validator = SQLValidator(schema_registry)

# print("\n================ REGISTRY DEBUG ================")

# print("Registry object:", id(schema_registry))

# print("SS_PICKLIST exists:",
#       schema_registry.table_exists("SS_PICKLIST"))

# print("ss_picklist exists:",
#       schema_registry.table_exists("ss_picklist"))

# print("SS_PICKLIST columns:",
#       schema_registry.get_columns("SS_PICKLIST"))

# print("ss_picklist columns:",
#       schema_registry.get_columns("ss_picklist"))

# print("Raw table key:")
# for table in schema_registry.tables:
#     if table.lower() == "ss_picklist":
#         print(repr(table))

# print("================================================\n")
































import re
from typing import Dict, List, Optional, Set

import sqlglot
from sqlglot import exp

from rag_service.schema_registry import schema_registry


class SQLValidator:

    def __init__(self, registry):

        self.registry = registry

    # ============================================================
    # PUBLIC VALIDATION
    # ============================================================

    def validate(
        self,
        sql: str,
        retrieved_tables=None
    ):

        errors = []

        # --------------------------------------------------------
        # 1. BASIC SQL CHECK
        # --------------------------------------------------------

        if not sql or not sql.strip():

            return self._failure(
                ["Empty SQL"]
            )

        sql = sql.strip()

        # --------------------------------------------------------
        # 2. PARSE SQL
        # --------------------------------------------------------

        try:

            statements = sqlglot.parse(
                sql,
                dialect="mysql"
            )

        except Exception as e:

            return self._failure([
                f"SQL syntax error: {str(e)}"
            ])

        if not statements:

            return self._failure([
                "Unable to parse SQL."
            ])

        if len(statements) != 1:

            errors.append(
                "Only one SQL statement is allowed."
            )

        expression = statements[0]

        # --------------------------------------------------------
        # 3. READ ONLY
        # --------------------------------------------------------

        self._validate_read_only(
            expression,
            errors
        )

        # --------------------------------------------------------
        # 4. EXTRACT TABLES
        # --------------------------------------------------------

        sql_tables = self._extract_tables(
            expression
        )

        if not sql_tables:

            errors.append(
                "No database table found in SQL."
            )

        # --------------------------------------------------------
        # 5. GLOBAL TABLE VALIDATION
        # --------------------------------------------------------

        self._validate_tables(
            sql_tables,
            errors
        )

        # --------------------------------------------------------
        # 6. RAG TABLE VALIDATION
        # --------------------------------------------------------

        self._validate_retrieved_tables(
            sql_tables,
            retrieved_tables,
            errors
        )

        # --------------------------------------------------------
        # 7. ALIAS MAP
        # --------------------------------------------------------

        aliases = self._build_alias_map(
            expression
        )

        # --------------------------------------------------------
        # 8. COLUMN VALIDATION
        # --------------------------------------------------------

        self._validate_columns(
            expression,
            sql_tables,
            aliases,
            errors
        )

        # --------------------------------------------------------
        # 9. JOIN VALIDATION
        # --------------------------------------------------------

        self._validate_joins(
            expression,
            aliases,
            errors
        )

        # --------------------------------------------------------
        # 10. SOFT DELETE
        # --------------------------------------------------------

        self._validate_soft_delete(
            expression,
            sql_tables,
            errors
        )

        # --------------------------------------------------------
        # 11. LIMIT
        # --------------------------------------------------------

        self._validate_limit(
            expression,
            errors
        )

        # --------------------------------------------------------
        # 12. DISTINCT + LIMIT
        # --------------------------------------------------------

        self._validate_distinct_limit(
            sql,
            errors
        )

        # --------------------------------------------------------
        # RESULT
        # --------------------------------------------------------

        if errors:

            return self._failure(
                errors,
                sql_tables
            )

        return {
            "valid": True,
            "errors": [],
            "tables": sorted(
                sql_tables
            )
        }

    # ============================================================
    # READ ONLY
    # ============================================================

    def _validate_read_only(
        self,
        expression,
        errors: List[str]
    ):

        if not isinstance(
            expression,
            exp.Select
        ):

            errors.append(
                "Only SELECT queries are allowed."
            )

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

            if isinstance(
                node,
                forbidden
            ):

                errors.append(
                    "Forbidden SQL operation: "
                    f"{type(node).__name__}"
                )

    # ============================================================
    # TABLE EXTRACTION
    # ============================================================

    def _extract_tables(
        self,
        expression
    ) -> Set[str]:

        tables = set()

        for table in expression.find_all(
            exp.Table
        ):

            name = table.name

            if not name:
                continue

            canonical = (
                self.registry.resolve_table_name(
                    name
                )
            )

            if canonical:

                tables.add(canonical)

            else:

                # Preserve unknown name for
                # useful validation error.
                tables.add(
                    name.strip()
                )

        return tables

    # ============================================================
    # TABLE VALIDATION
    # ============================================================

    def _validate_tables(
        self,
        sql_tables: Set[str],
        errors: List[str]
    ):

        for table in sql_tables:

            if not self.registry.table_exists(
                table
            ):

                errors.append(
                    "Table does not exist in schema: "
                    f"{table}"
                )

    # ============================================================
    # RAG TABLE VALIDATION
    # ============================================================

    def _validate_retrieved_tables(
        self,
        sql_tables: Set[str],
        retrieved_tables,
        errors: List[str]
    ):

        if not retrieved_tables:
            return

        retrieved_canonical = set()

        for table in retrieved_tables:

            canonical = (
                self.registry.resolve_table_name(
                    table
                )
            )

            if canonical:

                retrieved_canonical.add(
                    canonical.lower()
                )

            else:

                retrieved_canonical.add(
                    str(table).lower()
                )

        for table in sql_tables:

            canonical = (
                self.registry.resolve_table_name(
                    table
                )
            )

            comparison_name = (
                canonical.lower()
                if canonical
                else table.lower()
            )

            if comparison_name not in retrieved_canonical:

                errors.append(
                    f"Table '{table}' was not present "
                    "in retrieved RAG knowledge."
                )

    # ============================================================
    # ALIAS MAP
    # ============================================================

    def _build_alias_map(
        self,
        expression
    ) -> Dict[str, str]:

        aliases = {}

        for table in expression.find_all(
            exp.Table
        ):

            table_name = table.name

            canonical = (
                self.registry.resolve_table_name(
                    table_name
                )
            )

            actual_table = (
                canonical
                if canonical
                else table_name
            )

            alias = table.alias

            if alias:

                aliases[
                    alias.lower()
                ] = actual_table

            aliases[
                table_name.lower()
            ] = actual_table

        return aliases

    # ============================================================
    # COLUMN VALIDATION
    # ============================================================

    def _validate_columns(
        self,
        expression,
        sql_tables: Set[str],
        aliases: Dict[str, str],
        errors: List[str]
    ):

        for column in expression.find_all(
            exp.Column
        ):

            column_name = column.name

            if not column_name:
                continue

            # SELECT *
            if column_name == "*":
                continue

            table_alias = column.table

            # ----------------------------------------------------
            # QUALIFIED COLUMN
            # ----------------------------------------------------

            if table_alias:

                actual_table = aliases.get(
                    table_alias.lower()
                )

                if not actual_table:

                    errors.append(
                        f"Unknown table alias: "
                        f"{table_alias}"
                    )

                    continue

                if not self.registry.column_exists(
                    actual_table,
                    column_name
                ):

                    errors.append(
                        f"Column '{column_name}' "
                        f"does not exist in table "
                        f"'{actual_table}'."
                    )

                continue

            # ----------------------------------------------------
            # UNQUALIFIED COLUMN
            # ----------------------------------------------------

            matching_tables = []

            for table in sql_tables:

                if self.registry.column_exists(
                    table,
                    column_name
                ):

                    matching_tables.append(
                        table
                    )

            if not matching_tables:

                errors.append(
                    f"Column '{column_name}' does not "
                    "exist in any referenced table."
                )

    # ============================================================
    # JOIN VALIDATION
    # ============================================================

    def _validate_joins(
        self,
        expression,
        aliases: Dict[str, str],
        errors: List[str]
    ):

        for join in expression.find_all(
            exp.Join
        ):

            right_table_expression = (
                join.this
            )

            if not isinstance(
                right_table_expression,
                exp.Table
            ):

                continue

            right_name = (
                right_table_expression.name
            )

            right_table = (
                self.registry.resolve_table_name(
                    right_name
                )
                or right_name
            )

            on_expression = (
                join.args.get("on")
            )

            if not on_expression:
                continue

            conditions = list(
                on_expression.find_all(
                    exp.EQ
                )
            )

            for condition in conditions:

                left_column = condition.left
                right_column = condition.right

                if not isinstance(
                    left_column,
                    exp.Column
                ):
                    continue

                if not isinstance(
                    right_column,
                    exp.Column
                ):
                    continue

                left_table = self._resolve_column_table(
                    left_column,
                    aliases
                )

                right_table_resolved = (
                    self._resolve_column_table(
                        right_column,
                        aliases
                    )
                )

                if not left_table or not right_table_resolved:
                    continue

                if not self.registry.relationship_exists(
                    left_table,
                    left_column.name,
                    right_table_resolved,
                    right_column.name
                ):

                    errors.append(
                        "Invalid JOIN relationship: "
                        f"{left_table}.{left_column.name} "
                        f"↔ "
                        f"{right_table_resolved}.{right_column.name}"
                    )

    # ============================================================
    # COLUMN TABLE RESOLUTION
    # ============================================================

    def _resolve_column_table(
        self,
        column,
        aliases
    ):

        if not column.table:
            return None

        return aliases.get(
            column.table.lower()
        )

    # ============================================================
    # SOFT DELETE
    # ============================================================

    def _validate_soft_delete(
        self,
        expression,
        sql_tables: Set[str],
        errors: List[str]
    ):

        # This is deliberately informational rather than
        # automatically rejecting every query.
        #
        # The MD says:
        #
        # "Always filter isDeleted = 0 for tables
        # containing the isDeleted column."
        #
        # We check whether the query references an
        # isDeleted column at all.

        tables_with_soft_delete = []

        for table in sql_tables:

            if self.registry.column_exists(
                table,
                "isDeleted"
            ):

                tables_with_soft_delete.append(
                    table
                )

        if not tables_with_soft_delete:
            return

        has_is_deleted = False

        for column in expression.find_all(
            exp.Column
        ):

            if (
                column.name
                and
                column.name.lower()
                == "isdeleted"
            ):

                has_is_deleted = True
                break

        # Do not reject here yet.
        #
        # Reason:
        # Some aggregate/reporting queries in the
        # knowledge file do not include isDeleted.
        #
        # Keep this available for future strict mode.

        return

    # ============================================================
    # LIMIT
    # ============================================================

    def _validate_limit(
        self,
        expression,
        errors: List[str]
    ):

        if not expression.args.get(
            "limit"
        ):

            errors.append(
                "Query must contain LIMIT."
            )

    # ============================================================
    # DISTINCT + LIMIT
    # ============================================================

    def _validate_distinct_limit(
        self,
        sql: str,
        errors: List[str]
    ):

        sql_upper = sql.upper()

        if "DISTINCT" not in sql_upper:
            return

        if "LIMIT" not in sql_upper:
            return

        if not re.search(
            r"LIMIT\s+\d+",
            sql_upper
        ):

            errors.append(
                "Invalid DISTINCT + LIMIT syntax. "
                "Use SELECT DISTINCT ... LIMIT N."
            )

    # ============================================================
    # FAILURE RESPONSE
    # ============================================================

    def _failure(
        self,
        errors: List[str],
        tables=None
    ):

        response = {
            "valid": False,
            "errors": errors
        }

        if tables is not None:
            response["tables"] = sorted(
                tables
            )

        return response


# ================================================================
# SINGLE VALIDATOR INSTANCE
# ================================================================

sql_validator = SQLValidator(
    schema_registry
)