# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from toolbox_core import ToolboxSyncClient
# from dotenv import load_dotenv
# import pymysql
# import os
# import re


# load_dotenv()

# app = FastAPI()


# # ============================================================
# # MCP TOOLBOX CONNECTION
# # ============================================================

# toolbox = ToolboxSyncClient(
#     os.getenv("TOOLBOX_URL")
# )

# tools = toolbox.load_toolset("sql-toolset")

# if not tools:
#     raise Exception("No tools found in sql-toolset")

# print("[INIT] Loaded tools:", tools)


# # ============================================================
# # REQUEST MODEL
# # ============================================================

# class ExecuteQueryRequest(BaseModel):
#     query: str


# # ============================================================
# # MYSQL CONNECTION
# # ============================================================

# def get_mysql_connection():
#     return pymysql.connect(
#         host=os.getenv("MYSQL_HOST", "13.203.218.252"),
#         port=int(os.getenv("MYSQL_PORT", "3306")),
#         user=os.getenv("MYSQL_USER", "sa"),
#         password=os.getenv("MYSQL_PASSWORD"),
#         database=os.getenv("MYSQL_DATABASE", "UAT"),
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True,
#     )


# # ============================================================
# # SQL VALIDATION
# # ============================================================

# def validate_select_query(query: str):

#     query = query.strip()

#     if not query:
#         raise HTTPException(
#             status_code=400,
#             detail="Query cannot be empty"
#         )

#     # Only SELECT statements
#     if not re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
#         raise HTTPException(
#             status_code=400,
#             detail="Only SELECT queries are allowed"
#         )

#     # Remove trailing semicolon for validation
#     clean_query = query.rstrip(";").strip()

#     # Prevent multiple statements
#     if ";" in clean_query:
#         raise HTTPException(
#             status_code=400,
#             detail="Multiple SQL statements are not allowed"
#         )

#     # Block dangerous SQL keywords
#     forbidden = [
#         "INSERT",
#         "UPDATE",
#         "DELETE",
#         "DROP",
#         "TRUNCATE",
#         "ALTER",
#         "CREATE",
#         "RENAME",
#         "REPLACE",
#         "GRANT",
#         "REVOKE",
#     ]

#     query_upper = clean_query.upper()

#     for word in forbidden:
#         if re.search(rf"\b{word}\b", query_upper):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Unsafe SQL keyword detected: {word}"
#             )

#     return clean_query


# # ============================================================
# # EXECUTE QUERY
# # ============================================================

# @app.post("/execute-query")
# def execute_query(request: ExecuteQueryRequest):

#     query = validate_select_query(request.query)

#     print("\n======================================")
#     print("[API] Received SELECT query:")
#     print(query)
#     print("======================================")

#     connection = None

#     try:

#         connection = get_mysql_connection()

#         with connection.cursor() as cursor:

#             print("[MYSQL] Executing query...")

#             cursor.execute(query)

#             result = cursor.fetchall()

#             print(
#                 f"[MYSQL] Query successful. "
#                 f"Rows returned: {len(result)}"
#             )

#         return {
#             "message": "Query executed successfully",
#             "executedQuery": query,
#             "rowCount": len(result),
#             "result": result,
#         }

#     except pymysql.MySQLError as e:

#         print("[MYSQL ERROR]", str(e))

#         raise HTTPException(
#             status_code=500,
#             detail=f"MySQL execution failed: {str(e)}"
#         )

#     except Exception as e:

#         print("[ERROR]", str(e))

#         raise HTTPException(
#             status_code=500,
#             detail=f"Query execution failed: {str(e)}"
#         )

#     finally:

#         if connection:
#             connection.close()








from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from toolbox_core import ToolboxSyncClient
from dotenv import load_dotenv
import pymysql
import os
import re


load_dotenv()


router = APIRouter()


# ============================================================
# MCP TOOLBOX CONNECTION
# ============================================================

# toolbox = ToolboxSyncClient(
#     os.getenv("TOOLBOX_URL")
# )

# tools = toolbox.load_toolset("sql-toolset")

# if not tools:
#     raise Exception("No tools found in sql-toolset")

# print("[INIT] Loaded tools:", tools)


# ============================================================
# REQUEST MODEL
# ============================================================

class ExecuteQueryRequest(BaseModel):
    query: str


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_mysql_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "10.1.2.167"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "sa"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "uat"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


# ============================================================
# SQL VALIDATION
# ============================================================

def validate_select_query(query: str):

    query = query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    # Only SELECT statements
    if not re.match(
        r"^\s*SELECT\b",
        query,
        re.IGNORECASE
    ):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed"
        )

    # Remove trailing semicolon for validation
    clean_query = query.rstrip(";").strip()

    # Prevent multiple statements
    if ";" in clean_query:
        raise HTTPException(
            status_code=400,
            detail="Multiple SQL statements are not allowed"
        )

    # Block dangerous SQL keywords
    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "RENAME",
        "REPLACE",
        "GRANT",
        "REVOKE",
    ]

    query_upper = clean_query.upper()

    for word in forbidden:

        if re.search(
            rf"\b{word}\b",
            query_upper
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsafe SQL keyword detected: {word}"
                )
            )

    return clean_query


# ============================================================
# EXECUTE QUERY
# ============================================================


# ============================================================
# TABLE NAME CASE NORMALIZER (Linux MySQL Case-Sensitivity Fix)
# ============================================================

_TABLE_CASE_MAP = None

def get_exact_table_map(connection):
    global _TABLE_CASE_MAP
    if _TABLE_CASE_MAP is None:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [list(r.values())[0] for r in cursor.fetchall()]
                _TABLE_CASE_MAP = {t.lower(): t for t in tables}
        except Exception as e:
            print("[TABLE MAP ERROR]", str(e))
            _TABLE_CASE_MAP = {}
    return _TABLE_CASE_MAP

def normalize_table_names(query: str, table_map: dict) -> str:
    if not table_map:
        return query
    for low, exact in table_map.items():
        if low.lower() == exact:
            continue
        # 1. Replace with backticks: `pickuplist` -> `pickupList`
        query = re.sub(rf'`{re.escape(low)}`', f'`{exact}`', query, flags=re.IGNORECASE)
        # 2. Replace without backticks after FROM or JOIN
        query = re.sub(rf'\b(FROM|JOIN)\s+{re.escape(low)}\b', rf'\1 {exact}', query, flags=re.IGNORECASE)
    return query

@router.post("/execute-query")
def execute_query(
    request: ExecuteQueryRequest
):

    query = validate_select_query(
        request.query
    )

    print("\n======================================")
    print("[API] Received SELECT query:")
    print(query)
    print("======================================")

    connection = None

    try:

        connection = get_mysql_connection()
        table_map = get_exact_table_map(connection)
        query = normalize_table_names(query, table_map)

        with connection.cursor() as cursor:

            print("[MYSQL] Executing query...")

            cursor.execute(query)

            result = cursor.fetchall()

            print(
                f"[MYSQL] Query successful. "
                f"Rows returned: {len(result)}"
            )

        return {
            "message": "Query executed successfully",
            "executedQuery": query,
            "rowCount": len(result),
            "result": result,
        }

    except pymysql.MySQLError as e:

        print(
            "[MYSQL ERROR]",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"MySQL execution failed: "
                f"{str(e)}"
            )
        )

    except Exception as e:

        print(
            "[ERROR]",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Query execution failed: "
                f"{str(e)}"
            )
        )

    finally:

        if connection:
            connection.close()