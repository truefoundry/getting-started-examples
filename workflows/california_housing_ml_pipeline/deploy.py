from truefoundry.deploy import Workflow, LocalSource


workflow = Workflow(
    name="testing-pipeline",  # your workflow application name
    workflow_file_path="demo_wf_py.py",
    source=LocalSource(local_build=False)
)
workflow.deploy(workspace_fqn="<put your workpace fqn here>")
