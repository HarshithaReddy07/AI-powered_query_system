import json
import os
import pymssql
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete",
    "drop", "alter", "truncate",
    "exec", "execute", "merge",
    "create"
]

def is_safe_select(query: str) -> bool:
    lower_query = query.lower()

    if not lower_query.startswith("select"):
        return False

    if any(keyword in lower_query for keyword in FORBIDDEN_KEYWORDS):
        return False

    if ";" in lower_query[:-1]:  # Prevent multiple statements
        return False

    return True

def lambda_handler(event, context):
    try:
        if "query" not in event:
            return {
                "success": False,
                "data": None,
                "error": "Missing 'query'"
            }

        query = event["query"].strip()

        logger.info(f"Received query: {query}")

        # Allow only SELECT
        if not is_safe_select(query):
            logger.warning(f"Blocked unsafe query: {query}")
            return {
                "success": False,
                "data": None,
                "error": "Only SELECT queries are allowed"
            }

        conn = pymssql.connect(
            server=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(os.environ.get("DB_PORT", 1433)),
            timeout=5,
            login_timeout=5
        )

        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return {
            "success": True,
            "data": results,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }