from langchain_core.tools import tool
from clickhouse_connect import get_client
import os
from dotenv import load_dotenv
from typing import Optional
import logging
import pandas as pd

load_dotenv()

client = get_client(
    host=os.getenv('CLICKHOUSE_HOST'),
    port=int(os.getenv('CLICKHOUSE_PORT', '443')),
    username=os.getenv('CLICKHOUSE_USER'),
    password=os.getenv('CLICKHOUSE_PASSWORD'),
    database=os.getenv('CLICKHOUSE_DATABASE', 'default')
)

logger = logging.getLogger(__name__)


@tool
def execute_clickhouse_query(query: str, limit: Optional[int] = None) -> str:
    """
    Execute a ClickHouse query and return the results as a formatted string.

    Args:
        query (str): The SQL query to execute
        limit (Optional[int]): Maximum number of rows to return

    Returns:
        str: The query results as a formatted string
    """
    try:
        result = client.query(query)
        if not result.result_rows:
            return "No results found"

        headers = [col[0] for col in result.column_names]
        output = [" | ".join(headers), "-" * len(" | ".join(headers))]

        for row in result.result_rows[:limit]:
            formatted_row = ["NULL" if cell is None else str(cell) for cell in row]
            output.append(" | ".join(formatted_row))

        return "\n".join(output)

    except Exception as e:
        return f"Error: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Example code is commented out
    pass
    # agent = Agent(tools=[ClickHouseTools()], show_tool_calls=True, markdown=True)
    # agent.print_response("Show me the first 5 rows from the request_logs table.") 