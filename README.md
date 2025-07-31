<h1 align="center">🧬 U-Probe: Universal Probe Design Tool</h1>

<div align="center">
  <img src="./assets/3.png" alt="uprobe logo", width="710px", height="210px">
</div>
<br>

- U-Probe is a powerful and flexible Python-based tool for designing custom DNA or RNA probes for various molecular biology applications, such as *in situ* hybridization and targeted sequencing. 
- It provides a comprehensive workflow from target gene selection to final probe generation, with a focus on automation, customization, and ease of use.

## Features

- **End-to-end workflow**: Automates the entire probe design process, from sequence extraction to final filtering.
- **Highly customizable**: Use simple YAML configuration files to define target genes, probe structures, and filtering criteria.
- **Advanced filtering**: Filter probes based on a wide range of attributes like GC content, melting temperature (Tm), and off-target potential.
- **Extensible API**: In addition to a command-line interface, U-Probe offers a clean Python API for programmatic access and integration into other bioinformatics pipelines.
- **Built-in indexing**: Automatically handles the creation of genome indices for alignment tools like Bowtie2 and BLAST.

## Installation

To get started with U-Probe, clone the repository and install the required dependencies.

Using pip:

```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd u-probe
pip install -r requirements.txt
```

Using conda:
```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd u-probe
conda env create -f environments.yaml
conda activate uprobe
conda deactivate
```

*(Note: A `requirements.txt` file should be created.)*

## Use guide

U-Probe provides two ways to use: Command Line Interface (CLI) and Python API.

### Configuration Files

Before using U-Probe, you need to prepare two YAML configuration files:

1. **genomes.yaml** - Define genome information:
   ```yaml
   human_hg38:
     fasta: "/path/to/hg38.fa"
     gtf: "/path/to/gencode.v38.annotation.gtf"
     align_index: ["bowtie2", "blast"]
   ```

2. **protocol.yaml** - 定义探针设计参数：
   ```yaml
   name: "MyExperiment"
   genome: "human_hg38"
   targets:
     - "GENE1"
     - "GENE2"
   extracts:
     target_region:
       source: "exon"
       overlap: 10
       length: 120
   # For more parameter configurations, please refer to tests/data/*.yaml
   ```

### Command Line Interface (CLI)

#### Complete Workflow

One-click execution of the complete process from genome index construction to probe design:

```bash
python -m uprobe.cli run \
  --protocol protocol.yaml \
  --genomes genomes.yaml \
  --output ./results \
  --raw \
  --threads 10
```

#### Individual Step Execution

**1. Build Genome Index**
```bash
python -m uprobe.cli build-index \
  --protocol protocol.yaml \
  --genomes genomes.yaml \
  --threads 10
```

**2. Validate Target Genes**
```bash
python -m uprobe.cli validate-targets \
  --protocol protocol.yaml \
  --genomes genomes.yaml \
  --continue-invalid
```

**3. Generate Barcode Sequences**
```bash
python -m uprobe.cli generate-barcodes \
  --protocol protocol.yaml \
  --output ./barcodes
```

#### Common Parameters

| Parameter | Description |
|------|------|
| `--protocol` | Path to probe design protocol configuration file |
| `--genomes` | Path to genome configuration file |
| `--output` | Output directory |
| `--raw` | Save unfiltered raw probe data |
| `--continue-invalid` | Continue execution even if some targets are invalid |
| `--threads` | Number of threads for index building and computation |

#### Get Help

```bash
# View all commands
python -m uprobe.cli --help

# View help for specific command
python -m uprobe.cli run --help
```

### Python API

U-Probe provides an object-oriented API for easy integration into other Python projects.

#### Basic Usage

```python
from pathlib import Path
from uprobe.api import UProbeAPI

# 初始化API
api = UProbeAPI(
    protocol_config=Path("protocol.yaml"),
    genomes_config=Path("genomes.yaml"),
    output_dir=Path("./results")
)

# 执行完整工作流
probes_df = api.run_workflow(
    raw_csv=True,
    continue_on_invalid_targets=False,
    threads=10
)
```

#### Step-by-Step Execution

```python
# Initialize API
api = UProbeAPI(
    protocol_config=Path("protocol.yaml"),
    genomes_config=Path("genomes.yaml"),
    output_dir=Path("./results")
)

# 1. Build genome index
api.build_genome_index(threads=10)

# 2. Validate target genes
if not api.validate_targets(continue_on_invalid=False):
    print("Target validation failed")
    exit(1)

# 3. Generate target sequences
df_targets = api.generate_target_seqs()
if df_targets.empty:
    print("No target sequences generated")
    exit(1)

# 4. Construct probes
df_probes = api.construct_probes(df_targets)
if df_probes.empty:
    print("No probes constructed")
    exit(1)

# 5. Merge target and probe data
import pandas as pd
df_combined = pd.concat([df_targets.reset_index(drop=True), 
                        df_probes.reset_index(drop=True)], axis=1)

# 6. Post-process probes
df_final = api.post_process_probes(df_combined, raw_csv=True)
print(f"Generated {len(df_final)} probes")

# 7. Generate barcode sequences (optional)
barcode_sets = api.generate_barcodes()
```

#### Main Methods

| Method | Description |
|------|------|
| `build_genome_index(threads=10)` | Build genome index |
| `validate_targets(continue_on_invalid=False)` | Validate target genes |
| `generate_target_seqs()` | Generate target region sequences |
| `construct_probes(df_targets)` | Construct probes |
| `post_process_probes(df_probes, raw_csv=False)` | Add attributes and filter probes |
| `generate_barcodes()` | Generate DNA barcode sequences |
| `run_workflow(...)` | Execute complete probe design workflow |

## Configuration Details

### `genomes.yaml`
This file maps a genome name to its corresponding file paths.

- `fasta`: Path to the genome FASTA file.
- `gtf`: Path to the gene annotation GTF file.
- `align_index`: A list of aligners (e.g., `bowtie2`, `blast`) for which to build indices.

### `protocol.yaml`
This file defines all parameters for a specific probe design run.

- `name`: A unique name for your experiment.
- `genome`: The name of the genome to use (must match a key in `genomes.yaml`).
- `targets`: A list of target gene names or IDs.
- `extracts`: Parameters for extracting target sequences (e.g., source, overlap, length).
- `probes`: The core of the design, defining probe templates, parts, and expressions.
- `encoding`: Mapping of genes to barcodes or other identifiers.
- `filters`: Criteria for post-processing and filtering probes (e.g., GC content, Tm).

For more detailed examples and advanced configurations, please refer to the [`tests/data/*.yaml`](https://github.com/UFISH-Team/U-Probe/tree/main/tests/data "Click to visit here") directory.
