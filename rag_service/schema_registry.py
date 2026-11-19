# import os
# import re


# class SchemaRegistry:

#     def __init__(self, md_file_path):
#         self.md_file_path = md_file_path

#         self.tables = {}
#         self.relationships = []
#         self.join_paths = []

#         self._load()

#     # ============================================================
#     # LOAD MARKDOWN
#     # ============================================================

#     def _load(self):

#         if not os.path.exists(self.md_file_path):
#             raise FileNotFoundError(
#                 f"Schema file not found: {self.md_file_path}"
#             )

#         with open(
#             self.md_file_path,
#             "r",
#             encoding="utf-8"
#         ) as f:

#             content = f.read()

#         self._parse_tables(content)
#         self._parse_relationships(content)
#         self._parse_join_paths(content)

#         print(
#             f"SchemaRegistry loaded: "
#             f"{len(self.tables)} tables, "
#             f"{len(self.relationships)} relationships"
#         )

#     # ============================================================
#     # TABLES + COLUMNS
#     # ============================================================

#     def _parse_tables(self, content):

#         pattern = re.compile(
#             r"# TABLE:\s*(.+?)\n"
#             r"TYPE:\s*schema\s*\n"
#             r"COLUMNS:\s*\n"
#             r"(.*?)(?=\n(?:USAGE:|STATUS:|COMPLETION LOGIC:|DOCUMENT TYPE DEFINITIONS:|RULE:|JOIN:|---|\# TABLE:|\# CORE RELATIONSHIPS)|\Z)",
#             re.IGNORECASE | re.DOTALL
#         )

#         matches = pattern.findall(content)

#         for table_name, columns_text in matches:

#             table_name = table_name.strip()

#             columns = {}

#             for line in columns_text.splitlines():

#                 line = line.strip()

#                 if not line:
#                     continue

#                 # Ignore markdown bullets
#                 if line.startswith("-"):
#                     continue

#                 line = line.replace("`", "")

#                 match = re.match(
#                     r"^([A-Za-z_][A-Za-z0-9_\[\]]*)"
#                     r"(?:\s+\((PK|UNIQUE)\))?"
#                     r"(?:\s+→\s+(.+))?$",
#                     line
#                 )

#                 if not match:
#                     continue

#                 column_name = match.group(1)
#                 constraint = match.group(2)
#                 reference = match.group(3)

#                 columns[column_name] = {
#                     "primary_key": constraint == "PK",
#                     "unique": constraint == "UNIQUE",
#                     "reference": reference
#                 }

#             self.tables[table_name] = {
#                 "columns": columns
#             }
#         # ============================================================
#     # RELATIONSHIPS
#     # ============================================================

#     def _parse_relationships(self, content):

#         section_match = re.search(
#             r"# CORE RELATIONSHIPS\s*"
#             r"(.*?)(?=\n---|\n# JOIN PATHS|\Z)",
#             content,
#             re.IGNORECASE | re.DOTALL
#         )

#         if not section_match:
#             return

#         section = section_match.group(1)

#         for line in section.splitlines():

#             line = line.strip()

#             if not line:
#                 continue

#             if line.startswith("TYPE:"):
#                 continue

#             if "→" not in line:
#                 continue

#             self.relationships.append(line)

#     # ============================================================
#     # JOIN PATHS
#     # ============================================================

#     def _parse_join_paths(self, content):

#         section_match = re.search(
#             r"# JOIN PATHS \(CRITICAL\)\s*"
#             r"(.*?)(?=\n---|\n# INTENT MAPPING|\Z)",
#             content,
#             re.IGNORECASE | re.DOTALL
#         )

#         if not section_match:
#             return

#         section = section_match.group(1)

#         for line in section.splitlines():

#             line = line.strip()

#             if not line:
#                 continue

#             if line.startswith("TYPE:"):
#                 continue

#             if "→" not in line:
#                 continue

#             self.join_paths.append(line)

#     # ============================================================
#     # PUBLIC METHODS
#     # ============================================================

#     def table_exists(self, table_name):

#         normalized = table_name.replace(
#             "[", ""
#         ).replace(
#             "]", ""
#         ).lower()

#         for table in self.tables:

#             normalized_table = table.replace(
#                 "[", ""
#             ).replace(
#                 "]", ""
#             ).lower()

