# Model Clone Job

This script clones a model from one TrueFoundry repository and logs it to another TrueFoundry repository. It downloads the source model, preserves its metadata and framework information, and uploads it to the target repository.

## Installation

1. Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure you have TrueFoundry credentials configured (via `tfy login` or environment variables).

## Usage

### Basic Usage

```bash
# Make sure to activate your virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

python clone_model.py --source-model-fqn "model:truefoundry/source-repo/my-model:1" --target-ml-repo "target-repo"
```

## Arguments

- `--source-model-fqn` (required): TrueFoundry source model FQN (Fully Qualified Name) in the format `model:workspace/source-repo/model-name:version`
- `--target-ml-repo` (required): TrueFoundry target ML repository name where the model will be cloned

## Examples

### Clone a model from one repository to another:

```bash
python clone_model.py --source-model-fqn "model:truefoundry/production-models/bert-classifier:2" --target-ml-repo "staging-models"
```

### Clone a model with a specific version:

```bash
python clone_model.py --source-model-fqn "model:truefoundry/ml-team/image-classifier:v1.0" --target-ml-repo "backup-models"
```

### Clone a model across different workspaces:

```bash
python clone_model.py --source-model-fqn "model:truefoundry/dev-workspace/experimental-model:latest" --target-ml-repo "prod-workspace-models"
```
