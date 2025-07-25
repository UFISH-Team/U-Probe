"""
This module provides the main API for the uprobe package.
"""
import os
import typing as T
from pathlib import Path
import pandas as pd
import yaml
import time

from .utils import get_logger, gene_barcode
from .attributes import add_attributes
from .tools import build_genome
from .gen.fun import generate_target_seqs, validate_targets
from .gen.probe import construct_probes
from .process import post_process

log = get_logger(__name__)


def build_genome_index(genome_config: dict, threads: int = 10) -> dict:
    """
    Builds genome indices for aligners specified in the genome configuration.

    Args:
        genome_config: A dictionary containing genome information, including 'fasta', 'gtf', and 'align_index' keys.
        threads: The number of threads to use for index construction.

    Returns:
        The updated genome configuration dictionary.
    """
    log.info("Building genome index...")
    updated_genome_config = build_genome(genome_config, threads=threads)
    log.info("Genome index building completed.")
    return updated_genome_config


def get_gene_barcodes(protocol_config: dict) -> dict:
    """
    Extracts gene-to-barcode mappings from the protocol configuration.

    Args:
        protocol_config: The protocol configuration dictionary.

    Returns:
        A dictionary mapping gene names to their corresponding barcodes.
    """
    return gene_barcode(protocol_config)


def run_workflow(
    protocol_config: T.Union[Path, dict],
    genomes_config: T.Union[Path, dict],
    output_dir: Path,
    raw_csv: bool = False,
    continue_on_invalid_targets: bool = False,
) -> pd.DataFrame:
    """
    Runs the full probe design workflow.

    Args:
        protocol_config: Path to the protocol YAML file or a dictionary.
        genomes_config: Path to the genomes YAML file or a dictionary.
        output_dir: Directory to save the output CSV files.
        raw_csv: If True, saves the unprocessed probe data to a CSV file.
        continue_on_invalid_targets: If True, continue with valid targets even if some are invalid.

    Returns:
        A pandas DataFrame containing the final probe information.

    Raises:
        ValueError: If a configuration is invalid or essential data is missing.
        IOError: If a required file (e.g., FASTA, GTF) is not found.
    """
    log.info("--- Starting U-Probe Workflow ---")

    # Ensure output and work directories exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Parse Configurations ---
    log.info("Parsing configurations...")
    if isinstance(protocol_config, Path):
        protocol = yaml.safe_load(protocol_config.read_text(encoding="utf-8"))
    else:
        protocol = protocol_config

    if isinstance(genomes_config, Path):
        genomes = yaml.safe_load(genomes_config.read_text(encoding="utf-8"))
    else:
        genomes = genomes_config

    # --- 2. Validate Genome and Files ---
    genome_name = protocol.get('genome')
    if not genome_name or genome_name not in genomes:
        raise ValueError(f"Genome '{genome_name}' not found in genomes configuration.")
    genome = genomes[genome_name]

    fasta_path = Path(genome['fasta'])
    gtf_path = Path(genome['gtf'])
    if not fasta_path.exists():
        raise IOError(f"Genome FASTA file not found: {fasta_path}")
    if not gtf_path.exists():
        raise IOError(f"Genome GTF file not found: {gtf_path}")
    log.info(f"Using FASTA: {fasta_path} and GTF: {gtf_path}")

    # --- 3. Build Genome Index ---
    log.info("Building genome index...")
    build_genome(genome, threads=60) # Assuming build_genome is idempotent

    # --- 4. Validate Targets ---
    targets = protocol.get("targets", [])
    if not targets:
        raise ValueError("No targets specified in the protocol.")

    log.info("Validating targets...")
    valid, valid_targets, invalid_targets = validate_targets(targets, gtf_path)
    if not valid:
        error_msg = f"Invalid targets found: {invalid_targets}"
        if not continue_on_invalid_targets:
            raise ValueError(error_msg)
        log.warning(f"{error_msg}. Continuing with valid targets as requested.")
        protocol["targets"] = valid_targets
        if not valid_targets:
            raise ValueError("No valid targets remaining after validation.")
    
    # --- 5. Generate Target Region Sequences ---
    log.info("Generating target region sequences...")
    df_targets = generate_target_seqs(
        protocol['extracts']['target_region']['source'],
        protocol["targets"],
        genome['fasta'],
        genome['gtf'],
        overlap=protocol['extracts']['target_region']['overlap'],
        min_length=protocol['extracts']['target_region']['length'],
    )
    if df_targets.empty:
        log.error("No target sequences generated. Check target definitions and extraction parameters.")
        return pd.DataFrame()

    # --- 6. Construct Probes ---
    contexts = [
        {
            "target_region": row['target_region'],
            "gene_id": row['gene_id'],
            "gene_name": row['gene'],
            "encoding": protocol['encoding'],
        }
        for _, row in df_targets.iterrows()
    ]

    log.info("Constructing probes...")
    probe_df = construct_probes(protocol, contexts)
    if probe_df.empty:
        log.error("No probes were constructed. Check probe construction parameters.")
        return pd.DataFrame()

    log.info(f"Successfully generated {probe_df.shape[0]} initial probes.")

    # --- 7. Post-processing and Attribute Addition ---
    df_combined = pd.concat([df_targets.reset_index(drop=True), probe_df.reset_index(drop=True)], axis=1)

    log.info("Adding attributes to probes...")
    df_final = add_attributes(df_combined, protocol, genome)

    time_str = time.strftime("%Y%m%d_%H%M%S")
    name = protocol.get("name", "probes")
    if raw_csv:
        raw_path = output_dir / f"{name}_{time_str}_raw.csv"
        log.info(f"Saving raw results to {raw_path}")
        df_final.to_csv(raw_path, index=False)

    log.info("Post-processing probes...")
    df_processed = post_process(df_final, protocol)
    
    if df_processed.empty:
        log.warning("No probes remaining after post-processing filters.")
    else:
        output_path = output_dir / f"{name}_{time_str}.csv"
        log.info(f"Saving {df_processed.shape[0]} processed probes to {output_path}")
        df_processed.to_csv(output_path, index=False)
    
    log.info("--- U-Probe Workflow Completed ---")
    return df_processed 
