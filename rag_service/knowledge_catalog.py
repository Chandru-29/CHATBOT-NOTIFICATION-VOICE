import os
import re
import json
import hashlib
from typing import Set, Dict, List, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge")
CACHE_FILE_PATH = os.path.join(CURRENT_DIR, "catalog_cache.json")

# Baseline tables for 100% backwards compatibility
BASELINE_KNOWN_TABLES = [
    "user", "log", "gatewaylogs",
    "ss_picklist", "ss_picklistview", "ss_picklistitem", "ss_pickliststagemap",
    "ss_pivallocation", "ss_documenttr",
    "pickuplist", "pickuplistmapping",
    "ss_supersedefefomapping",
    "item", "store", "ss_sulocation",
    "location", "ss_location",
    "warehouse", "ss_warehouse",
    "ss_whlocmap", "ss_whtypemap",
    "ss_itemcategory", "ss_relationalallltype", "ss_itemlocacnmap",
    "ss_itemcategorymap", "ss_itemminmaxandsectionmap",
    "sapstockstatus", "ss_relationalloctype", "ss_whrltmap",
    "pivheaders", "pivphases", "pivmaterialissueslip", "pivallocation",
    "movementheaders", "movementlineitems", "movementpickuplist",
    "movementsuidmapping", "movementtypes",
    "ss_mvt", "ss_document", "ss_docmvtmap",
    "accesses", "action", "submodules", "department",
    "qualityinspector", "rejmaterialdetails", "revalidation",
    "updateqistatuslog", "reqtypes", "approvalrequests",
    "assetmaster", "palletbinmapping", "pallet", "tempassetmapping",
    "resource", "ss_resourcezonemapping",
    "operationmaster", "operationtimemapping",
    "ss_suidchargingmapping", "printer",
    "intermediatefilling", "intermediatefillinggrn",
    "productionfilling", "stainersmanualweightlogs"
]

# Baseline business term mappings for backwards compatibility
BASELINE_BUSINESS_TERM_MAP: Dict[Tuple[str, ...], List[str]] = {
    ("material", "item"): ["item", "store"],
    ("sku", "store inventory"): ["store"],
    ("stock", "inventory", "available qty", "actual qty"): ["store", "ss_sulocation", "sapstockstatus"],
    ("suid",): ["ss_sulocation"],
    ("location", "bin"): ["location", "ss_location"],
    ("warehouse",): ["warehouse", "ss_warehouse", "ss_whlocmap", "ss_whrltmap"],
    ("picklist", "pick list", "pickup list", "pickuplist"): ["ss_picklist", "pickuplist", "ss_picklistview", "ss_picklistitem"],
    ("piv", "po number", "process order", "piv order", "po batch", "batch"): ["pivheaders", "pivallocation", "pivphases"],
    ("movement", "transfer", "material movement"): ["movementheaders", "movementlineitems", "movementpickuplist"],
    ("user", "assigned", "operator", "employee", "who"): ["user"],
    ("pallet",): ["assetmaster", "palletbinmapping", "pallet", "tempassetmapping"],
    ("grn",): ["store", "intermediatefillinggrn"],
    ("approval", "approval request", "req type"): ["approvalrequests", "reqtypes"],
    ("quality", "inspection", "qi", "rejected", "revalidation"): ["qualityinspector", "rejmaterialdetails", "revalidation", "updateqistatuslog"],
    ("filling", "stainer", "weight", "weighbridge"): ["intermediatefilling", "intermediatefillinggrn", "productionfilling", "stainersmanualweightlogs", "gatewaylogs"],
    ("fefo", "supersede"): ["ss_supersedefefomapping"],
    ("resource", "zone"): ["resource", "ss_resourcezonemapping"],
    ("category", "min max", "section"): ["ss_itemcategory", "ss_itemcategorymap", "ss_itemminmaxandsectionmap"],
    ("log", "audit", "endpoint"): ["log", "gatewaylogs"],
    ("printer",): ["printer"]
}


