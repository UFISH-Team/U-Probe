"""
Command Line Interface for U-Probe.
"""
import sys
from pathlib import Path
import logging

try:
    import click
except ImportError:
    print("Error: click package is required. Install it with: pip install click")
    sys.exit(1)

try:
    from .api import UProbeAPI
    from .utils import get_logger
    from . import __version__
except ImportError as e:
    print(f"Error: Failed to import U-Probe modules: {e}")
    print("Please ensure U-Probe is properly installed: pip install -e .")
    sys.exit(1)

log = get_logger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name='uprobe')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging.')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors.')
@click.pass_context
def cli(ctx, verbose, quiet):
    """
    U-Probe: Universal Probe Design Tool
    
    A powerful and flexible Python-based tool for designing custom DNA or RNA probes
    for various molecular biology applications.
    """
    # Configure logging
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Ensure context is passed to subcommands
    ctx.ensure_object(dict)


@cli.command()
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True), 
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--output', '-o', default='./results', type=click.Path(),
              help='Output directory. [default: ./results]')
@click.option('--raw', is_flag=True,
              help='Save unfiltered raw probe data.')
@click.option('--continue-invalid', is_flag=True,
              help='Continue execution even if some targets are invalid.')
@click.option('--threads', '-t', default=10, type=int,
              help='Number of threads for computation. [default: 10]')
def run(protocol, genomes, output, raw, continue_invalid, threads):
    """
    Execute the complete probe design workflow.
    
    This command runs the entire pipeline from genome index building to final probe generation.
    """
    try:
        log.info("Starting U-Probe complete workflow...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        
        result_df = uprobe.run_workflow(
            raw_csv=raw,
            continue_on_invalid_targets=continue_invalid,
            threads=threads
        )
        
        if result_df.empty:
            log.error("No probes were generated. Check your configuration and input files.")
            sys.exit(1)
        else:
            log.info(f"Workflow completed successfully! Generated {len(result_df)} probes.")
            
    except Exception as e:
        log.error(f"Workflow failed: {e}")
        sys.exit(1)


@cli.command(name='build-index')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--threads', '-t', default=10, type=int,
              help='Number of threads for index building. [default: 10]')
def build_index(protocol, genomes, threads):
    """
    Build genome index for alignment tools.
    
    Creates necessary indices for tools like Bowtie2 and BLAST as specified
    in the genome configuration.
    """
    try:
        log.info("Building genome index...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path('./temp')  # Temporary output dir for index building only
        )
        
        uprobe.build_genome_index(threads=threads)
        log.info("Genome index building completed successfully!")
        
    except Exception as e:
        log.error(f"Index building failed: {e}")
        sys.exit(1)


@cli.command(name='validate-targets')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--continue-invalid', is_flag=True,
              help='Continue with valid targets even if some are invalid.')
def validate_targets(protocol, genomes, continue_invalid):
    """
    Validate target genes against the genome annotation.
    
    Checks if all target genes specified in the protocol exist in the GTF file.
    """
    try:
        log.info("Validating target genes...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path('./temp')  # Temporary output dir for validation only
        )
        
        valid = uprobe.validate_targets(continue_on_invalid=continue_invalid)
        
        if valid:
            log.info("All target genes are valid!")
        elif continue_invalid:
            log.warning("Some targets are invalid but continuing as requested.")
        else:
            log.error("Target validation failed!")
            sys.exit(1)
            
    except Exception as e:
        log.error(f"Target validation failed: {e}")
        sys.exit(1)


@cli.command(name='generate-targets')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--output', '-o', default='./results', type=click.Path(),
              help='Output directory. [default: ./results]')
@click.option('--continue-invalid', is_flag=True,
              help='Continue with valid targets even if some are invalid.')
