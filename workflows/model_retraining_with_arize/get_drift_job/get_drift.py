import os

import requests
from truefoundry.deploy import trigger_workflow

query = """
{node(id:"TW9uaXRvcjo0NjkzNTk6VHp3Kw=="){...on Monitor{calculationsWithinTimeRange(startTime:"2025-02-23T00:00:00.000Z",endTime:"2025-02-25T00:00:00.000Z",timeZone:"UTC"){computedValue,evaluatedAt,computedThreshold,calculationStatus}}}}
"""

response = requests.post(
    "https://app.arize.com/graphql",
    json={"query": query},
    headers={
        "x-api-key": os.environ["ARIZE_GRAPHQL_API_KEY"],
    },
)

calculations = response.json()["data"]["node"]["calculationsWithinTimeRange"]
for calculation in calculations:
    calculationStatus = calculation["calculationStatus"]
    if calculationStatus == "triggered":
        break

if calculationStatus == "triggered":
    print("Drift detected, triggering retraining workflow")
    trigger_workflow(
        application_fqn="tfy-aws:dev-ws:retraining-model-wf",
        inputs={"ml_repo": "bank-customer-churn", "workspace_fqn": "tfy-aws:dev-ws"},
    )
else:
    print("No drift detected")
