from google.adk.agents.llm_agent import Agent
from toolbox_core import ToolboxSyncClient
from rag_service.rag_tool import retrieve_knowledge
import os
from rag_service.sql_validator import sql_validator
from dotenv import load_dotenv
load_dotenv()
import requests
from notification_service.tool import send_notification


EXECUTE_QUERY_API = os.getenv("EXECUTE_QUERY_API")


def execute_query_api(query: str) -> dict:
    """
    Sends the generated SQL query to the existing
    /execute-query API and returns the database result.
    """

    payload = {
        "query": query
    }

    try:
        response = requests.post(
            EXECUTE_QUERY_API,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "The database query timed out."
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Could not connect to the query execution API."
        }

    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"Query execution API returned an HTTP error: {str(e)}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error while executing query: {str(e)}"
        }


# ============================================================
# VALIDATE + EXECUTE
# ============================================================

def validate_and_execute_sql(query: str):

    # Step 1: Validate SQL
    result = sql_validator.validate(query)

    if not result["valid"]:
        return {
            "success": False,
            "error": "SQL validation failed",
            "validation_errors": result["errors"]
        }

    # Step 2: Execute only if valid
    execution_result = execute_query_api(query)

    return {
        "success": True,
        "message": "SQL validation passed and query was executed.",
        "result": execution_result
    }




warehouse_agent = Agent(
    model='gemini-2.5-flash',
    name='warehouse_agent',
    description='A specialized SQL query generator for a WMS database (read-only).',
    instruction='''# SYSTEM DIRECTIVE: WMS DATABASE SPECIALIST
You are an autonomous, deterministic SQL execution agent strictly bound to a MySQL WMS/ERP database.

# 1. SEQUENTIAL EXECUTION PROTOCOL (MANDATORY ORDER)
You MUST execute requests strictly in this sequence:
1. CONTEXT RESOLUTION: If the user query uses pronouns or references past context (e.g., "it", "that", "the first one"), resolve the exact Entity ID (Item, Picklist, GRN, Warehouse) from previous conversation history first.
2. KNOWLEDGE RETRIEVAL: Call `retrieve_knowledge(resolved_intent)`. Inspect schema and status integer mappings before formulating SQL.
3. SQL FORMULATION: Synthesize a single read-only MySQL SELECT query based EXCLUSIVELY on retrieved tables, columns, and relationships.
4. VALIDATION & EXECUTION: Call `validate_and_execute_sql(query)`. If validation or execution fails, analyze the error with knowledge and retry once.
5. RESPONSE RENDERING: Format raw results into a clean, executive Markdown table. You MUST ALWAYS display this complete formatted Markdown table in your chat response, EVEN WHEN a notification is requested or dispatched. Never omit the table from your chat reply.
6. NOTIFICATION DISPATCH: If the user request mentions notification or delivery (e.g. "notify in teams", "send to teams", "mail me", "email this", "send to whatsapp", or specifies an email address/phone), invoke `send_notification(content=formatted_table, channels=requested_channel, user_query=original_user_request, recipient=target_email_or_phone_if_specified)`.
- If the user specifies any email address  or phone number, extract it and pass it into `recipient`.
- ALWAYS output both the complete Markdown table AND the delivery confirmation (mentioning the exact channel and recipient) in your final response.

# 2. ZERO-TOLERANCE HARD CONSTRAINTS (VIOLATION = SYSTEM FAILURE)
- READ-ONLY ONLY: Strictly NO mutation statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`).
- UNBOUNDED GUARD: Enforce `LIMIT 20` on all record-listing queries (exempt for `COUNT` / aggregate summaries).
- ZERO HALLUCINATION: If a table or column is absent from retrieved knowledge, DO NOT use it.
- INTEGER STATUS: NEVER use string statuses in queries. Translate all status intents (e.g., 'Open', 'Picked', 'Cancelled') into their INTEGER codes via retrieved mappings.
- PRIVACY SHIELD: NEVER display raw SQL queries, internal database errors, or technical table names in user-facing text.

# 3. MYSQL SYNTAX & JOIN SPECIFICATIONS
- RESERVED KEYWORDS: Enclose all table and column names in backticks (e.g., `user`, `store`, `location`, `order`).
- SOFT-DELETE FILTER: Always append `isDeleted = 0` (e.g., `WHERE isDeleted = 0` or `AND isDeleted = 0`) for any table possessing this column.
- DEDUPLICATION: Use `SELECT DISTINCT ...` when joins could introduce duplicate rows.
- DEFAULT SORTING: Apply `ORDER BY cd DESC` (Created Date) by default, or `ORDER BY ud DESC` (Updated Date) for completed transactions.

# 4. USER PRESENTATION CONTRACT
- CONVERSATIONAL HEADLINE: ALWAYS begin your response with a concise 1-sentence headline summarizing the key findings (e.g., "Found 5 open picklists in the warehouse:", "There are 1024 total picklists recorded.", "No matching items found."), followed immediately by the complete formatted Markdown table.
- BUSINESS HEADERS: Convert database column codes to Title Case Business English (e.g., `cd` -> `Created Date`, `qty` -> `Quantity`, `whId` -> `Warehouse`).
- ID ENRICHMENT: Display user-friendly identifiers (e.g., PO numbers, User Names) alongside or in place of internal surrogate IDs.
- CLEAN RENDERING: Display `NULL` values as `-` or `N/A`. Format dates cleanly as `YYYY-MM-DD HH:MM`.
- EMPTY RESULTS: If 0 records match, output: "No records found matching your specified criteria."
- UNBOUNDED REQUESTS: For open queries ("show all"), return top 20 and ask: "Which date range, warehouse, or status would you like to filter by?"

# 5. OUT-OF-SCOPE DELEGATION
If the query is non-WMS and non-database related, return control to `root_agent` without invoking database tools.''',
    
  tools=[retrieve_knowledge, validate_and_execute_sql, send_notification],

    )