#             if normalized_table == normalized:
#                 return True

#         return False

#     def get_table(self, table_name):

#         normalized = table_name.replace(
#             "[", ""
#         ).replace(
#             "]", ""
#         ).lower()

#         for table, data in self.tables.items():

#             normalized_table = table.replace(
#                 "[", ""
#             ).replace(
#                 "]", ""
#             ).lower()

#             if normalized_table == normalized:
#                 return data

#         return None

#     def column_exists(self, table_name, column_name):

#         table = self.get_table(table_name)

#         if not table:
#             return False

#         normalized_column = column_name.lower()

#         for column in table["columns"]:

#             if column.lower() == normalized_column:
#                 return True

#         return False

#     def get_columns(self, table_name):

#         table = self.get_table(table_name)

#         if not table:
#             return []

#         return list(table["columns"].keys())

#     def get_relationships(self):

#         return self.relationships

#     def get_join_paths(self):

#         return self.join_paths

#     def get_all_tables(self):

#         return list(self.tables.keys())


# # ================================================================
# # CREATE SINGLE REGISTRY INSTANCE
# # ================================================================

# # BASE_DIR = os.path.dirname(
# #     os.path.abspath(__file__)
# # )

# # # KNOWLEDGE_DIR = os.path.join(
# # #     BASE_DIR,
# # #     "knowledge"
# # # )

# # SCHEMA_FILE = os.path.join(
# #     BASE_DIR,
# #     "knowledge",
# #     "db_schema.md"
# # )
# # print("Loading schema from:", SCHEMA_FILE)


# # schema_registry = SchemaRegistry(
# #     SCHEMA_FILE
# # )




# BASE_DIR = os.path.dirname(
#     os.path.dirname(
#         os.path.abspath(__file__)
#     )
# )

# SCHEMA_FILE = os.path.join(
#     BASE_DIR,
#     "knowledge",
#     "nerolac.md"
# )

# print("Loading schema from:", SCHEMA_FILE)

# schema_registry = SchemaRegistry(
#     SCHEMA_FILE
# )







# import os
# import re


# class SchemaRegistry:

#     def __init__(self, md_file_path):
#         self.md_file_path = md_file_path
#         self.tables = {}
#         self.relationships = []
#         self.join_paths = []
#         self._load()

#     # ============================================================
#     # LOAD MARKDOWN
#     # ============================================================

#     def _load(self):

#         if not os.path.exists(self.md_file_path):
#             raise FileNotFoundError(
#                 f"Schema file not found: {self.md_file_path}"
#             )

#         with open(
#             self.md_file_path,
#             "r",
#             encoding="utf-8"
#         ) as f:
#             content = f.read()

#         self._parse_tables(content)
#         self._parse_relationships(content)
#         self._parse_join_paths(content)

#         print(
#             f"SchemaRegistry loaded: "
#             f"{len(self.tables)} tables, "
#             f"{len(self.relationships)} relationships"
#         )

#         print(
#             f"Tables found: {list(self.tables.keys())}"
#         )

#     # ============================================================
#     # TABLES + COLUMNS
#     # ============================================================

#     def _parse_tables(self, content):

#         pattern = re.compile(
#             r"^#\s+TABLE:\s*(.+?)\s*$"
#             r"(.*?)"
#             r"(?=^#\s+TABLE:|"
#             r"^##\s+DOMAIN CORE RELATIONSHIPS|"
#             r"^##\s+QUERY PATTERNS|"
#             r"^---\s*$|"
#             r"\Z)",
#             re.IGNORECASE | re.MULTILINE | re.DOTALL
#         )

#         matches = pattern.findall(content)

#         print(
#             f"Schema table matches: {len(matches)}"
#         )

#         for table_name, table_content in matches:

#             table_name = table_name.strip()

#             # ----------------------------------------------------
#             # Find COLUMNS section
#             # ----------------------------------------------------

#             columns_match = re.search(
#                 r"^COLUMNS:\s*$"
#                 r"(.*?)"
#                 r"(?=^USAGE:|"
#                 r"^RULE:|"
#                 r"^STATUS:|"
#                 r"^COMPLETION LOGIC:|"
#                 r"^DOCUMENT TYPE DEFINITIONS:|"
#                 r"^##|"
#                 r"^#\s+TABLE:|"
#                 r"\Z)",
#                 table_content,
#                 re.IGNORECASE | re.MULTILINE | re.DOTALL
#             )

