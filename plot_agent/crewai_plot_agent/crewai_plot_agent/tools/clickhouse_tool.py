import os
from typing import Any, Optional, Type

from clickhouse_connect import get_client
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field, PrivateAttr

# Load environment variables
load_dotenv()


class ClickHouseQueryInput(BaseModel):
    """Input schema for executing ClickHouse queries."""

    query: str = Field(..., description="The SQL query to execute.")
    limit: Optional[int] = Field(None, description="Maximum number of rows to return.")


class ClickHouseTool(BaseTool):
    name: str = "ClickHouse Query Executor"
    description: str = "Executes a ClickHouse query and returns the formatted results."
    args_schema: Type[BaseModel] = ClickHouseQueryInput
    _client: Any = PrivateAttr()

    def __init__(self):
        super().__init__()
        print(
            "Initializing ClickHouseTool",
            os.getenv("CLICKHOUSE_HOST"),
            os.getenv("CLICKHOUSE_PORT"),
            os.getenv("CLICKHOUSE_USER"),
            os.getenv("CLICKHOUSE_PASSWORD"),
            os.getenv("CLICKHOUSE_DATABASE"),
        )
        self._client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "443")),
            username=os.getenv("CLICKHOUSE_USER"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE", "default"),
        )

    def _run(self, query: str, limit: Optional[int] = None) -> str:
        """Executes a ClickHouse query and returns formatted results."""
        try:
            result = self._client.query(query)

            if not result.result_rows:
                return "No results found."

            # Format the results
            headers = [col[0] for col in result.column_names]
            output = [" | ".join(headers), "-" * len(" | ".join(headers))]

            for row in result.result_rows:
                formatted_row = ["NULL" if cell is None else str(cell) for cell in row]
                output.append(" | ".join(formatted_row))

            return "\n".join(output)
        except Exception as e:
            return f"Error executing ClickHouse query: {str(e)}"
