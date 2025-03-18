from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from src.crewai_plot_agent.tools.clickhouse_tool import ClickHouseTool
from src.crewai_plot_agent.tools.plot_tool import PlotTools
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
from traceloop.sdk import Traceloop

Traceloop.init(app_name="crewai")


class SQLQueryResult(BaseModel):
    query: str = Field(..., description="The SQL query that was executed.")
    column_names: List[str] = Field(..., description="List of column names in the query result.")
    rows: List[List[str]] = Field(..., description="List of row values, where each row is a list of column values.")
    error: Optional[str] = Field(None, description="Error message if the query failed.")

class PlotResult(BaseModel):
    plot_type: str = Field(..., description="The type of plot generated (e.g., bar, line, scatter, time series, histogram, box, violin).")
    title: str = Field(..., description="The title of the plot.")
    data_summary: Dict[str, Any] = Field(..., description="Summary of the data used for plotting.")
    insights: List[str] = Field(..., description="List of insights derived from the plot.")
    plot_file_path: Optional[str] = Field(None, description="Path to the saved plot file if available.")
    error: Optional[str] = Field(None, description="Error message if the plot generation failed.")
    time_range: Optional[Dict[str, str]] = Field(None, description="Start and end dates for time series plots, format: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}")


@CrewBase
class CrewaiPlotAgent():
	"""CrewaiPlotAgent crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# def process_output(self, output):
	# 	# Modify output after the crew finishes
	# 	output.raw += "\nProcessed after kickoff."
	# 	print("Output", output ,"sdfsdfsdfsd")
	# 	return output

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def sql_writer(self) -> Agent:
		return Agent(
			config=self.agents_config['sql_writer'],
			verbose=True,
			tools=[ClickHouseTool()]
		)

	@agent
	def plot_writer(self) -> Agent:
		return Agent(
			config=self.agents_config['plot_writer'],
			verbose=True,
			tools=[PlotTools()],
			pydantic_output=PlotResult,
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def sql_task(self) -> Task:
		return Task(
			config=self.tasks_config['sql_task'],
		)

	@task
	def plot_task(self) -> Task:
		return Task(
			config=self.tasks_config['plot_task'],
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
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# output_pydantic=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
	