class KnowledgeCatalog:
    """
    Dynamic Knowledge & Schema Catalog.
    Automatically parses table names, columns, and business terms from all .md files.
    Maintains persistent disk cache (catalog_cache.json) and in-memory high-speed cache.
    """

    def __init__(self, knowledge_path: str = KNOWLEDGE_PATH, cache_file_path: str = CACHE_FILE_PATH):
        self.knowledge_path = knowledge_path
        self.cache_file_path = cache_file_path
        self.known_tables: Set[str] = set(BASELINE_KNOWN_TABLES)
        self.business_term_map: Dict[Tuple[str, ...], List[str]] = dict(BASELINE_BUSINESS_TERM_MAP)
        self.table_columns_map: Dict[str, List[str]] = {}
        self.file_hashes: Dict[str, str] = {}
        self.reload()

    def _compute_file_hash(self, filepath: str) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _clean_str(self, val: str) -> str:
        if not val:
            return ""
        val = val.strip().replace("`", "").replace("**", "").replace("\\", "")
        return val.replace("[", "").replace("]", "").strip()

    def reload(self, force: bool = False) -> dict:
        """
        Scans knowledge directory, discovers all tables and business terms.
        If files haven't changed and cache exists, loads from disk cache for speed.
        """
        os.makedirs(self.knowledge_path, exist_ok=True)
        current_files = [
            f for f in sorted(os.listdir(self.knowledge_path))
            if f.endswith(".md") or f.endswith(".markdown")
        ]

        # Calculate current hashes
        current_hashes = {}
        for fname in current_files:
            fpath = os.path.join(self.knowledge_path, fname)
            current_hashes[fname] = self._compute_file_hash(fpath)

        # Check if cache is fresh
        if not force and os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, "r", encoding="utf-8") as cf:
                    cached_data = json.load(cf)
                if cached_data.get("file_hashes") == current_hashes:
                    # Restore from disk cache
                    self.known_tables = set(cached_data.get("tables", []))
                    self.known_tables.update(BASELINE_KNOWN_TABLES)

                    # Restore business term map
                    cached_terms = cached_data.get("business_term_map", {})
                    restored_terms = {}
                    for k_str, v_list in cached_terms.items():
                        key_tuple = tuple(k.strip() for k in k_str.split("|||"))
                        restored_terms[key_tuple] = v_list
                    for k_tup, v_list in BASELINE_BUSINESS_TERM_MAP.items():
                        if k_tup not in restored_terms:
                            restored_terms[k_tup] = v_list
                        else:
                            for t in v_list:
                                if t not in restored_terms[k_tup]:
                                    restored_terms[k_tup].append(t)

                    self.business_term_map = restored_terms
                    self.table_columns_map = cached_data.get("table_columns", {})
                    self.file_hashes = current_hashes
                    return {
                        "status": "loaded_from_cache",
                        "tables_count": len(self.known_tables),
                        "terms_count": len(self.business_term_map)
                    }
            except Exception as e:
                print(f"Note: Could not load catalog cache: {e}. Rebuilding...")

        # Parse from fresh markdown files
        discovered_tables: Set[str] = set(BASELINE_KNOWN_TABLES)
        discovered_terms: Dict[Tuple[str, ...], List[str]] = dict(BASELINE_BUSINESS_TERM_MAP)
        discovered_cols: Dict[str, List[str]] = {}

        for fname in current_files:
            fpath = os.path.join(self.knowledge_path, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            self._parse_file_content(content, discovered_tables, discovered_terms, discovered_cols)

        self.known_tables = discovered_tables
        self.business_term_map = discovered_terms
        self.table_columns_map = discovered_cols
        self.file_hashes = current_hashes

        # Persist to disk cache
        self._save_cache()

        return {
            "status": "reparsed",
            "tables_count": len(self.known_tables),
            "terms_count": len(self.business_term_map),
            "files": current_files
        }

    def _parse_file_content(
        self,
        content: str,
        tables_set: Set[str],
        terms_dict: Dict[Tuple[str, ...], List[str]],
        cols_dict: Dict[str, List[str]]
    ):
        # 1. Discover all tables (supports '# TABLE: xxx', '## TABLE: xxx', '**# TABLE: xxx**')
        table_matches = re.finditer(
            r"^\s*\*{0,2}#+\s*TABLE:\s*([^\r\n*]+)",
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
        for tm in table_matches:
            tbl_name = self._clean_str(tm.group(1)).lower()
            if tbl_name:
                tables_set.add(tbl_name)

        # 2. Extract Business Terms across all sections (both global and table-specific)
        for line in content.splitlines():
            line_clean = line.strip()
            if ("→" in line_clean or "->" in line_clean) and '"' in line_clean:
                parts = re.split(r'→|->', line_clean, maxsplit=1)
                left = parts[0].strip()
                right = parts[1].strip() if len(parts) > 1 else ""

                raw_terms = [self._clean_str(t).lower() for t in re.findall(r'"([^"]+)"', left) if t]
                target_str = self._clean_str(right).lower()
                target_tbl = target_str.split(".")[0].strip()

                if raw_terms and target_tbl:
                    tables_set.add(target_tbl)
                    term_tuple = tuple(raw_terms)
                    if term_tuple not in terms_dict:
                        terms_dict[term_tuple] = []
                    if target_tbl not in terms_dict[term_tuple]:
                        terms_dict[term_tuple].append(target_tbl)

        # 3. Extract Table-specific sections: Business Terms without arrow and Columns
        table_sections = re.split(r'\n(?=\s*\*{0,2}#+\s*TABLE:\s*)', content, flags=re.IGNORECASE)
        for sec in table_sections:
            tbl_header = re.search(r'^\s*\*{0,2}#+\s*TABLE:\s*([^\r\n*]+)', sec, flags=re.MULTILINE | re.IGNORECASE)
            if not tbl_header:
                continue
            cur_tbl = self._clean_str(tbl_header.group(1)).lower()
            if not cur_tbl:
                continue
            tables_set.add(cur_tbl)

            # Check inside table BUSINESS TERMS for lines without arrows
            bt_block = re.search(
                r'BUSINESS TERMS:\s*(.*?)(?=\n(?:COLUMNS:|USAGE:|STATUS:|RELATIONSHIPS:|QUERY PATTERNS:|---\s*$|\Z))',
                sec,
                flags=re.IGNORECASE | re.DOTALL
            )
            if bt_block:
                for bl in bt_block.group(1).splitlines():
                    if ("→" not in bl and "->" not in bl) and '"' in bl:
                        terms = [self._clean_str(t).lower() for t in re.findall(r'"([^"]+)"', bl) if t]
                        if terms:
                            t_tup = tuple(terms)
                            if t_tup not in terms_dict:
                                terms_dict[t_tup] = []
                            if cur_tbl not in terms_dict[t_tup]:
                                terms_dict[t_tup].append(cur_tbl)

            # Extract columns inside this table block
            col_block = re.search(
                r'COLUMNS:\s*(.*?)(?=\n(?:USAGE:|STATUS:|COMPLETION LOGIC:|DOCUMENT TYPE DEFINITIONS:|RULE:|RELATIONSHIPS:|QUERY PATTERNS:|---\s*$|\Z))',
                sec,
                flags=re.IGNORECASE | re.DOTALL
            )
            if col_block:
                cols = []
                for line in col_block.group(1).splitlines():
                    clean_l = self._clean_str(line)
                    if not clean_l or clean_l.startswith("-"):
                        continue
                    col_name = clean_l.split()[0]
                    if col_name and col_name not in cols:
                        cols.append(col_name)
                cols_dict[cur_tbl] = cols

    def _save_cache(self):
        try:
            # Serialize business_term_map with delimiter for tuple keys
            serialized_terms = {
                "|||".join(k): v
                for k, v in self.business_term_map.items()
            }
            cache_data = {
                "file_hashes": self.file_hashes,
                "tables": sorted(list(self.known_tables)),
                "business_term_map": serialized_terms,
                "table_columns": self.table_columns_map
            }
            with open(self.cache_file_path, "w", encoding="utf-8") as cf:
                json.dump(cache_data, cf, indent=2)
        except Exception as e:
            print("Warning: Could not save catalog cache:", e)

    def get_known_tables(self) -> List[str]:
        return sorted(list(self.known_tables))

    def get_business_term_map(self) -> Dict[Tuple[str, ...], List[str]]:
        return self.business_term_map

    def get_table_columns(self, table_name: str) -> List[str]:
        normalized = self._clean_str(table_name).lower()
        return self.table_columns_map.get(normalized, [])


# Singleton instance
catalog = KnowledgeCatalog()
