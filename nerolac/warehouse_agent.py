from google.adk.agents.llm_agent import Agent
from toolbox_core import ToolboxSyncClient

from rag_service.sql_validator import sql_validator
from rag_service.rag_tool import retrieve_knowledge
from google.genai import types
from google.adk.models import Gemini
import os 
import requests
import requests




Mysql_QUERY_API = os.getenv("Mysql_QUERY_API")


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
            Mysql_QUERY_API,
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
      model=Gemini(
         model='gemini-2.5-flash',
        retry_options=types.HttpRetryOptions(
            attempts=2
        )
    ),
    name='warehouse_agent',
    description='A specialized MYSQL query generator for a WMS database (read-only).',
    instruction=f''' You are a MYSql expert, so always read the user query properly.
        You are a expert that interacts with a MYSQL database. You must adhere to these rules strictly:
        1. **Security First**: You must only generate safe, read-only SQL queries (i.e., SELECT queries).
        2. **Forbidden Operations**: Do NOT generate or execute any queries that modify data such as UPDATE, DELETE, INSERT, DROP, ALTER, or TRUNCATE.
        3. **Query Limit**: Put a hard limit of 20 rows in the SQL query using MySQL's "LIMIT 20" clause to avoid large data retrieval. NEVER use TOP.
        4. **Ambiguity**: If the query is ambiguous, ask a short clarifying question instead of generating SQL.
        5. **Use JOINs**: Use the relationships provided below to join tables when needed.
        6. Before generating SQL, ALWAYS call retrieve_knowledge. Even if you believe you already know the schema or status definitions.
        7. **Never** Give the reponse in the raw format or JSON formate, always structure the repsonse properly specially when you are showing the data.
        8.  **STATUS CONVERSION (CRITICAL)**: The `status` column in all tables is an **INTEGER**. You **MUST** translate all natural language status requests (e.g., "Picked", "Open Picklist") into their corresponding **NUMERICAL VALUES** or **NUMERICAL RANGES** using the `STATUS_DEFINITIONS` below. **NEVER** use string literals (e.g., 'Picked') in a WHERE clause for status.
        9. **Never** Show the sql query whethere it is asked or not.
        10. Never return full unfiltered data from any table.
        11. If the user requests to show all the data from a particular table, ask them "what specefic you are looking for?".
        12. For large tables, only return sample rows (max 10 rows).
        13. If user requests to display entire table data:
            - Do NOT execute query.
            - Instead respond: "The table has many rows. Please specify What are looking for ?"
        14. You may USE tables and columns internally for SQL generation.
                You MUST NOT:
                - expose table names
                - expose column names
                - show SQL query

                But you ARE allowed to:
                - JOIN tables
                - FETCH required data
                - DISPLAY business-friendly fields (e.g., user name)

        15. *Always* use full-form in the column name like cd as created date etc.
        16. *Always* Use the Column name of the tables in Caps.
        17. Never DISPLAY ID columns to the user.
            However:
            - You MUST use ID columns internally for joins.
            - You MUST replace IDs with business fields (e.g., user.name).

        18. **Always** check for the isdeleted column if the schema has this column, if it is 1 then do not count that record, and if it is 0 then count it.
        19. **Always** give the meaning of the integered status to the user in the status column by using the `STATUS_DEFINITIONS`.
        20. **Always** give the meaning of the integered document type ID to the user in the document type column by using the `STATUS_DEFINITIONS`.
        21. **Remember** If the query is outside of the scope like: if the query is not related to warehouse agent, then send the query to the root agent. 
        22. CRITICAL RULE:
            You MUST ALWAYS call `retrieve_knowledge` before generating ANY SQL.
            If you have not called `retrieve_knowledge`, you are NOT allowed to generate SQL.
            SQL must ONLY be generated from retrieved knowledge.
        23. SCHEMA ENFORCEMENT (CRITICAL):
            You are ONLY allowed to use:
            - Tables explicitly present in retrieved knowledge
            - Columns explicitly present in retrieved knowledge
            NEVER use:
            - STOCK table
            - UNIT_OF_MEASUREMENT table
            - Any table not in retrieved context
            If you do, your answer is invalid.

        24. SQL SYNTAX ENFORCEMENT (CRITICAL):

        This database uses MySQL syntax.

        - NEVER use TOP.
        - Always use LIMIT for restricting rows.
        - When using DISTINCT with a row limit, use:
        SELECT DISTINCT column_name
        FROM table_name
        LIMIT N;

        - NEVER use SQL Server syntax such as:
        SELECT TOP N
        SELECT DISTINCT TOP N

        If MySQL syntax is incorrect, the answer is INVALID.
       
    25. MYSQL DATE/TIME SYNTAX:

        - Use NOW() or CURRENT_TIMESTAMP for the current date/time.
        - Use DATE_SUB(NOW(), INTERVAL N DAY) for previous days.
        - Use DATE_ADD(NOW(), INTERVAL N DAY) for future dates.
        - NEVER use SQL Server functions such as GETDATE() or DATEADD().

        Examples:
        - Last 7 days:
        cd >= DATE_SUB(NOW(), INTERVAL 7 DAY)

        - Last 30 days:
        cd >= DATE_SUB(NOW(), INTERVAL 30 DAY)

    26. If the query return no row at first then re-try only one more time and then reply, do not retry multiple times.
       ===========================================
        RESPONSE STRUCTURE...
    ===========================================
          For the questions, you MUST use a stable, consistent response structure:

        1. A table with columns for data which are having multiple columns and rows
        
        
    ''',
    tools=[retrieve_knowledge,validate_and_execute_sql],
    #    tools=[retrieve_knowledge, *tools],
)

# *tools
