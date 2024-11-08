### Sample Workflow for California Housing Dataset

This is a sample workflow for the California Housing Dataset.

### Steps to run the workflow locally

1. Install the TrueFoundry Python SDK
```
pip install truefoundry[workflow]==0.4.7
``` 

Login to TrueFoundry
```
tfy login --host <Enter your Truefoundry UI's host, e.g. https://company-name.truefoundry.com>
```

2. Run the workflow locally (testing if things are working)
```
python demo_wf_py.py
```

3. Deploy the workflow
```
tfy deploy workflow \
    --name california-housing-ml-pipeline\
    --file demo_wf_py.py\
    --workspace_fqn "put your workspacefqn here"
```
