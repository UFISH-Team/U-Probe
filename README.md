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

To get started with U-Probe, clone the repository and install the package.

### Install from source (Recommended)

```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd u-probe
pip install .
```

After installation, you can use U-Probe directly with the `uprobe` command.

### Development install

For development purposes, install in editable mode:

```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd u-probe
pip install -e .
```

### Using conda environment

```bash
git clone https://github.com/UFISH-Team/U-Probe.git
cd u-probe
conda env create -f environments.yaml
conda activate uprobe
pip install .
```

## Usage Guide

U-Probe provides two flexible ways to use the tool: **Command Line Interface (CLI)** and **Python API**. 

Before starting, ensure you have prepared two YAML configuration files:
1. **`genomes.yaml`**: Defines genome paths (FASTA, GTF, etc.).
2. **`protocol.yaml`**: Defines probe design parameters.

### 1. Command Line Interface (CLI)

The CLI is perfect for running tasks quickly in the terminal or shell scripts.

#### 🌟 Complete Workflow (Recommended)
To run the entire pipeline from genome index construction to final probe generation in one go:

```bash
uprobe run -p protocol.yaml -g genomes.yaml -o ./results --threads 10
```

#### 🔧 Step-by-Step Execution
For advanced users who need intermediate results or custom workflows, you can execute each step individually:

```bash
# 1. Build genome index
uprobe build-index -p protocol.yaml -g genomes.yaml -t 10

# 2. Validate target genes against the GTF file
uprobe validate-targets -p protocol.yaml -g genomes.yaml

# 3. Extract target region sequences
uprobe generate-targets -p protocol.yaml -g genomes.yaml -o ./results

# 4. Construct initial probes from target sequences
uprobe construct-probes -p protocol.yaml -g genomes.yaml --targets ./results/target_sequences.csv -o ./results

# 5. Post-process probes (add attributes, filter, sort)
uprobe post-process -p protocol.yaml -g genomes.yaml --probes ./results/constructed_probes.csv -o ./results

# 6. Generate visual analysis report
uprobe generate-report -p protocol.yaml -g genomes.yaml --probes ./results/probes_*.csv -o ./results
```

### 2. Python API (Ideal for Backend Integration)

If you are developing a web backend or data analysis pipeline, we recommend directly using `UProbeAPI`. It returns Pandas DataFrames, making it easy to process further.

```python
from pathlib import Path
from uprobe.core.api import UProbeAPI

# Initialize API
uprobe = UProbeAPI(
    protocol_config=Path("protocol.yaml"),
    genomes_config=Path("genomes.yaml"),
    output_dir=Path("./results")
)

# --- Method 1: Complete Workflow ---
df_final = uprobe.run_workflow(threads=10)

# --- Method 2: Step-by-Step Execution ---
uprobe.build_genome_index(threads=10)
uprobe.validate_targets()
df_targets = uprobe.generate_target_seqs()
df_probes = uprobe.construct_probes(df_targets)

import pandas as pd
df_combined = pd.concat([df_targets, df_probes], axis=1)
df_final = uprobe.post_process_probes(df_combined)

# Generate HTML/PDF report
uprobe.generate_report(df_final)
```

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

## Documentation

📖 **Complete documentation is available at [uprobe.readthedocs.io](https://uprobe.readthedocs.io/)**

The documentation includes:
- Detailed installation instructions
- Step-by-step tutorials
- Complete CLI and Python API reference  
- Real-world examples for FISH, PCR, and sequencing applications
- Configuration file reference
- Troubleshooting guide
- Contributing guidelines

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs/
./build_docs.sh
```

Open `docs/build/html/index.html` in your browser to view the local documentation.

## Community & Support

- 📖 **Documentation**: [uprobe.readthedocs.io](https://uprobe.readthedocs.io/)
- 💬 **GitHub Discussions**: [Ask questions and share ideas](https://github.com/UFISH-Team/U-Probe/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/UFISH-Team/U-Probe/issues)
- 🚀 **Contributing**: See our [contributing guide](https://uprobe.readthedocs.io/en/latest/contributing.html)

## Citation

If you use U-Probe in your research, please cite:

```bibtex
@software{uprobe2024,
  title={U-Probe: Universal Probe Design Tool},
  author={Zhang, Qian and Xu, Weize and Cai, Huaiyuan},
  year={2025},
  url={https://github.com/UFISH-Team/U-Probe},
  version={1.0.0}
}
```

## License

U-Probe is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

We thank the bioinformatics community for valuable feedback during development, and the authors of the following tools that U-Probe integrates:

- [Bowtie2](http://bowtie-bio.sourceforge.net/bowtie2/) - Fast sequence alignment
- [BLAST+](https://blast.ncbi.nlm.nih.gov/) - Sequence similarity search  
- [Jellyfish](https://github.com/gmarcais/Jellyfish) - K-mer counting
- [ViennaRNA](https://www.tbi.univie.ac.at/RNA/) - Secondary structure prediction




