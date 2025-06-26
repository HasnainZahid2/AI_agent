# # math_mcp_server.py
# from mcp.server.fastmcp import FastMCP

# mcp = FastMCP("Math")

# # Prompts
# @mcp.prompt()
# def example_prompt(question: str) -> str:
#     return f"""
#     You are a math assistant. Answer the question.
#     Question: {question}
#     """

# @mcp.prompt()
# def system_prompt() -> str:
#     return """
#     You are an AI assistant use the tools if needed.
#     """

# # Resources
# @mcp.resource("greeting://{name}")
# def get_greeting(name: str) -> str:
#     return f"Hello, {name}!"

# @mcp.resource("config://app")
# def get_config() -> str:
#     return "App configuration here"

# # Tools
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     return a + b

# @mcp.tool()
# def multiply(a: int, b: int) -> int:
#     return a * b

# if __name__ == "__main__":
#     mcp.run()  # OR: mcp.run(transport="streamable-http") for HTTP

# math_mcp_server.py
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import OperationalError, ProgrammingError

mcp = FastMCP("Math")

# Prompts
@mcp.prompt()
def example_prompt(question: str) -> str:
    return f"""
    You are a math assistant. Answer the question.
    Question: {question}
    """
@mcp.prompt()
def system_prompt() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
    You are an AI assistant. Today is {today}.
    Use tools if needed, especially when answering questions about time-based data.
    - Convert time_spent from milliseconds to hours/minutes/seconds
    - Use human-friendly responses
    - Never show raw SQL unless the user explicitly asks for it
    - Use date ranges and categories smartly when analyzing
    """

# Resources
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name}!"

@mcp.resource("config://app")
def get_config() -> str:
    return "App configuration here"

# Tools: Math
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     return a + b

# @mcp.tool()
# def multiply(a: int, b: int) -> int:
#     return a * b

# @mcp.tool()
# def power(a: int, b: int) -> int:
#     return a ** b

# === PostgreSQL Helper ===

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname="usage_data",
            user="postgres",
            password="12345678",
            host="localhost",
            port="5432"
        )
    except OperationalError as e:
        raise RuntimeError(f"Database connection failed: {e.pgerror or str(e)}")


@mcp.tool()
def query_sql(sql: str) -> list[dict]:
    """
    Run a SELECT SQL query on the usage_data PostgreSQL database and return the results.
    Only SELECT queries are allowed for safety.

    ## Usage:
    This tool executes user-provided SELECT SQL statements on the `usage_logs` table 
    of the `usage_data` PostgreSQL database and returns the result as a list of dictionaries 
    where each dictionary represents a row.

    ## Table: usage_logs
    Columns:
    - id (int): Unique identifier for each log entry.
    - date (date): The date of usage (e.g., '2025-04-17').
    - time_slot (text): Time slot or usage source (e.g., 'apps', 'browser').
    - app_name (text): Name of the application used (e.g., 'Code.exe').
    - time_spent (int): Time spent in milliseconds (e.g., 3156017).
    - category (text): Category of the app (e.g., 'Code', 'Utilities').
    - description (text): Description or label of the app (e.g., 'Visual Studio Code').
    - domain (text): Associated domain if applicable (e.g., 'chatgpt.com').

    ## Output:
    Returns a list of dictionaries like:
    [
        {
            "id": 7689,
            "date": "2025-04-17",
            "time_slot": "apps",
            "app_name": "Code.exe",
            "time_spent": 3156017,
            "category": "Code",
            "description": "Visual Studio Code",
            "domain": null
        },
        ...
    ]
    ## Notes:
    - The `time_spent` field is returned in **milliseconds** for internal computation only.
    - The AI will convert this value into a human-readable format (e.g., **4 hours, 22 minutes, 31 seconds**) when presenting it to the user.
    - **Milliseconds will never be shown to the user directly.**
    - Use human-friendly responses

    ## Constraints:
    - Only SELECT statements are allowed. Other query types (INSERT, UPDATE, DELETE, etc.) will raise an error.
    - Ensure valid SQL syntax. Errors will be caught and returned with appropriate messages.

    """
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
        if not result:
            return "No data found for this date range. Please try a different time period."
        return result

    except ProgrammingError as e:
        raise RuntimeError(f"SQL error: {e.pgerror or str(e)}")

    except OperationalError as e:
        raise RuntimeError(f"Database access error: {e.pgerror or str(e)}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

    finally:
        if conn:
            conn.close()


# Run the MCP Server
if __name__ == "__main__":
    mcp.run()  # OR: mcp.run(transport="streamable-http") for HTTP