def generate_targets(protocol, genomes, output, continue_invalid):
    """
    Generate target region sequences from the genome.
    
    Extracts target sequences based on the extraction parameters in the protocol.
    """
    try:
        log.info("Generating target sequences...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        
        # Validate targets first
        if not uprobe.validate_targets(continue_on_invalid=continue_invalid):
            log.error("Target validation failed!")
            sys.exit(1)
        
        df_targets = uprobe.generate_target_seqs()
        
        if df_targets.empty:
            log.error("No target sequences generated!")
            sys.exit(1)
        else:
            log.info(f"Generated {len(df_targets)} target sequences successfully!")
            # Save targets to file
            targets_file = Path(output) / "target_sequences.csv"
            Path(output).mkdir(parents=True, exist_ok=True)
            df_targets.to_csv(targets_file, index=False)
            log.info(f"Target sequences saved to {targets_file}")
            
    except Exception as e:
        log.error(f"Target generation failed: {e}")
        sys.exit(1)


@cli.command(name='construct-probes')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--targets', required=True, type=click.Path(exists=True),
              help='Path to target sequences CSV file.')
@click.option('--output', '-o', default='./results', type=click.Path(),
              help='Output directory. [default: ./results]')
def construct_probes(protocol, genomes, targets, output):
    """
    Construct probes from target sequences.
    
    Takes target sequences and constructs probes according to the probe design
    specifications in the protocol.
    """
    try:
        import pandas as pd
        
        log.info("Constructing probes...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        
        # Load target sequences
        df_targets = pd.read_csv(targets)
        
        df_probes = uprobe.construct_probes(df_targets)
        
        if df_probes.empty:
            log.error("No probes constructed!")
            sys.exit(1)
        else:
            log.info(f"Constructed {len(df_probes)} probes successfully!")
            # Save probes to file
            probes_file = Path(output) / "constructed_probes.csv"
            Path(output).mkdir(parents=True, exist_ok=True)
            df_probes.to_csv(probes_file, index=False)
            log.info(f"Constructed probes saved to {probes_file}")
            
    except Exception as e:
        log.error(f"Probe construction failed: {e}")
        sys.exit(1)


@cli.command(name='post-process')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--probes', required=True, type=click.Path(exists=True),
              help='Path to probe data CSV file (combined targets and probes).')
@click.option('--output', '-o', default='./results', type=click.Path(),
              help='Output directory. [default: ./results]')
@click.option('--raw', is_flag=True,
              help='Save unfiltered raw probe data.')
def post_process(protocol, genomes, probes, output, raw):
    """
    Post-process probes (add attributes and apply filters).
    
    Adds various attributes to probes and applies filtering criteria
    as specified in the protocol.
    """
    try:
        import pandas as pd
        
        log.info("Post-processing probes...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        
        # Load probe data
        df_probes = pd.read_csv(probes)
        
        df_processed = uprobe.post_process_probes(df_probes, raw_csv=raw)
        
        if df_processed.empty:
            log.warning("No probes remaining after post-processing!")
        else:
            log.info(f"Post-processing completed! {len(df_processed)} probes passed filters.")
            
    except Exception as e:
        log.error(f"Post-processing failed: {e}")
        sys.exit(1)


@cli.command(name='generate-barcodes')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--output', '-o', default='./barcodes', type=click.Path(),
              help='Output directory for barcode files. [default: ./barcodes]')
def generate_barcodes(protocol, output):
    """
    Generate DNA barcode sequences.
    
    Creates barcode sequences based on the encoding configuration in the protocol.
    """
    try:
        log.info("Generating barcodes...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config={},  # Not needed for barcode generation
            output_dir=Path(output)
        )
        
        barcode_sets = uprobe.generate_barcodes()
        
        if not barcode_sets:
            log.warning("No barcodes generated!")
        else:
            log.info(f"Generated {len(barcode_sets)} barcode set(s) successfully!")
            
    except Exception as e:
        log.error(f"Barcode generation failed: {e}")
        sys.exit(1)


@cli.command()
def version():
    """Show the U-Probe version."""
    click.echo(f"U-Probe version {__version__}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
