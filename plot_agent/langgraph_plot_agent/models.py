from typing import List, Union

from pydantic import BaseModel, Field


class SQLQueryResult(BaseModel):
    query: str = Field(..., description="The SQL query that was executed.")
    column_names: List[str] = Field(..., description="List of column names in the query result.")
    rows: List[List[str]] = Field(..., description="List of row values, where each row is a list of column values.")
    error: Union[str, None] = Field(default=None, description="Error message if the query failed.")


class PlotResult(BaseModel):
    plot_type: str = Field(..., description="Type of plot created.")
    plot_path: str = Field(..., description="Path to the saved plot image.")
    x_col: str = Field(..., description="Column used for x-axis.")
    y_col: Union[str, None] = Field(default=None, description="Column used for y-axis.")
    title: Union[str, None] = Field(default=None, description="Title of the plot.")
    error: Union[str, None] = Field(default=None, description="Error message if plotting failed.")


class VisualizationRequest(BaseModel):
    plot_type: str = Field(..., description="Type of plot to create.")
    x_col: str = Field(..., description="Column for x-axis.")
    y_col: Union[str, None] = Field(default=None, description="Column for y-axis.")
    title: Union[str, None] = Field(default=None, description="Plot title.")
    hue: Union[str, None] = Field(default=None, description="Column for color grouping.")