#             if not columns_match:
#                 continue

#             columns_text = columns_match.group(1)

#             columns = {}

#             for line in columns_text.splitlines():

#                 line = line.strip()

#                 if not line:
#                     continue

#                 if line.startswith("-"):
#                     line = line[1:].strip()

#                 line = line.replace("`", "")

#                 if line.startswith("#"):
#                     continue

#                 match = re.match(
#                     r"^([A-Za-z_][A-Za-z0-9_\[\]]*)"
#                     r"(?:\s*\(([^)]*)\))?"
#                     r"(?:\s*→\s*(.+))?$",
#                     line
#                 )

#                 if not match:
#                     continue

#                 column_name = match.group(1).strip()

#                 constraint_text = match.group(2)
#                 reference = match.group(3)

#                 primary_key = False
#                 unique = False

#                 if constraint_text:

#                     constraints = {
#                         item.strip().upper()
#                         for item in constraint_text.split(",")
#                     }

#                     primary_key = "PK" in constraints
#                     unique = "UNIQUE" in constraints

#                 columns[column_name] = {
#                     "primary_key": primary_key,
#                     "unique": unique,
#                     "reference": (
#                         reference.strip()
#                         if reference
#                         else None
#                     )
#                 }

#             self.tables[table_name] = {
#                 "columns": columns
#             }
#     # ============================================================
#     # RELATIONSHIPS
#     # ============================================================

#     def _parse_relationships(self, content):

#         # Your file uses:
#         #
#         # ## DOMAIN CORE RELATIONSHIPS & JOINS (Picklist):
#         #
#         # - `SS_PICKLIST.picklistId → SS_PICKLISTVIEW.picklistId`

#         pattern = re.compile(
#             r"^##\s+DOMAIN CORE RELATIONSHIPS.*?$"
#             r"(.*?)"
#             r"(?=^##\s+QUERY PATTERNS|"
#             r"^---\s*$|"
#             r"^#\s+DOMAIN:|"
#             r"\Z)",
#             re.IGNORECASE | re.MULTILINE | re.DOTALL
#         )

#         matches = pattern.findall(content)

#         for section in matches:

#             for line in section.splitlines():

#                 line = line.strip()

#                 if not line:
#                     continue

#                 # Remove markdown bullet
#                 if line.startswith("-"):
#                     line = line[1:].strip()

#                 # Remove backticks
#                 line = line.replace("`", "")

#                 if "→" not in line:
#                     continue

#                 self.relationships.append(line)

#     # ============================================================
#     # JOIN PATHS
#     # ============================================================

#     def _parse_join_paths(self, content):

#         # Your current nerolac.md does not appear to contain
#         # a "# JOIN PATHS" section.
#         #
#         # Keep this method so the public API remains unchanged.

#         section_match = re.search(
#             r"^#\s+JOIN PATHS\s*(?:\(CRITICAL\))?\s*$"
#             r"(.*?)"
#             r"(?=^---\s*$|"
#             r"^#\s+DOMAIN:|"
#             r"\Z)",
#             content,
#             re.IGNORECASE | re.MULTILINE | re.DOTALL
#         )

#         if not section_match:
#             return

#         section = section_match.group(1)

#         for line in section.splitlines():

#             line = line.strip()

#             if not line:
#                 continue

#             if line.startswith("-"):
#                 line = line[1:].strip()

#             line = line.replace("`", "")

#             if "→" not in line:
#                 continue

#             self.join_paths.append(line)

#     # ============================================================
#     # PUBLIC METHODS
#     # ============================================================

#     def table_exists(self, table_name):

#         normalized = (
#             table_name
#             .replace("[", "")
#             .replace("]", "")
#             .lower()
#         )

#         for table in self.tables:

#             normalized_table = (
#                 table
#                 .replace("[", "")
#                 .replace("]", "")
#                 .lower()
#             )

#             if normalized_table == normalized:
#                 return True

#         return False

#     # ============================================================
#     # GET TABLE
#     # ============================================================

#     def get_table(self, table_name):

#         normalized = (
#             table_name
#             .replace("[", "")
#             .replace("]", "")
#             .lower()
#         )

#         for table, data in self.tables.items():

