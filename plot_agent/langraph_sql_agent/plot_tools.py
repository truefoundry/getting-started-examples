from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from agno.agent import Agent
from agno.tools import Toolkit
from agno.utils.log import logger
import os
import uuid
from matplotlib.ticker import FuncFormatter
from langchain_core.tools import tool

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

@tool
def create_plot(
    data: str,
    plot_type: str,
    x_col: str,
    y_col: Optional[str] = None,
    title: Optional[str] = None,
    hue: Optional[str] = None,
    figsize: Optional[List[float]] = [12, 8],
    style: Optional[str] = "seaborn-v0_8-darkgrid",
    palette: Optional[str] = "husl",
    output_path: Optional[str] = None
) -> str:
    """Create a visualization plot from tabular data.

    This function creates various types of plots (line, bar, scatter, histogram) using 
    the provided tabular data. It handles plot styling, saving, and returns the output path.

    Args:
        data (str): Tabular data in pipe-separated string format
        plot_type (str): Type of plot to create ('line', 'bar', 'scatter', 'histogram')
        x_col (str): Column name to use for x-axis
        y_col (Optional[str]): Column name to use for y-axis. Not required for histograms.
        title (Optional[str]): Plot title. If None, auto-generated from plot type and columns
        hue (Optional[str]): Column name to use for color grouping
        figsize (Optional[List[float]]): Figure dimensions [width, height] in inches
        style (Optional[str]): Matplotlib/Seaborn style to use
        palette (Optional[str]): Color palette name for the plot
        output_path (Optional[str]): Path to save plot. If None, auto-generated.

    Returns:
        str: Path where the plot was saved

    Raises:
        ValueError: If plot creation fails or plot type is unsupported
    """
    try:
        if output_path is None:
            filename = f"plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.png"
            output_path = os.path.join(PLOTS_DIR, filename)
        elif not os.path.isabs(output_path):
            output_path = os.path.join(PLOTS_DIR, output_path)

        plt.style.use(style)

        df = pd.read_csv(pd.compat.StringIO(data), sep='|').apply(lambda x: x.str.strip())

        plt.figure(figsize=tuple(figsize))

        if plot_type == 'line':
            sns.lineplot(data=df, x=x_col, y=y_col, hue=hue, marker='o')
        elif plot_type == 'bar':
            sns.barplot(data=df, x=x_col, y=y_col, hue=hue)
        elif plot_type == 'scatter':
            sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue)
        elif plot_type == 'histogram':
            sns.histplot(data=df, x=x_col, hue=hue, bins=30)
        else:
            raise ValueError(f"Unsupported plot type: {plot_type}")

        plt.title(title or f'{plot_type.capitalize()} Plot of {y_col or x_col}', pad=20)
        plt.xlabel(x_col)
        if y_col:
            plt.ylabel(y_col)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    except Exception as e:
        raise ValueError(f"Failed to create plot: {e}")

@tool
def parse_tabular_data(data: str) -> pd.DataFrame:
    """Convert tabular string data to pandas DataFrame.
    
    This function parses tabular data in string format (either space or pipe separated) 
    into a pandas DataFrame. It handles data type conversion for numeric and datetime columns,
    with special handling for cost columns to ensure positive values.

    Args:
        data (str): String containing tabular data with headers in first row.
                   Can be space-separated or pipe-separated format.

    Returns:
        pd.DataFrame: Parsed data as a pandas DataFrame with appropriate data types.
                     Empty DataFrame if input is empty.

    Raises:
        ValueError: If parsing fails due to invalid data format.
    """
    try:
        # Check if data is empty
        if not data or data.strip() == "":
            logger.warning("Empty data provided for parsing")
            return pd.DataFrame()
        
        # Split the data into lines and get headers
        lines = data.strip().split('\n')
        
        # Debug the raw data
        logger.info(f"Parsing tabular data with {len(lines)} lines")
        if len(lines) > 0:
            logger.info(f"First line: {lines[0]}")
        
        # Extract headers - handle both space-separated and pipe-separated formats
        if '|' in lines[0]:
            headers = [col.strip() for col in lines[0].split('|') if col.strip()]
        else:
            headers = [col.strip() for col in lines[0].split() if col.strip()]
        
        logger.info(f"Extracted headers: {headers}")
        
        # Parse the data rows
        rows = []
        for line in lines[1:]:
            if line.strip() and not line.startswith('-'):  # Skip empty lines and separator lines
                if '|' in line:
                    row = [val.strip() for val in line.split('|') if val.strip()]
                else:
                    row = [val.strip() for val in line.split() if val.strip()]
                
                # Ensure row has the same length as headers
                if len(row) == len(headers):
                    rows.append(row)
                else:
                    logger.warning(f"Skipping row with mismatched columns: {line}")
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Convert data types where possible
        for col in df.columns:
            # Special handling for cost column to ensure positive float values
            if 'cost' in col.lower():
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Ensure positive values for cost
                df[col] = df[col].abs()
            # Try to convert other columns to numeric
            else:
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    # Try to convert to datetime if 'time' or 'date' in column name
                    if 'time' in col.lower() or 'date' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except:
                            pass
        
        logger.info(f"Successfully parsed data into DataFrame with shape {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.warning(f"Failed to parse tabular data: {e}")
        raise ValueError(f"Failed to parse tabular data: {e}")

# Example usage
if __name__ == "__main__":
    # Example code is commented out
    pass
    # Create a sample agent with plot tools
    # agent = Agent(tools=[PlotTools()], show_tool_calls=True, markdown=True)
    
    # # Example data
    # sample_data = """
    # created_at | cost | model_name
    # 2023-01-01 | 0.1 | gpt-4
    # 2023-01-02 | 0.2 | gpt-3.5
    # 2023-01-03 | 0.15 | gpt-4
    # 2023-01-04 | 0.25 | gpt-3.5
    # """
    
    # # Create a test plot
    # plot_tools = PlotTools()
    # plot_tools.create_plot(
    #     data=sample_data.strip(),
    #     plot_type="line",
    #     x_col="created_at",
    #     y_col="cost",
    #     title="Cost Over Time by Model",
    #     hue="model_name"
    # ) 