# U-Probe
Universal oligo probe design software

## Installation and Usage

```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd uprobe
```

using pip:
```
pip install -r requirements.txt
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