#             normalized_table = (
#                 table
#                 .replace("[", "")
#                 .replace("]", "")
#                 .lower()
#             )

#             if normalized_table == normalized:
#                 return data

#         return None

#     # ============================================================
#     # COLUMN EXISTS
#     # ============================================================

#     def column_exists(
#         self,
#         table_name,
#         column_name
#     ):

#         table = self.get_table(table_name)

#         if not table:
#             return False

#         normalized_column = column_name.lower()

#         for column in table["columns"]:

#             if column.lower() == normalized_column:
#                 return True

#         return False

#     # ============================================================
#     # GET COLUMNS
#     # ============================================================

#     def get_columns(self, table_name):

#         table = self.get_table(table_name)

#         if not table:
#             return []

#         return list(
#             table["columns"].keys()
#         )

#     # ============================================================
#     # GET RELATIONSHIPS
#     # ============================================================

#     def get_relationships(self):

#         return self.relationships

#     # ============================================================
#     # GET JOIN PATHS
#     # ============================================================

#     def get_join_paths(self):

#         return self.join_paths

#     # ============================================================
#     # GET ALL TABLES
#     # ============================================================

#     def get_all_tables(self):

#         return list(
#             self.tables.keys()
#         )


# # ================================================================
# # CREATE SINGLE REGISTRY INSTANCE
# # ================================================================

# BASE_DIR = os.path.dirname(
#     os.path.dirname(
#         os.path.abspath(__file__)
#     )
# )

# SCHEMA_FILE = os.path.join(
#     BASE_DIR,
#     "knowledge",
#     "nerolac.md"
# )

# print(
#     "Loading schema from:",
#     SCHEMA_FILE
# )

# schema_registry = SchemaRegistry(
#     SCHEMA_FILE
# )






















import os
import re
from typing import Any, Dict, List, Optional, Tuple


