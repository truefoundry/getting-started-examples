from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from agno.agent import Agent
from agno.tools import Toolkit
from agno.utils.log import logger

class PlotTools(Toolkit):
    def __init__(self):
        super().__init__(name="plot_tools")
        self.register(self.create_plot)
        
    def _parse_tabular_data(self, data: str) -> pd.DataFrame:
        """Convert tabular string data to pandas DataFrame."""
        try:
            # Split the data into lines and get headers
            lines = data.strip().split('\n')
            headers = [col.strip() for col in lines[0].split('|')]
            
            # Parse the data rows
            rows = []
            for line in lines[1:]:
                if line.strip():  # Skip empty lines
                    row = [val.strip() for val in line.split('|')]
                    rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Convert data types where possible
            for col in df.columns:
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    # Try to convert to datetime if 'time' or 'date' in column name
                    if 'time' in col.lower() or 'date' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except:
                            pass
            return df
        except Exception as e:
            logger.warning(f"Failed to parse tabular data: {e}")
            raise ValueError(f"Failed to parse tabular data: {e}")

    def create_plot(
        self,
        data: str,
        plot_type: str,
        x_col: str,
        y_col: Optional[str] = None,
        title: Optional[str] = None,
        hue: Optional[str] = None,
        figsize: Optional[List[float]] = [12, 8],  # Increased default figure size
        style: Optional[str] = "seaborn-v0_8-darkgrid",
        palette: Optional[str] = "husl",
        output_path: Optional[str] = "plot.png"
    ) -> str:
        """
        Create a visualization based on the input data and plot type.
        
        Args:
            data: Tabular data as string with columns separated by '|' and rows by newlines
            plot_type: Type of plot ('line', 'bar', 'scatter', 'histogram', 'box', 'violin')
            x_col: Column name for x-axis
            y_col: Column name for y-axis (optional for histogram)
            title: Plot title
            hue: Column name for color grouping (optional)
            figsize: List of [width, height] for the figure size
            style: matplotlib style to use (e.g. 'seaborn-v0_8-darkgrid', 'seaborn-v0_8-whitegrid')
            palette: Color palette to use
            output_path: Path where to save the plot
            
        Returns:
            str: Path to the saved plot image or error message
        """
        try:
            logger.info(f"Creating {plot_type} plot with x={x_col}, y={y_col}, hue={hue}")
            
            # Set style with error handling
            try:
                plt.style.use(style)
            except Exception as style_error:
                logger.warning(f"Failed to set style {style}, falling back to default style: {style_error}")
                plt.style.use('default')
            
            # Parse data
            df = self._parse_tabular_data(data)
            
            # If model_name column exists, clean up the names
            if 'model_name' in df.columns:
                df['model_name'] = df['model_name'].apply(lambda x: x.split('/')[-1])  # Take only the part after the last '/'
            
            # Create figure
            plt.figure(figsize=tuple(figsize))
            
            # Create plot based on type
            if plot_type == 'line':
                sns.lineplot(data=df, x=x_col, y=y_col, hue=hue, marker='o')
                if hue:  # Move legend outside for better readability
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                
            elif plot_type == 'bar':
                if hue:
                    df_grouped = df.groupby([x_col, hue])[y_col].mean().unstack()
                    df_grouped.plot(kind='bar', ax=plt.gca())
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                else:
                    sns.barplot(data=df, x=x_col, y=y_col)
                
            elif plot_type == 'scatter':
                sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue)
                if hue:
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                
            elif plot_type == 'histogram':
                sns.histplot(data=df, x=x_col, hue=hue, bins=30)
                if hue:
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                
            elif plot_type == 'box':
                sns.boxplot(data=df, x=x_col, y=y_col, hue=hue)
                if hue:
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                
            elif plot_type == 'violin':
                sns.violinplot(data=df, x=x_col, y=y_col, hue=hue)
                if hue:
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
            
            else:
                raise ValueError(f"Unsupported plot type: {plot_type}")
            
            # Format y-axis for cost values (if dealing with small numbers)
            if y_col and 'cost' in y_col.lower():
                plt.gca().yaxis.set_major_formatter(plt.ScalarFormatter(useMathText=True))
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
            
            # Rotate x-axis labels if they're dates or long text
            if x_col.lower() in ['date', 'created_at'] or (isinstance(df[x_col].iloc[0], str) and df[x_col].str.len().max() > 10):
                plt.xticks(rotation=45, ha='right')
            
            # Set title and labels
            plt.title(title or f'{plot_type.capitalize()} Plot of {y_col or x_col}', pad=20)
            plt.xlabel(x_col)
            if y_col:
                plt.ylabel(y_col)
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save plot with high DPI
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Successfully created plot at {output_path}")
            return f"Plot saved successfully at {output_path}"
            
        except Exception as e:
            logger.warning(f"Failed to create plot: {e}")
            return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Create a sample agent with plot tools
    agent = Agent(tools=[PlotTools()], show_tool_calls=True, markdown=True)
    
    # Example data
    sample_data = """
    created_at | cost | model_name
    2023-01-01 | 0.1 | gpt-4
    2023-01-02 | 0.2 | gpt-3.5
    2023-01-03 | 0.15 | gpt-4
    2023-01-04 | 0.25 | gpt-3.5
    """
    
    # Create a test plot
    plot_tools = PlotTools()
    plot_tools.create_plot(
        data=sample_data.strip(),
        plot_type="line",
        x_col="created_at",
        y_col="cost",
        title="Cost Over Time by Model",
        hue="model_name"
    ) 