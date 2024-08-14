from truefoundry.deploy import Workflow, LocalSource


workflow = Workflow(
    name="testing-pipeline",
    workflow_file_path="sum_of_squares.py",
    source=LocalSource(project_root_path="./", local_build=False)

)
workflow.deploy(workspace_fqn="<workspace-fqn>")