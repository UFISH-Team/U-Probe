# U-Probe
Universal oligo probe design software

## Installation and Usage

### 1. Clone the Repository
First, clone the repository to your local machine:
```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd uprobe
```

### 2.  Install Dependencies
Install the required dependencies using pip:
```
pip install -r requirements.txt
```

### 3. Install the Project in Editable Mode
To make the uprobe package available for absolute imports, install the project in editable mode:
```
pip install -e .
```

## Development

Install requirements:

```
$ pip install -e ".[dev]"
```

Run tests:

```
$ pytest -s tests/
```

## Test

Run workflow

```
python ./uprobe/workflow.py ./tests/data/double_hyb_rca.yaml ./tests/data/genomes.yaml ./out_probes.csv
```
