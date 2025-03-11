from typing import List, Optional, Dict, Any
from clickhouse_connect import get_client
from langchain_core.tools import tool
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClickHouseTools:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.client = get_client(
            host=os.getenv('CLICKHOUSE_HOST'),
            port=int(os.getenv('CLICKHOUSE_PORT', '443')),
            username=os.getenv('CLICKHOUSE_USER'),
            password=os.getenv('CLICKHOUSE_PASSWORD'),
            database=os.getenv('CLICKHOUSE_DATABASE', 'default')
        )

    @tool("execute_query", return_direct=False)
    def execute_query_tool(self, query: str, limit: Optional[int] = None) -> str:
        """
        Executes a ClickHouse SQL query and returns the results.

        Args:
            query (str): The SQL query to execute
            limit (Optional[int]): Maximum number of rows to return
        Returns:
            str: The query results as a formatted string
        """
        try:
            logger.info(f"Executing ClickHouse query: {query}")
            if limit:
                query = f"{query} LIMIT {limit}"
            
            result = self.client.query(query)
            
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
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes a ClickHouse SQL query and returns the results in a structured format.

        Args:
            query (str): The SQL query to execute
            limit (Optional[int]): Maximum number of rows to return
        Returns:
            Dict: The query results with column_names and rows
        """
        try:
            logger.info(f"Executing ClickHouse query: {query}")
            if limit:
                query = f"{query} LIMIT {limit}"
            
            result = self.client.query(query)
            
            if not result.result_rows:
                return {
                    "query": query,
                    "column_names": [],
                    "rows": [],
                    "error": None
                }
            
            # Extract column names and rows
            column_names = [col[0] for col in result.column_names]
            
            # Convert rows to list of strings
            rows = []
            for row in result.result_rows:
                formatted_row = []
                for cell in row:
                    if cell is None:
                        formatted_row.append("NULL")
                    else:
                        formatted_row.append(str(cell))
                rows.append(formatted_row)
            
            logger.info(f"Query returned {len(rows)} rows")
            
            return {
                "query": query,
                "column_names": column_names,
                "rows": rows,
                "error": None
            }
            
        except Exception as e:
            logger.warning(f"Failed to execute ClickHouse query: {e}")
            return {
                "query": query,
                "column_names": [],
                "rows": [],
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    tools = ClickHouseTools()
    result = tools.execute_query("SELECT * FROM request_logs LIMIT 5")
    print(result) 