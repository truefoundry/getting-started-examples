import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional, Type

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from crewai.tools import BaseTool
from matplotlib.ticker import FuncFormatter
from pydantic import BaseModel, Field

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)


class PlotQueryInput(BaseModel):
    """Input schema for executing a plotting operation."""

    data: str = Field(..., description="Tabular string data to be plotted.")
    plot_type: str = Field(..., description="Type of plot (line, bar, scatter, etc.).")
    x_col: str = Field(..., description="Column to use for the X-axis.")
    y_col: Optional[str] = Field(None, description="Column to use for the Y-axis.")
    title: Optional[str] = Field(None, description="Title of the plot.")
    hue: Optional[str] = Field(None, description="Column to use for grouping data.")
    figsize: Optional[List[float]] = Field(default=[12, 8], description="Figure size.")
    style: Optional[str] = Field(default="seaborn-v0_8-darkgrid", description="Matplotlib style.")
    palette: Optional[str] = Field(default="husl", description="Color palette.")
    output_path: Optional[str] = Field(None, description="Path to save the plot.")


class PlotTools(BaseTool):
    name: str = "Plot Generator"
    description: str = "Generates plots from tabular data."
    args_schema: Type[BaseModel] = PlotQueryInput

    def _parse_tabular_data(self, data: str) -> pd.DataFrame:
        """Convert tabular string data to pandas DataFrame."""
        try:
            if not data.strip():
                logger.warning("Empty data provided for parsing")
                return pd.DataFrame()

            lines = data.strip().split("\n")
            logger.info(f"Parsing tabular data with {len(lines)} lines")

            headers = [col.strip() for col in lines[0].split("|") if col.strip()]
            logger.info(f"Extracted headers: {headers}")

            rows = []
            for line in lines[1:]:
                if line.strip() and not line.startswith("-"):
                    row = [val.strip() for val in line.split("|") if val.strip()]
                    if len(row) == len(headers):
                        rows.append(row)
                    else:
                        logger.warning(f"Skipping row with mismatched columns: {line}")

            df = pd.DataFrame(rows, columns=headers)
            for col in df.columns:
                if "cost" in col.lower():
                    df[col] = pd.to_numeric(df[col], errors="coerce").abs()
                else:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except Exception:
                        if "time" in col.lower() or "date" in col.lower():
                            try:
                                df[col] = pd.to_datetime(df[col])
                            except Exception:
                                pass

            logger.info(f"Parsed DataFrame shape: {df.shape}")
            return df
        except Exception as e:
            logger.warning(f"Failed to parse tabular data: {e}")
            raise ValueError(f"Failed to parse tabular data: {e}")

    def _run(
        self,
        data: str,
        plot_type: str,
        x_col: str,
        y_col: Optional[str] = None,
        title: Optional[str] = None,
        hue: Optional[str] = None,
        figsize: Optional[List[float]] = [12, 8],
        style: Optional[str] = "seaborn-v0_8-darkgrid",
        palette: Optional[str] = "husl",
        output_path: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """Executes a plotting function and returns the saved file path."""
        try:
            if output_path is None:
                # Fallback to datetime-based filename
                filename = f"plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(PLOTS_DIR, filename)
            elif not os.path.isabs(output_path):
                output_path = os.path.join(PLOTS_DIR, output_path)

            logger.info(f"Creating {plot_type} plot, saving to: {output_path}")

            try:
                plt.style.use(style)
            except Exception as style_error:
                logger.warning(f"Failed to set style {style}, falling back to default: {style_error}")
                plt.style.use("default")

            df = self._parse_tabular_data(data)

            plt.figure(figsize=tuple(figsize))

            if plot_type in ["line", "time series"]:
                sns.lineplot(data=df, x=x_col, y=y_col, hue=hue, marker="o")
                if hue:
                    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

            elif plot_type == "bar":
                sns.barplot(data=df, x=x_col, y=y_col, hue=hue)

            elif plot_type == "scatter":
                sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue)

            elif plot_type == "histogram":
                sns.histplot(data=df, x=x_col, hue=hue, bins=30)

            elif plot_type == "box":
                sns.boxplot(data=df, x=x_col, y=y_col, hue=hue)

            elif plot_type == "violin":
                sns.violinplot(data=df, x=x_col, y=y_col, hue=hue)

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

            print(f"Successfully created plot at {output_path}", "SDFDSFSDD")
            return output_path

        except Exception as e:
            logger.warning(f"Failed to create plot: {e}")
            raise ValueError(f"Failed to create plot: {e}")
