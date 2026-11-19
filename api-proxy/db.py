import pyodbc

print("DB MODULE LOADED")

# ---------------------------------------------------
# DB CONFIG & CONNECTION HELPER
# ---------------------------------------------------
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=3.109.55.223;"
    # "SERVER=10.1.2.167;"
    "DATABASE=acp_swms;"
    "UID=sa;"
    "PWD=Mobillor@2021"
)

_conn = None

def get_connection():
    """Returns an active DB connection, reconnecting if closed or dropped."""
    global _conn
    if _conn is None:
        _conn = pyodbc.connect(CONNECTION_STRING)
    else:
        # Test if connection is still alive
        try:
            _conn.execute("SELECT 1")
        except Exception:
            print("DB Connection stale or lost. Reconnecting...")
            try:
                _conn.close()
            except Exception:
                pass
            _conn = pyodbc.connect(CONNECTION_STRING)
    return _conn


# Initial connection test at startup
try:
    get_connection()
    print("DB Connected Successfully")
except Exception as e:
    print("DB INITIAL CONNECTION ERROR:", str(e))

# ---------------------------------------------------
#  UPSERT FUNCTION
# ---------------------------------------------------
def upsert_token_usage(
    userId,
    sessionId,
    total,
    prompt,
    completion,
    appName
):
    print("DB FUNCTION CALLED")

    query = """
    MERGE token_usage AS target

    USING (
        SELECT ? AS user_id,
               ? AS session_id
    ) AS source

    ON target.user_id = source.user_id
       AND target.session_id = source.session_id

    WHEN MATCHED THEN
        UPDATE SET
            total_tokens = target.total_tokens + ?,
            prompt_tokens = target.prompt_tokens + ?,
            completion_tokens = target.completion_tokens + ?,
            total_calls = target.total_calls + 1,
            appName = ?,
            updated_at = GETDATE()

    WHEN NOT MATCHED THEN
        INSERT (
            user_id,
            session_id,
            total_tokens,
            prompt_tokens,
            completion_tokens,
            total_calls,
            appName
        )
        VALUES (
            ?, ?, ?, ?, ?, 1, ?
        );
    """

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                query,

                # USING
                userId,
                sessionId,

                # WHEN MATCHED
                total,
                prompt,
                completion,
                appName,

                # WHEN NOT MATCHED
                userId,
                sessionId,
                total,
                prompt,
                completion,
                appName
            )

            conn.commit()

        print(
            "DB write success:",
            userId,
            sessionId,
            appName
        )

        return True

    except Exception as e:
        print(
            "DB ERROR in upsert_token_usage:",
            str(e)
        )

        return False
