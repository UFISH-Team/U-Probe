# U-Probe
Universal oligo probe design software

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
python /uprobe/workflow.py /tests/data/double_hyb_rca.yaml tests/data/genomes.yaml out_probes.csv
```
