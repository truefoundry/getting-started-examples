from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_plot_agent.tools.clickhouse_tool import ClickHouseTool
from crewai_plot_agent.tools.plot_tool import PlotTools
from pydantic import BaseModel, Field
import os
import litellm

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators



from traceloop.sdk import Traceloop

# Traceloop Configuration
TRACELOOP_APP_NAME = os.environ.get("TRACELOOP_APP_NAME")
TRACELOOP_TRACING_PROJECT_FQN = os.environ.get("TRACELOOP_TRACING_PROJECT_FQN")

# Get API Key for both LLM Gateway and Traceloop
# TFY_API_KEY can be used for both, or use separate keys
TFY_API_KEY = os.environ.get("TFY_API_KEY") or os.environ.get("LLM_GATEWAY_API_KEY")
LLM_GATEWAY_BASE_URL = os.environ.get("LLM_GATEWAY_BASE_URL", "https://gateway.truefoundry.ai")
MODEL_NAME =os.environ.get("MODEL_NAME")


# Validate that required environment variables are set
if not TFY_API_KEY:
    raise ValueError(
        "LLM_GATEWAY_API_KEY must be set. "
        "Please set LLM_GATEWAY_API_KEY environment variable."
    )

# Configure LiteLLM default headers
# litellm.drop_params = True  # Drop unsupported params
# litellm.suppress_debug_info = False

extra_headers = {
    "Authorization": f"Bearer {TFY_API_KEY}",
    "TFY-Tracing-Project": TRACELOOP_TRACING_PROJECT_FQN,
}

# Set default headers for all LiteLLM requests
if not hasattr(litellm, 'default_headers') or litellm.default_headers is None:
    litellm.default_headers = {}
litellm.default_headers.update(extra_headers)

# Initialize Traceloop SDK for tracing
# Generate a Personal Access Token or Virtual Account from the Access Tab
# If you are using Virtual Account, make sure to give it access to the tracing project
print("\n" + "="*80)
print("INITIALIZING TRACELOOP SDK FOR TRACING")
print("="*80)
if TFY_API_KEY:
    Traceloop.init(
        app_name=TRACELOOP_APP_NAME,
        api_endpoint="https://tfy-eo.truefoundry.cloud/api/otel",
        headers={
            "Authorization": f"Bearer {TFY_API_KEY}",
            "TFY-Tracing-Project": TRACELOOP_TRACING_PROJECT_FQN,
        },
    )
    print("✅ Traceloop SDK initialized successfully in crew.py")
    # print("="*80 + "\n")
else:
    print("⚠️  ERROR: Traceloop SDK not initialized - TFY_API_KEY or LLM_GATEWAY_API_KEY not set")
    print("Please set TFY_API_KEY or LLM_GATEWAY_API_KEY environment variable")
    print("="*80 + "\n")


class SQLQueryResult(BaseModel):
    query: str = Field(..., description="The SQL query that was executed.")
    column_names: List[str] = Field(..., description="List of column names in the query result.")
    rows: List[List[str]] = Field(..., description="List of row values, where each row is a list of column values.")
    error: Optional[str] = Field(None, description="Error message if the query failed.")


class PlotResult(BaseModel):
    plot_type: str = Field(
        ...,
        description="The type of plot generated (e.g., bar, line, scatter, time series, histogram, box, violin).",
    )
    title: str = Field(..., description="The title of the plot.")
    data_summary: Dict[str, Any] = Field(..., description="Summary of the data used for plotting.")
    insights: List[str] = Field(..., description="List of insights derived from the plot.")
    plot_file_path: Optional[str] = Field(None, description="Path to the saved plot file if available.")
    error: Optional[str] = Field(None, description="Error message if the plot generation failed.")
    time_range: Optional[Dict[str, str]] = Field(
        None,
        description="Start and end dates for time series plots, format: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}",
    )


@CrewBase
class CrewaiPlotAgent:
    """CrewaiPlotAgent crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # def process_output(self, output):
    # 	# Modify output after the crew finishes
    # 	output.raw += "\nProcessed after kickoff."
    # 	print("Output", output ,"sdfsdfsdfsd")
    # 	return output

    # Configure LLM for agents with TrueFoundry Gateway settings
    def _get_llm(self) -> LLM:
        """Get configured LLM for agents with TrueFoundry Gateway"""
        # Use the actual model name directly: chatwithtraces/gpt5
        return LLM(
            model=MODEL_NAME,  # Use actual model: chatwithtraces/gpt5
            api_key=TFY_API_KEY,
            base_url=LLM_GATEWAY_BASE_URL,
            custom_llm_provider="openai",  # <— LiteLLM uses this
            extra_headers={
            "Authorization": f"Bearer {TFY_API_KEY}",
            "TFY-Tracing-Project": TRACELOOP_TRACING_PROJECT_FQN,
            },
            temperature=0.1,  
            # Using chatwithtraces/gpt5 directly without wrapper
            # Headers are set via litellm.default_headers
        )

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    @agent
    def sql_writer(self) -> Agent:
        return Agent(config=self.agents_config["sql_writer"], 
        verbose=True, 
        llm=self._get_llm(),
        tools=[ClickHouseTool()])

    @agent
    def plot_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["plot_writer"],
            verbose=True,
            llm=self._get_llm(),
            tools=[PlotTools()],
            pydantic_output=PlotResult,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def sql_task(self) -> Task:
        return Task(
            config=self.tasks_config["sql_task"],
        )

    @task
    def plot_task(self) -> Task:
        return Task(
            config=self.tasks_config["plot_task"],
            # callback=self.process_output,
            allow_code_execution=True,
            output_pydantic=PlotResult,
            # output_file='plot.png'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewaiPlotAgent crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # output_pydantic=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

    