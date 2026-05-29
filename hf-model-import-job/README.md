# Hugging Face Model Import Job

This script downloads a Hugging Face model from a given URL and logs it to TrueFoundry's model registry.

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

python main.py --model-id "microsoft/DialoGPT-medium" --ml-repo "my-ml-repo" --model-name "dialogpt-medium" --model-type "text-generation"
```

## Arguments

- `--model-id` (required): Hugging Face model ID or repository ID
- `--ml-repo` (required): TrueFoundry ML repository name
- `--model-name` (required): Name for the model in TrueFoundry
- `--model-type` (required): Type of the model (e.g., 'text-generation', 'fill-mask')
- `--hf-token` (optional): Hugging Face token for private models

## Examples

### Import a popular language model:

```bash
python main.py --model-id "gpt2" --ml-repo "language-models" --model-name "gpt2-small" --model-type "text-generation"
```

### Import a BERT model:

```bash
python main.py --model-id "bert-base-uncased" --ml-repo "nlp-models" --model-name "bert-base" --model-type "fill-mask"
```
