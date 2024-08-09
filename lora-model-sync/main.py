import os
import json
from truefoundry.ml import get_client


SOURCES = json.loads(os.getenv("SOURCES") or "{}")
PATH = "/adapters"
client = get_client()
for source in SOURCES:
    ml_repo = source["name"]
    fqns = source.get("artifact_fqn_patterns") or []
    for fqn in fqns:
        for av in client.list_artifact_versions_by_fqn(fqn):
            dirname = av.fqn.replace(":", "-").replace("/", "-")
            path = os.path.join(PATH, dirname)
            if os.path.exists(path):
                print(f"Skipping {path} as it already exists")
                continue
            os.makedirs(path, exist_ok=True)
            print(f"Downloading {av.fqn} to {path}")
            av.download(path, overwrite=True)
