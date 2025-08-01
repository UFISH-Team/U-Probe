"""
Command Line Interface for U-Probe.
"""
import click
from pathlib import Path
import typing as T

from .api import UProbeAPI
from .utils import get_logger

log = get_logger(__name__)

@click.group()
def cli():
    """U-Probe: A tool for designing universal probes."""
    pass

@cli.command()
@click.option('--protocol', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the protocol YAML file.')
@click.option('--genomes', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the genomes YAML file.')
@click.option('--output', required=True, type=click.Path(file_okay=False), help='Output directory for results.')
@click.option('--raw', is_flag=True, help='Save raw, unfiltered probes to a CSV file.')
@click.option('--continue-invalid', is_flag=True, help='Continue even if some targets are invalid.')
@click.option('--threads', default=10, type=int, help='Number of threads for genome indexing.')
def run(protocol: str, genomes: str, output: str, raw: bool, continue_invalid: bool, threads: int):
    """Run the full U-Probe design workflow."""
    api = UProbeAPI(
        protocol_config=Path(protocol),
        genomes_config=Path(genomes),
        output_dir=Path(output)
    )
    api.run_workflow(
        raw_csv=raw,
        continue_on_invalid_targets=continue_invalid,
        threads=threads
    )
    log.info("Workflow finished.")

@cli.command('build-index')
@click.option('--protocol', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the protocol YAML file.')
@click.option('--genomes', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the genomes YAML file.')
@click.option('--threads', default=10, type=int, help='Number of threads to use.')
def build_index(protocol: str, genomes: str, threads: int):
    """Build the genome index for the specified genome."""
    api = UProbeAPI(
        protocol_config=Path(protocol),
        genomes_config=Path(genomes),
        output_dir=Path("/tmp/uprobe_index_build") 
    )
    api.build_genome_index(threads=threads)
    log.info("Genome index building finished.")

@cli.command('validate-targets')
@click.option('--protocol', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the protocol YAML file.')
@click.option('--genomes', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the genomes YAML file.')
@click.option('--continue-invalid', is_flag=True, help='Continue with valid targets if some are invalid.')
def validate_targets_cmd(protocol: str, genomes: str, continue_invalid: bool):
    """Validate targets defined in the protocol file."""
    api = UProbeAPI(
        protocol_config=Path(protocol),
        genomes_config=Path(genomes),
        output_dir=Path("/tmp/uprobe_validate") 
    )
    if api.validate_targets(continue_on_invalid=continue_invalid):
        log.info("Target validation successful.")
    else:
        log.error("Target validation failed.")

@cli.command('generate-barcodes')
@click.option('--protocol', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to the protocol YAML file.')
@click.option('--output', required=True, type=click.Path(file_okay=False), help='Output directory to save barcode files.')
def generate_barcodes_cmd(protocol: str, output: str):
    """Generate DNA barcodes based on the protocol configuration."""
    api = UProbeAPI(
        protocol_config=Path(protocol),
        genomes_config=Path("dummy_genomes.yml"), 
        output_dir=Path(output)
    )
    try:
        api.genomes = {} 
        api.generate_barcodes()
        log.info("Barcode generation finished.")
    except Exception as e:
        dummy_genomes_path = Path("dummy_genomes.yml")
        with open(dummy_genomes_path, "w") as f:
            f.write("dummy_genome:\n  fasta: dummy.fa\n  gtf: dummy.gtf\n")
        Path("dummy.fa").touch()
        Path("dummy.gtf").touch()

        api = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=dummy_genomes_path,
            output_dir=Path(output)
        )
        api.generate_barcodes()
        dummy_genomes_path.unlink()
        Path("dummy.fa").unlink()
        Path("dummy.gtf").unlink()

        log.info("Barcode generation finished.")


if __name__ == '__main__':
    cli()
