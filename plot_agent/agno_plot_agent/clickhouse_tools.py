from typing import List, Optional, Dict, Any
from clickhouse_connect import get_client
from agno.agent import Agent
from agno.tools import Toolkit
from agno.utils.log import logger
import os
from dotenv import load_dotenv

class ClickHouseTools(Toolkit):
    def __init__(self):
        super().__init__(name="clickhouse_tools")
        self.register(self.execute_query)
        
        # Load environment variables
        load_dotenv()
        
        self.client = get_client(
            host=os.getenv('CLICKHOUSE_HOST'),
            port=int(os.getenv('CLICKHOUSE_PORT', '443')),
            username=os.getenv('CLICKHOUSE_USER'),
            password=os.getenv('CLICKHOUSE_PASSWORD'),
            database=os.getenv('CLICKHOUSE_DATABASE', 'default')
        )

    def execute_query(self, query: str, limit: Optional[int] = None) -> str:
        """
        Use this function to execute a ClickHouse query and return the results from the database back so that it can be used for plotting.

        Args:
            query (str): The SQL query to execute
            limit (Optional[int]): Maximum number of rows to return
        Returns:
            str: The query results as a formatted string

        """
        try:
            logger.info(f"Executing ClickHouse query: {query}")
            
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

# Example usage
if __name__ == "__main__":
    agent = Agent(tools=[ClickHouseTools()], show_tool_calls=True, markdown=True)
    agent.print_response("Show me the first 5 rows from the request_logs table.") 