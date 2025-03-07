from typing import List, Optional, Dict, Any
from clickhouse_connect import get_client
from agno.agent import Agent
from agno.tools import Toolkit
from agno.utils.log import logger

class ClickHouseTools(Toolkit):
    def __init__(self):
        super().__init__(name="clickhouse_tools")
        self.register(self.execute_query)
        self.client = get_client(
            host='clickhouse-tfy-llm-gateway-infra.tfy-usea1-ctl.devtest.truefoundry.tech',
            port=443,
            username='user',
            password='xWx9HCN51LPVLsWK1ZPrZPIJrneuZ8sdftvX32tvwAkEjWNx',
            database='default'
        )

    def execute_query(self, query: str, limit: Optional[int] = None) -> str:
        """
        Executes a ClickHouse query and returns the results.

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

# Example usage
if __name__ == "__main__":
    agent = Agent(tools=[ClickHouseTools()], show_tool_calls=True, markdown=True)
    agent.print_response("Show me the first 5 rows from the request_logs table.") 