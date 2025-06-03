from typing import Any, Dict, List, Union

import matplotlib

matplotlib.use("Agg")  # Set non-GUI backend before importing pyplot - important for background tasks

# import logger
import logging
import os
import uuid
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from langchain_core.tools import tool
from matplotlib.ticker import FuncFormatter
from traceloop.sdk.decorators import task

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)


def parse_tabular_data(data: str) -> pd.DataFrame:
    """Convert tabular string data to pandas DataFrame."""
    try:
        # Check if data is empty
        if not data or data.strip() == "":
            logger.warning("Empty data provided for parsing")
            return pd.DataFrame()

        # Split the data into lines and get headers
        lines = data.strip().split("\n")

        # Debug the raw data
        logger.info(f"Parsing tabular data with {len(lines)} lines")
        if len(lines) > 0:
            logger.info(f"First line: {lines[0]}")

        # Extract headers - handle both space-separated and pipe-separated formats
        if "|" in lines[0]:
            headers = [col.strip() for col in lines[0].split("|") if col.strip()]
        else:
            headers = [col.strip() for col in lines[0].split() if col.strip()]

        logger.info(f"Extracted headers: {headers}")

        # Parse the data rows
        rows = []
        for line in lines[1:]:
            if line.strip() and not line.startswith("-"):  # Skip empty lines and separator lines
                if "|" in line:
                    row = [val.strip() for val in line.split("|") if val.strip()]
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
            if "cost" in col.lower():
                df[col] = pd.to_numeric(df[col], errors="coerce")
                # Ensure positive values for cost
                df[col] = df[col].abs()
            # Try to convert other columns to numeric
            else:
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    # Try to convert to datetime if 'time' or 'date' in column name
                    if "time" in col.lower() or "date" in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception:
                            pass

        logger.info(f"Successfully parsed data into DataFrame with shape {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.warning(f"Failed to parse tabular data: {e}")
        raise ValueError(f"Failed to parse tabular data: {e}")


@tool
@task(name="create_plot")
def create_plot(
    data: str,
    plot_type: str,
    x_col: str,
    y_col: Union[str, None] = None,
    title: Union[str, None] = None,
    hue: Union[str, None] = None,
    figsize: Union[List[float], None] = [12, 8],  # Increased default figure size
    style: Union[str, None] = "seaborn-v0_8-darkgrid",
    palette: Union[str, None] = "husl",
    output_path: Union[str, None] = None,
) -> Dict[str, Any]:
    """Create a plot based on the data and parameters."""
    try:
        # Generate a unique filename if output_path is not provided
        if output_path is None:
            filename = f"plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.png"
            output_path = os.path.join(PLOTS_DIR, filename)
        elif not os.path.isabs(output_path):
            output_path = os.path.join(PLOTS_DIR, output_path)

        logger.info(f"Creating plot, will save to: {output_path}")

        logger.info(f"Creating {plot_type} plot with x={x_col}, y={y_col}, hue={hue}")

        # Set style with error handling
        try:
            plt.style.use(style)
        except Exception as style_error:
            logger.warning(f"Failed to set style {style}, falling back to default style: {style_error}")
            plt.style.use("default")

        # Parse data
        df = parse_tabular_data(data)
        print(f"DataFrame: {df}")

        # Create figure
        plt.figure(figsize=tuple(figsize))

        # Create plot based on type
        if plot_type == "line" or plot_type == "time series":  # Added time series as an alias for line
            sns.lineplot(data=df, x=x_col, y=y_col, hue=hue, marker="o")
            if hue:  # Move legend outside for better readability
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        elif plot_type == "bar":
            if hue:
                df_grouped = df.groupby([x_col, hue])[y_col].mean().unstack()
                df_grouped.plot(kind="bar", ax=plt.gca())
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)
            else:
                sns.barplot(data=df, x=x_col, y=y_col)

        elif plot_type == "scatter":
            sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue)
            if hue:
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        elif plot_type == "histogram":
            sns.histplot(data=df, x=x_col, hue=hue, bins=30)
            if hue:
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        elif plot_type == "box":
            sns.boxplot(data=df, x=x_col, y=y_col, hue=hue)
            if hue:
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        elif plot_type == "violin":
            sns.violinplot(data=df, x=x_col, y=y_col, hue=hue)
            if hue:
                plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        else:
            raise ValueError(f"Unsupported plot type: {plot_type}")

        # Format y-axis for cost values (if dealing with small numbers)
        if y_col and "cost" in y_col.lower():
            # Set y-axis to start at 0
            plt.ylim(bottom=0)

            # Get and print y-axis values
            y_values = plt.gca().get_yticks()
            print("Y-axis values before formatting:", y_values)

            def cost_formatter(x, p):
                # Only format if value is non-negative
                if x < 0:
                    return ""
                return f"{x:.4f}"

            plt.gca().yaxis.set_major_formatter(FuncFormatter(cost_formatter))

        # Rotate x-axis labels if they're dates or long text
        if x_col.lower() in ["date", "created_at"] or (
            isinstance(df[x_col].iloc[0], str) and df[x_col].str.len().max() > 10
        ):
            plt.xticks(rotation=45, ha="right")

        # Set title and labels
        plt.title(title or f"{plot_type.capitalize()} Plot of {y_col or x_col}", pad=20)
        plt.xlabel(x_col)
        if y_col:
            plt.ylabel(y_col)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save plot with high DPI
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"Successfully created plot at {output_path}")
        return output_path

    except Exception as e:
        logger.warning(f"Failed to create plot: {e}")
        raise ValueError(f"Failed to create plot: {e}")


# Example usage
if __name__ == "__main__":
    # Example data
    sample_data = """
    created_at | cost | model_name
    2023-01-01 | 0.1 | gpt-4
    2023-01-02 | 0.2 | gpt-3.5
    2023-01-03 | 0.15 | gpt-4
    2023-01-04 | 0.25 | gpt-3.5
    """

    df = parse_tabular_data(sample_data)
    print(df)

    create_plot(
        sample_data,
        plot_type="line",
        x_col="created_at",
        y_col="cost",
        title="Cost Over Time by Model",
        hue="model_name",
    )