class SchemaRegistry:

    def __init__(self, knowledge_path: Optional[str] = None):

        if not knowledge_path:
            knowledge_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "knowledge"
            )

        self.knowledge_path = knowledge_path
        self.md_file_path = knowledge_path  # For backwards compatibility

        # Canonical schema representation.
        # Original table/column casing is preserved.
        self.tables: Dict[str, Dict[str, Any]] = {}

        # Relationships are stored in normalized structured form.
        self.relationships: List[Dict[str, str]] = []

        # Query patterns grouped by table/domain.
        self.query_patterns: List[Dict[str, Any]] = []

        # Global rules / semantic mappings.
        self.global_rules: List[str] = []
        self.business_term_mapping: Dict[str, str] = {}
        self.intent_mapping: Dict[str, str] = {}

        self.reload()

    # ============================================================
    # LOAD & HOT-RELOAD
    # ============================================================

    def _load(self):
        self.reload()

    def reload(self):
        """
        Dynamically loads / hot-reloads all markdown knowledge files.
        Can load a single file or an entire knowledge directory without restarting the server.
        """
        self.tables.clear()
        self.relationships.clear()
        self.query_patterns.clear()
        self.global_rules.clear()
        self.business_term_mapping.clear()
        self.intent_mapping.clear()

        files_to_load = []
        if os.path.isdir(self.knowledge_path):
            for f in sorted(os.listdir(self.knowledge_path)):
                if f.endswith(".md") or f.endswith(".markdown"):
                    files_to_load.append(os.path.join(self.knowledge_path, f))
        elif os.path.isfile(self.knowledge_path):
            files_to_load.append(self.knowledge_path)
        else:
            print(f"Warning: Schema path not found: {self.knowledge_path}")
            return

        for fpath in files_to_load:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self._parse_global_sections(content)
                self._parse_tables(content)
            except Exception as e:
                print(f"Error loading schema file '{fpath}':", e)

        print(
            f"SchemaRegistry loaded: "
            f"{len(self.tables)} tables, "
            f"{len(self.relationships)} relationships"
        )

        print(
            f"Query patterns loaded: "
            f"{len(self.query_patterns)}"
        )

        print(
            f"Tables found: "
            f"{list(self.tables.keys())}"
        )

    # ============================================================
    # NORMALIZATION HELPERS
    # ============================================================

    @staticmethod
    def _clean(value: str) -> str:

        if value is None:
            return ""

        value = value.strip()

        # Markdown formatting
        value = value.replace("`", "")
        value = value.replace("**", "")

        # Escaped markdown characters from the MD source
        value = value.replace("\\", "")

        return value.strip()

    @staticmethod
    def _normalize_identifier(value: str) -> str:

        value = SchemaRegistry._clean(value)

        value = (
            value
            .replace("[", "")
            .replace("]", "")
            .strip()
        )

        return value.lower()

    @staticmethod
    def _normalize_relationship_line(line: str) -> Optional[str]:

        line = SchemaRegistry._clean(line)

        line = re.sub(
            r"^\s*-\s*",
            "",
            line
        )

        if "<->" not in line:
            return None

        return line.strip()

    # ============================================================
    # GLOBAL SECTIONS
    # ============================================================

    def _parse_global_sections(self, content: str):

        # --------------------------------------------------------
        # BUSINESS TERM MAPPING
        # --------------------------------------------------------

        match = re.search(
            r"^\s*\*{0,2}##\s+BUSINESS TERM MAPPING:\s*\*{0,2}"
            r"(.*?)"
            r"(?=^\s*\*{0,2}##\s+INTENT MAPPING|"
            r"^\s*\*{0,2}##\s+SPECIAL RULES|"
            r"^\s*\*{0,2}#\s+TABLE:|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if match:

            for line in match.group(1).splitlines():

                line = self._clean(line)

                line = re.sub(
                    r"^\s*-\s*",
                    "",
                    line
                )

                if "→" not in line:
                    continue

                left, right = line.split(
                    "→",
                    1
                )

                self.business_term_mapping[
                    left.strip()
                ] = right.strip()

        # --------------------------------------------------------
        # INTENT MAPPING
        # --------------------------------------------------------

        match = re.search(
            r"^\s*\*{0,2}##\s+INTENT MAPPING\s*&?\s*LOGIC:\s*\*{0,2}"
            r"(.*?)"
            r"(?=^\s*\*{0,2}##\s+SPECIAL RULES|"
            r"^\s*\*{0,2}#\s+TABLE:|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if match:

            for line in match.group(1).splitlines():

                line = self._clean(line)

                line = re.sub(
                    r"^\s*-\s*",
                    "",
                    line
                )

                if "→" not in line:
                    continue

                left, right = line.split(
                    "→",
                    1
                )

                self.intent_mapping[
                    left.strip()
                ] = right.strip()

        # --------------------------------------------------------
        # SPECIAL RULES
        # --------------------------------------------------------

        match = re.search(
            r"^\s*\*{0,2}##\s+SPECIAL RULES\s*&?\s*CONSTRAINTS:\s*\*{0,2}"
            r"(.*?)"
            r"(?=^\s*\*{0,2}#\s+TABLE:|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if match:

            for line in match.group(1).splitlines():

                line = self._clean(line)

                line = re.sub(
                    r"^\s*-\s*",
                    "",
                    line
                )

                if line:
                    self.global_rules.append(line)

    # ============================================================
    # TABLE PARSING
    # ============================================================

    def _parse_tables(self, content: str):

        # Supports:
        #
        # **# TABLE: SS_PICKLIST**
        #
        # # TABLE: SS_PICKLIST
        #
        # **# TABLE: user**
        #
        table_header = re.compile(
            r"^\s*\*{0,2}"
            r"#+\s+TABLE:\s*"
            r"(.+?)"
            r"\s*\*{0,2}\s*$",
            re.IGNORECASE | re.MULTILINE
        )

        matches = list(
            table_header.finditer(content)
        )

        print(
            f"Schema table matches: {len(matches)}"
        )

        for index, match in enumerate(matches):

            table_name = self._clean(
                match.group(1)
            )

            start = match.end()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(content)

            table_content = content[
                start:end
            ]

            table = self._parse_table_block(
                table_name,
                table_content
            )

            self.tables[table_name] = table

    # ============================================================
    # SINGLE TABLE BLOCK
    # ============================================================

    def _parse_table_block(
        self,
        table_name: str,
        content: str
    ) -> Dict[str, Any]:

        table_data = {
            "name": table_name,
            "columns": {},
            "business_terms": [],
            "usage": None,
            "rules": [],
            "status": {},
            "completion_logic": [],
            "document_type_definitions": {},
            "default_output": [],
            "relationships": [],
            "query_patterns": []
        }

        # --------------------------------------------------------
        # COLUMNS
        # --------------------------------------------------------

        columns_match = re.search(
            r"^\s*COLUMNS:\s*$"
            r"(.*?)"
            r"(?=^\s*(?:USAGE|RULE|STATUS|COMPLETION LOGIC|"
            r"DOCUMENT TYPE DEFINITIONS|DEFAULT OUTPUT|"
            r"RELATIONSHIPS|QUERY PATTERNS):\s*$|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if columns_match:

            for line in columns_match.group(1).splitlines():

                line = self._clean(line)

                line = re.sub(
                    r"^\s*-\s*",
                    "",
                    line
                )

                if not line:
                    continue

                # Column:
                #
                # id
                # id (PK)
                # id (UNIQUE)
                # id (PK, UNIQUE)
                # id (PK) → user.userId

                match = re.match(
                    r"^"
                    r"([A-Za-z_][A-Za-z0-9_]*)"
                    r"(?:\s*\(([^)]*)\))?"
                    r"(?:\s*→\s*(.+))?"
                    r"$",
                    line
                )

                if not match:
                    continue

                column_name = match.group(1)

                constraints = (
                    match.group(2) or ""
                )

                reference = (
                    match.group(3)
                    if match.group(3)
                    else None
                )

                constraint_set = {
                    x.strip().upper()
                    for x in constraints.split(",")
                    if x.strip()
                }

                table_data["columns"][
                    column_name
                ] = {
                    "primary_key": "PK" in constraint_set,
                    "unique": "UNIQUE" in constraint_set,
                    "reference": (
                        reference.strip()
                        if reference
                        else None
                    )
                }

        # --------------------------------------------------------
        # BUSINESS TERMS
        # --------------------------------------------------------

        self._parse_simple_list_section(
            content,
            r"BUSINESS TERMS:",
            table_data["business_terms"]
        )

        # --------------------------------------------------------
        # USAGE
        # --------------------------------------------------------

        usage_match = re.search(
            r"^\s*USAGE:\s*(.+?)$",
            content,
            re.IGNORECASE | re.MULTILINE
        )

        if usage_match:
            table_data["usage"] = (
                self._clean(
                    usage_match.group(1)
                )
            )

        # --------------------------------------------------------
        # RULE
        # --------------------------------------------------------

        self._parse_simple_list_section(
            content,
            r"RULE:",
            table_data["rules"]
        )

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        status_match = re.search(
            r"^\s*STATUS:\s*$"
            r"(.*?)"
            r"(?=^\s*(?:COMPLETION LOGIC|"
            r"DOCUMENT TYPE DEFINITIONS|DEFAULT OUTPUT|"
            r"RELATIONSHIPS|QUERY PATTERNS):\s*$|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if status_match:

            for line in status_match.group(1).splitlines():

                line = self._clean(line)

                match = re.match(
                    r"^(\d+)\s*=\s*(.+)$",
                    line
                )

                if match:

                    table_data["status"][
                        int(match.group(1))
                    ] = match.group(2).strip()

        # --------------------------------------------------------
        # COMPLETION LOGIC
        # --------------------------------------------------------

        self._parse_simple_list_section(
            content,
            r"COMPLETION LOGIC:",
            table_data["completion_logic"]
        )

        # --------------------------------------------------------
        # DOCUMENT TYPE DEFINITIONS
        # --------------------------------------------------------

        document_match = re.search(
            r"^\s*DOCUMENT TYPE DEFINITIONS:\s*$"
            r"(.*?)"
            r"(?=^\s*(?:DEFAULT OUTPUT|RELATIONSHIPS|"
            r"QUERY PATTERNS):\s*$|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if document_match:

            for line in document_match.group(1).splitlines():

                line = self._clean(line)

                match = re.match(
                    r"^(\d+)\s*→\s*(.+)$",
                    line
                )

                if match:

                    table_data[
                        "document_type_definitions"
                    ][
                        int(match.group(1))
                    ] = match.group(2).strip()

        # --------------------------------------------------------
        # DEFAULT OUTPUT
        # --------------------------------------------------------

        self._parse_simple_list_section(
            content,
            r"DEFAULT OUTPUT:",
            table_data["default_output"]
        )

        # --------------------------------------------------------
        # RELATIONSHIPS
        # --------------------------------------------------------

        relationship_match = re.search(
            r"^\s*RELATIONSHIPS:\s*$"
            r"(.*?)"
            r"(?=^\s*QUERY PATTERNS:\s*$|"
            r"^\s*\*{0,2}---\s*\*{0,2}\s*$|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if relationship_match:

            for line in relationship_match.group(1).splitlines():

                relationship = (
                    self._normalize_relationship_line(line)
                )

                if not relationship:
                    continue

                parsed = self._parse_relationship(
                    relationship
                )

                if not parsed:
                    continue

                table_data[
                    "relationships"
                ].append(parsed)

                self.relationships.append(
                    parsed
                )

        # --------------------------------------------------------
        # QUERY PATTERNS
        # --------------------------------------------------------

        query_match = re.search(
            r"^\s*QUERY PATTERNS:\s*$"
            r"(.*?)"
            r"(?=^\s*\*{0,2}---\s*\*{0,2}\s*$|\Z)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if query_match:

            query_section = query_match.group(1)

            sql_blocks = re.findall(
                r"```sql\s*(.*?)```",
                query_section,
                re.IGNORECASE | re.DOTALL
            )

            for sql in sql_blocks:

                sql = sql.strip()

                if not sql:
                    continue

                # Try to determine a title from the
                # line before the SQL block.

                before = query_section[
                    :query_section.find(
                        "```sql"
                    )
                ]

                title = None

                lines = [
                    self._clean(x)
                    for x in before.splitlines()
                    if self._clean(x)
                ]

                if lines:
                    title = lines[-1]

                pattern = {
                    "table": table_name,
                    "title": title,
                    "sql": sql
                }

                table_data[
                    "query_patterns"
                ].append(pattern)

                self.query_patterns.append(
                    pattern
                )

        return table_data

    # ============================================================
    # SIMPLE LIST SECTION
    # ============================================================

    def _parse_simple_list_section(
        self,
        content: str,
        heading: str,
        target: List[str]
    ):

        pattern = (
            r"^\s*"
            + heading
            + r"\s*$"
            r"(.*?)"
            r"(?=^\s*(?:BUSINESS TERMS|USAGE|RULE|STATUS|"
            r"COMPLETION LOGIC|DOCUMENT TYPE DEFINITIONS|"
            r"DEFAULT OUTPUT|RELATIONSHIPS|QUERY PATTERNS):\s*$"
            r"|\Z)"
        )

        match = re.search(
            pattern,
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        if not match:
            return

        for line in match.group(1).splitlines():

            line = self._clean(line)

            line = re.sub(
                r"^\s*-\s*",
                "",
                line
            )

            if line:
                target.append(line)

    # ============================================================
    # RELATIONSHIP PARSER
    # ============================================================

    def _parse_relationship(
        self,
        relationship: str
    ) -> Optional[Dict[str, str]]:

        if "<->" not in relationship:
            return None

        left, right = relationship.split(
            "<->",
            1
        )

        left = left.strip()
        right = right.strip()

        left_parts = left.split(
            ".",
            1
        )

        right_parts = right.split(
            ".",
            1
        )

        if len(left_parts) != 2:
            return None

        if len(right_parts) != 2:
            return None

        return {
            "left_table": left_parts[0].strip(),
            "left_column": left_parts[1].strip(),
            "right_table": right_parts[0].strip(),
            "right_column": right_parts[1].strip()
        }

    # ============================================================
    # TABLE RESOLUTION
    # ============================================================

    def resolve_table_name(
        self,
        table_name: str
    ) -> Optional[str]:

        normalized = self._normalize_identifier(
            table_name
        )

        for canonical in self.tables:

            if (
                self._normalize_identifier(
                    canonical
                )
                == normalized
            ):
                return canonical

        return None

    # ============================================================
    # TABLE EXISTS
    # ============================================================

    def table_exists(
        self,
        table_name: str
    ) -> bool:

        return (
            self.resolve_table_name(
                table_name
            )
            is not None
        )

    # ============================================================
    # GET TABLE
    # ============================================================

    def get_table(
        self,
        table_name: str
    ) -> Optional[Dict[str, Any]]:

        canonical = self.resolve_table_name(
            table_name
        )

        if not canonical:
            return None

        return self.tables.get(
            canonical
        )

    # ============================================================
    # COLUMN RESOLUTION
    # ============================================================

    def resolve_column_name(
        self,
        table_name: str,
        column_name: str
    ) -> Optional[str]:

        table = self.get_table(
            table_name
        )

        if not table:
            return None

        normalized = self._normalize_identifier(
            column_name
        )

        for canonical in table["columns"]:

            if (
                self._normalize_identifier(
                    canonical
                )
                == normalized
            ):
                return canonical

        return None

    # ============================================================
    # COLUMN EXISTS
    # ============================================================

    def column_exists(
        self,
        table_name: str,
        column_name: str
    ) -> bool:

        return (
            self.resolve_column_name(
                table_name,
                column_name
            )
            is not None
        )

    # ============================================================
    # GET COLUMNS
    # ============================================================

    def get_columns(
        self,
        table_name: str
    ) -> List[str]:

        table = self.get_table(
            table_name
        )

        if not table:
            return []

        return list(
            table["columns"].keys()
        )

    # ============================================================
    # RELATIONSHIP VALIDATION
    # ============================================================

    def relationship_exists(
        self,
        table1: str,
        column1: str,
        table2: str,
        column2: str
    ) -> bool:

        t1 = self.resolve_table_name(table1)
        t2 = self.resolve_table_name(table2)

        if not t1 or not t2:
            return False

        c1 = self.resolve_column_name(
            t1,
            column1
        )

        c2 = self.resolve_column_name(
            t2,
            column2
        )

        if not c1 or not c2:
            return False

        for relationship in self.relationships:

            left_match = (
                self._normalize_identifier(
                    relationship["left_table"]
                )
                == self._normalize_identifier(t1)
                and
                self._normalize_identifier(
                    relationship["left_column"]
                )
                == self._normalize_identifier(c1)
                and
                self._normalize_identifier(
                    relationship["right_table"]
                )
                == self._normalize_identifier(t2)
                and
                self._normalize_identifier(
                    relationship["right_column"]
                )
                == self._normalize_identifier(c2)
            )

            right_match = (
                self._normalize_identifier(
                    relationship["left_table"]
                )
                == self._normalize_identifier(t2)
                and
                self._normalize_identifier(
                    relationship["left_column"]
                )
                == self._normalize_identifier(c2)
                and
                self._normalize_identifier(
                    relationship["right_table"]
                )
                == self._normalize_identifier(t1)
                and
                self._normalize_identifier(
                    relationship["right_column"]
                )
                == self._normalize_identifier(c1)
            )

            if left_match or right_match:
                return True

        return False

    # ============================================================
    # GET RELATIONSHIPS
    # ============================================================

    def get_relationships(
        self,
        table_name: Optional[str] = None
    ) -> List[Dict[str, str]]:

        if not table_name:
            return self.relationships

        canonical = self.resolve_table_name(
            table_name
        )

        if not canonical:
            return []

        normalized = self._normalize_identifier(
            canonical
        )

        return [
            relationship
            for relationship in self.relationships
            if (
                self._normalize_identifier(
                    relationship["left_table"]
                ) == normalized
                or
                self._normalize_identifier(
                    relationship["right_table"]
                ) == normalized
            )
        ]

    # ============================================================
    # GET JOIN PATHS
    # ============================================================

    def get_join_paths(self) -> List[Dict[str, str]]:
        return self.relationships

    # ============================================================
    # GET QUERY PATTERNS
    # ============================================================

    def get_query_patterns(
        self,
        table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        if not table_name:
            return self.query_patterns

        canonical = self.resolve_table_name(
            table_name
        )

        if not canonical:
            return []

        normalized = self._normalize_identifier(
            canonical
        )

        return [
            pattern
            for pattern in self.query_patterns
            if (
                self._normalize_identifier(
                    pattern["table"]
                )
                == normalized
            )
        ]

    # ============================================================
    # GET ALL TABLES
    # ============================================================

    def get_all_tables(self) -> List[str]:

        return list(
            self.tables.keys()
        )


# ================================================================
# SINGLE REGISTRY INSTANCE
# ================================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

KNOWLEDGE_DIR = os.path.join(
    BASE_DIR,
    "knowledge"
)

print(
    "Loading schema from:",
    KNOWLEDGE_DIR
)

schema_registry = SchemaRegistry(
    KNOWLEDGE_DIR
)