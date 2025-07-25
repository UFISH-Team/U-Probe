# U-Probe
Universal oligo probe design software

## Installation and Usage

Clone:
```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd uprobe
```

Using conda install env:

```
conda env create -f environments.yaml
conda activate uprobe

```

Using pip:
```
pip install -r requirements.txt
```
If using pip, user need to install Bowtie2, Blast and MMseqs2.

## Development

Install requirements:

```
$ pip install -e ".[dev]"
```

## Test

Running workflow command:

```
python -m uprobe \
    --genomes_yaml tests/data/genomes.yaml \
    --protocol_yaml tests/data/RNA_format.yaml \
    --output_csv output_results.csv \
    --workdir work_path 
    --raw_csv True

```
