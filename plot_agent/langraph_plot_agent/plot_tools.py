from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from langchain_core.tools import tool
import logging
import os
import uuid
from matplotlib.ticker import FuncFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

class PlotTools:
    def __init__(self):
        pass
        
    def _parse_tabular_data(self, data: str) -> pd.DataFrame:
        """Convert tabular string data to pandas DataFrame."""
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
                        row_values = [val.strip() for val in line.split('|') if val.strip()]
                    else:
                        row_values = [val.strip() for val in line.split() if val.strip()]
                    
                    # Ensure row has same number of columns as headers
                    if len(row_values) == len(headers):
                        rows.append(row_values)
                    else:
                        logger.warning(f"Skipping row with mismatched columns: {line}")
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Convert numeric columns
            for col in df.columns:
                # Try to convert to numeric, coerce errors to NaN
                df[col] = pd.to_numeric(df[col], errors='ignore')
                
                # Try to convert to datetime if 'date' or 'time' in column name
                if any(time_word in col.lower() for time_word in ['date', 'time', 'created']):
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                    except:
                        pass
            
            logger.info(f"Created DataFrame with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing tabular data: {e}")
            return pd.DataFrame()
    
    @tool("create_plot", return_direct=False)
    def create_plot_tool(
        self,
        data: str,
        plot_type: str,
        x_col: str,
        y_col: Optional[str] = None,
        title: Optional[str] = None,
        hue: Optional[str] = None,
        figsize: Optional[List[float]] = None,
        style: Optional[str] = None,
        palette: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Creates a visualization from tabular data.
        
        Args:
            data: Tabular data with columns separated by ' | ' and rows by newlines
            plot_type: Type of plot to create (bar, line, scatter, histogram, box, etc.)
            x_col: Column to use for x-axis
            y_col: Column to use for y-axis (optional for some plot types)
            title: Title for the plot
            hue: Column to use for color grouping
            figsize: Figure size as [width, height] in inches
            style: Matplotlib style to use
            palette: Color palette for the plot
            output_path: Path to save the plot image (optional)
            
        Returns:
            str: Path to the saved plot image
        """
        plot_path = self.create_plot(
            data=data,
            plot_type=plot_type,
            x_col=x_col,
            y_col=y_col,
            title=title,
            hue=hue,
            figsize=figsize or [12, 8],
            style=style or "seaborn-v0_8-darkgrid",
            palette=palette or "husl",
            output_path=output_path
        )
        
        return f"Plot created and saved to {plot_path}"
    
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
        output_path: Optional[str] = None
    ) -> str:
        """
        Creates a visualization from tabular data.
        
        Args:
            data: Tabular data with columns separated by ' | ' and rows by newlines
            plot_type: Type of plot to create (bar, line, scatter, histogram, box, etc.)
            x_col: Column to use for x-axis
            y_col: Column to use for y-axis (optional for some plot types)
            title: Title for the plot
            hue: Column to use for color grouping
            figsize: Figure size as [width, height] in inches
            style: Matplotlib style to use
            palette: Color palette for the plot
            output_path: Path to save the plot image (optional)
            
        Returns:
            str: Path to the saved plot image
        """
        try:
            # Parse the data
            df = self._parse_tabular_data(data)
            if df.empty:
                raise ValueError("Failed to parse data or empty dataset")
            
            # Validate columns
            if x_col not in df.columns:
                raise ValueError(f"x_col '{x_col}' not found in data columns: {df.columns.tolist()}")
            
            if y_col and y_col not in df.columns:
                raise ValueError(f"y_col '{y_col}' not found in data columns: {df.columns.tolist()}")
                
            if hue and hue not in df.columns:
                raise ValueError(f"hue '{hue}' not found in data columns: {df.columns.tolist()}")
            
            # Set the style
            plt.style.use(style)
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize)
            
            # Create the plot based on type
            plot_type = plot_type.lower()
            
            # Special handling for cost columns - format as currency
            is_cost_column = False
            if y_col and 'cost' in y_col.lower():
                is_cost_column = True
                
                def cost_formatter(x, p):
                    # Only format if value is non-negative
                    if x >= 0:
                        return f"${x:.4f}"
                    else:
                        return f"-${abs(x):.4f}"
                
                ax.yaxis.set_major_formatter(FuncFormatter(cost_formatter))
            
            # Create the appropriate plot
            if plot_type == 'bar':
                if y_col:
                    sns.barplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                else:
                    # Count plot if no y_col specified
                    sns.countplot(x=x_col, hue=hue, data=df, palette=palette, ax=ax)
                    
                # Rotate x labels if there are many categories
                if len(df[x_col].unique()) > 5:
                    plt.xticks(rotation=45, ha='right')
                
            elif plot_type == 'line':
                # For time series, sort by x if it's a datetime
                if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                    df = df.sort_values(by=x_col)
                
                sns.lineplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                
                # Rotate x labels for time series
                if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                    plt.xticks(rotation=45, ha='right')
                
            elif plot_type == 'scatter':
                sns.scatterplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                
            elif plot_type == 'histogram':
                if y_col:
                    # If both x and y are provided, create a 2D histogram
                    plt.hist2d(df[x_col], df[y_col], cmap='viridis')
                    plt.colorbar(label='Count')
                else:
                    # Simple histogram
                    sns.histplot(df[x_col], kde=True, ax=ax)
                
            elif plot_type == 'box':
                if y_col:
                    sns.boxplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                else:
                    sns.boxplot(x=x_col, hue=hue, data=df, palette=palette, ax=ax)
                
            elif plot_type == 'violin':
                if y_col:
                    sns.violinplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                else:
                    sns.violinplot(x=x_col, hue=hue, data=df, palette=palette, ax=ax)
                
            elif plot_type == 'heatmap':
                # For heatmap, pivot the data if needed
                if y_col and hue:
                    pivot_df = df.pivot_table(index=y_col, columns=x_col, values=hue, aggfunc='mean')
                    sns.heatmap(pivot_df, annot=True, cmap='viridis', ax=ax)
                else:
                    # Correlation heatmap if no specific columns for heatmap
                    numeric_df = df.select_dtypes(include=['number'])
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='viridis', ax=ax)
                
            else:
                # Default to bar chart for unknown types
                logger.warning(f"Unknown plot type '{plot_type}', defaulting to bar chart")
                if y_col:
                    sns.barplot(x=x_col, y=y_col, hue=hue, data=df, palette=palette, ax=ax)
                else:
                    sns.countplot(x=x_col, hue=hue, data=df, palette=palette, ax=ax)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14, pad=20)
            else:
                if y_col:
                    ax.set_title(f"{y_col} by {x_col}", fontsize=14, pad=20)
                else:
                    ax.set_title(f"Distribution of {x_col}", fontsize=14, pad=20)
            
            ax.set_xlabel(x_col, fontsize=12, labelpad=10)
            
            if y_col:
                if is_cost_column:
                    ax.set_ylabel(f"{y_col} (USD)", fontsize=12, labelpad=10)
                else:
                    ax.set_ylabel(y_col, fontsize=12, labelpad=10)
            else:
                ax.set_ylabel("Count", fontsize=12, labelpad=10)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save the plot
            if not output_path:
                # Generate a unique filename
                filename = f"{plot_type}_{x_col}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(PLOTS_DIR, filename)
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Plot saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating plot: {e}")
            # Create a simple error plot
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, f"Error creating plot: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=plt.gca().transAxes, fontsize=14, color='red')
            
            # Save the error plot
            error_filename = f"error_plot_{uuid.uuid4().hex[:8]}.png"
            error_path = os.path.join(PLOTS_DIR, error_filename)
            plt.savefig(error_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Error plot saved to {error_path}")
            return error_path

# Example usage
if __name__ == "__main__":
    # Create a sample plot tools instance
    plot_tools = PlotTools()
    
    # Example data
    sample_data = """
    created_at | cost | model_name
    2023-01-01 | 0.1 | gpt-4
    2023-01-02 | 0.2 | gpt-3.5
    2023-01-03 | 0.15 | gpt-4
    2023-01-04 | 0.25 | gpt-3.5
    """
    
    # Create a test plot
    plot_path = plot_tools.create_plot(
        data=sample_data.strip(),
        plot_type="line",
        x_col="created_at",
        y_col="cost",
        title="Cost Over Time by Model",
        hue="model_name"
    )
    print(f"Plot created at: {plot_path}") 