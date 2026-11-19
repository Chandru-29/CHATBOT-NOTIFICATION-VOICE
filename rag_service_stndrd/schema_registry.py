import os
import re


class SchemaRegistry:

    def __init__(self, md_file_path):
        self.md_file_path = md_file_path

        self.tables = {}
        self.relationships = []
        self.join_paths = []

        self._load()

    # ============================================================
    # LOAD MARKDOWN
    # ============================================================

    def _load(self):

        if not os.path.exists(self.md_file_path):
            raise FileNotFoundError(
                f"Schema file not found: {self.md_file_path}"
            )

        with open(
            self.md_file_path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        self._parse_tables(content)
        self._parse_relationships(content)
        self._parse_join_paths(content)

        print(
            f"SchemaRegistry loaded: "
            f"{len(self.tables)} tables, "
            f"{len(self.relationships)} relationships"
        )

    # ============================================================
    # TABLES + COLUMNS
    # ============================================================

    def _parse_tables(self, content):

        pattern = re.compile(
            r"# TABLE:\s*(.+?)\n"
            r"TYPE:\s*schema\s*\n"
            r"COLUMNS:\s*\n"
            r"(.*?)(?=\n(?:USAGE:|STATUS:|COMPLETION LOGIC:|DOCUMENT TYPE DEFINITIONS:|RULE:|JOIN:|---|\# TABLE:|\# CORE RELATIONSHIPS)|\Z)",
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(content)

        for table_name, columns_text in matches:

            table_name = table_name.strip()

            columns = {}

            for line in columns_text.splitlines():

                line = line.strip()

                if not line:
                    continue

                # Ignore markdown bullets
                if line.startswith("-"):
                    continue

                line = line.replace("`", "")

                match = re.match(
                    r"^([A-Za-z_][A-Za-z0-9_\[\]]*)"
                    r"(?:\s+\((PK|UNIQUE)\))?"
                    r"(?:\s+→\s+(.+))?$",
                    line
                )

                if not match:
                    continue

                column_name = match.group(1)
                constraint = match.group(2)
                reference = match.group(3)

                columns[column_name] = {
                    "primary_key": constraint == "PK",
                    "unique": constraint == "UNIQUE",
                    "reference": reference
                }

            self.tables[table_name] = {
                "columns": columns
            }
        # ============================================================
    # RELATIONSHIPS
    # ============================================================

    def _parse_relationships(self, content):

        section_match = re.search(
            r"# CORE RELATIONSHIPS\s*"
            r"(.*?)(?=\n---|\n# JOIN PATHS|\Z)",
            content,
            re.IGNORECASE | re.DOTALL
        )

        if not section_match:
            return

        section = section_match.group(1)

        for line in section.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith("TYPE:"):
                continue

            if "→" not in line:
                continue

            self.relationships.append(line)

    # ============================================================
    # JOIN PATHS
    # ============================================================

    def _parse_join_paths(self, content):

        section_match = re.search(
            r"# JOIN PATHS \(CRITICAL\)\s*"
            r"(.*?)(?=\n---|\n# INTENT MAPPING|\Z)",
            content,
            re.IGNORECASE | re.DOTALL
        )

        if not section_match:
            return

        section = section_match.group(1)

        for line in section.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith("TYPE:"):
                continue

            if "→" not in line:
                continue

            self.join_paths.append(line)

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def table_exists(self, table_name):

        normalized = table_name.replace(
            "[", ""
        ).replace(
            "]", ""
        ).lower()

        for table in self.tables:

            normalized_table = table.replace(
                "[", ""
            ).replace(
                "]", ""
            ).lower()

            if normalized_table == normalized:
                return True

        return False

    def get_table(self, table_name):

        normalized = table_name.replace(
            "[", ""
        ).replace(
            "]", ""
        ).lower()

        for table, data in self.tables.items():

            normalized_table = table.replace(
                "[", ""
            ).replace(
                "]", ""
            ).lower()

            if normalized_table == normalized:
                return data

        return None

    def column_exists(self, table_name, column_name):

        table = self.get_table(table_name)

        if not table:
            return False

        normalized_column = column_name.lower()

        for column in table["columns"]:

            if column.lower() == normalized_column:
                return True

        return False

    def get_columns(self, table_name):

        table = self.get_table(table_name)

        if not table:
            return []

        return list(table["columns"].keys())

    def get_relationships(self):

        return self.relationships

    def get_join_paths(self):

        return self.join_paths

    def get_all_tables(self):

        return list(self.tables.keys())


# ================================================================
# CREATE SINGLE REGISTRY INSTANCE
# ================================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# KNOWLEDGE_DIR = os.path.join(
#     BASE_DIR,
#     "knowledge"
# )

SCHEMA_FILE = os.path.join(
    BASE_DIR,
    "knowledge_stndrd",
    "db_schema.md"
)
print("Loading schema from:", SCHEMA_FILE)


schema_registry = SchemaRegistry(
    SCHEMA_FILE
)