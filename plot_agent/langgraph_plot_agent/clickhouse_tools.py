import logging
import os
from typing import Union

from clickhouse_connect import get_client
from dotenv import load_dotenv
from langchain_core.tools import tool
from traceloop.sdk.decorators import task

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize ClickHouse client
client = get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "443")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DATABASE", "default"),
)


@tool
# @traceloop_tool(name="execute_clickhouse_query")
@task(name="execute_clickhouse_query")
def execute_clickhouse_query(query: str, limit: Union[int, None] = None) -> str:
    """Execute a ClickHouse query and return formatted results.

    Args:
        query: The SQL query to execute against ClickHouse
        limit: Optional maximum number of rows to return

    Returns:
        A formatted string containing the query results in a tabular format
    """
    try:
        logger.info(f"Executing ClickHouse query: {query}")

        # Add LIMIT clause if specified
        if limit:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        result = client.query(query)

        if not result.result_rows:
            return "No results found"

        # Format the results as a string
        output = []
        # Add column headers
        headers = [col[0] for col in result.column_names]
        logger.info(f"Query returned columns: {headers}")
        output.append(" | ".join(headers))

        # Add separator line
        output.append("-" * len(" | ".join(headers)))

        # Add rows
        for row in result.result_rows:
            formatted_row = []
            for cell in row:
                if cell is None:
                    formatted_row.append("NULL")
                else:
                    formatted_row.append(str(cell))
            output.append(" | ".join(formatted_row))

        result_str = "\n".join(output)
        logger.info(f"Query returned {len(result.result_rows)} rows")
        return result_str

    except Exception as e:
        logger.warning(f"Failed to execute ClickHouse query: {e}")
        return f"Error: {str(e)}"
