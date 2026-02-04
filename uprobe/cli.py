import sys
from pathlib import Path
import logging
import click
import yaml
import copy
import pandas as pd


from .api import UProbeAPI
from .utils import get_logger
from . import __version__


log = get_logger(__name__)


def _extract_probe_targets(probes_config: dict) -> list:
    """
    Extract all probe and part targets from probes configuration.
    Returns list of (target_name, is_probe_level) tuples.
    Examples: [('probe_1', True), ('probe_1.part1', False), ('probe_1.part2', False)]
    """
    if not isinstance(probes_config, dict):
        raise ValueError(
            "Invalid protocol: `probes` must be a YAML mapping (dict) like "
            "`probes: { probe_1: {template: ..., parts: {...}} }`. "
            "Do NOT use list-style probes."
        )

    targets = []
    
    def traverse_parts(prefix: str, config: dict, is_top_level: bool = False):
        """Recursively traverse probe parts."""
        if is_top_level:
            targets.append((prefix, True))  # probe level
        
        if 'parts' in config:
            if not isinstance(config['parts'], dict):
                raise ValueError(
                    f"Invalid protocol: `{prefix}.parts` must be a mapping (dict). "
                    "Do NOT use list-style parts; use `parts: {part1: {...}, part2: {...}}`."
                )
            for part_name, part_config in config['parts'].items():
                part_full_name = f"{prefix}.{part_name}"
                targets.append((part_full_name, False))  # part level
                # Recursively handle nested parts
                if 'parts' in part_config:
                    traverse_parts(part_full_name, part_config, is_top_level=False)
    
    for probe_name, probe_config in probes_config.items():
        traverse_parts(probe_name, probe_config, is_top_level=True)
    
    return targets


def _generate_default_attributes(protocol_config: dict) -> dict:
    """
    Generate default attributes based on probes structure and mode (DNA/RNA).
    DNA mode focuses on probe parts; RNA mode includes target_region + all probes/parts.
    """
    source = protocol_config['extracts']['target_region'].get('source', 'genome')
    is_dna_mode = (source == 'genome')
    probes_config = protocol_config.get('probes', {})
    
    attributes = {}
    
    # DNA mode: minimal or no target_region attributes (focus on probe parts)
    # RNA mode: comprehensive target_region attributes
    if not is_dna_mode:
        # RNA mode: add full target_region attributes
        attributes['target_gc'] = {
            'target': 'target_region',
            'type': 'gc_content'
        }
        attributes['target_tm'] = {
            'target': 'target_region',
            'type': 'annealing_temperature'
        }
        attributes['target_fold'] = {
            'target': 'target_region',
            'type': 'fold_score'
        }
        attributes['target_self_match'] = {
            'target': 'target_region',
            'type': 'self_match'
        }
        attributes['target_mapped_genes'] = {
            'target': 'target_region',
            'type': 'n_mapped_genes',
            'aligner': 'bowtie2',
            'min_mapq': 30
        }
    
    # Extract probe targets and generate attributes
    probe_targets = _extract_probe_targets(probes_config)
    
    for target_name, is_probe_level in probe_targets:
        # Generate safe attribute name (replace dots with underscores)
        safe_name = target_name.replace('.', '_')
        
        # DNA mode: focus on probe parts only
        # RNA mode: include both probe-level and part-level
        if is_dna_mode and is_probe_level:
            # DNA: skip probe-level attributes, only process parts
            continue
        
        # Common attributes for probes/parts
        attributes[f'{safe_name}_gc'] = {
            'target': target_name,
            'type': 'gc_content'
        }
        attributes[f'{safe_name}_tm'] = {
            'target': target_name,
            'type': 'annealing_temperature'
        }
        attributes[f'{safe_name}_fold'] = {
            'target': target_name,
            'type': 'fold_score'
        }
        attributes[f'{safe_name}_self_match'] = {
            'target': target_name,
            'type': 'self_match'
        }
        
        # DNA mode: add specificity attributes to probe parts
        if is_dna_mode and not is_probe_level:
            # Add mapped_sites and kmer_count for DNA probe parts
            attributes[f'{safe_name}_mapped_sites'] = {
                'target': target_name,
                'type': 'mapped_sites',
                'aligner': 'bowtie2'
            }
            attributes[f'{safe_name}_kmer_count'] = {
                'target': target_name,
                'type': 'kmer_count',
                'kmer_len': 35,
                'threads': 10,
                'size': '1G',
                'aligner': 'jellyfish'
            }
    
    return attributes


def _generate_default_summary(protocol_config: dict, attributes: dict) -> dict:
    """
    Generate default summary configuration based on mode (DNA/RNA) and attributes.
    DNA: report_name=dna_report, includes probe part attributes
    RNA: report_name=rna_report, includes target + probe-level attributes
    """
    source = protocol_config['extracts']['target_region'].get('source', 'genome')
    is_dna_mode = (source == 'genome')
    
    summary = {
        'report_name': 'dna_report' if is_dna_mode else 'rna_report',
        'attributes': []
    }
    
    # Select attributes for summary based on mode
    for attr_name in attributes.keys():
        if is_dna_mode:
            # DNA: include part-level attributes (gc, tm, kmer_count)
            if '_part' in attr_name and any(attr_name.endswith(x) for x in ['_gc', '_tm', '_kmer_count']):
                summary['attributes'].append(attr_name)
        else:
            # RNA: include target + probe-level attributes (not parts)
            if attr_name.startswith('target_'):
                # Include target attributes
                if any(attr_name.endswith(x) for x in ['_gc', '_tm', '_fold', '_self_match', '_mapped_genes']):
                    summary['attributes'].append(attr_name)
            elif '_part' not in attr_name:
                # Include probe-level attributes (not parts)
                if any(attr_name.endswith(x) for x in ['_gc', '_tm', '_fold']):
                    summary['attributes'].append(attr_name)
            else:
                # Include key part attributes for RNA as well
                if any(attr_name.endswith(x) for x in ['_tm']):
                    summary['attributes'].append(attr_name)
    
    return summary


def _generate_default_post_process(protocol_config: dict, attributes: dict) -> dict:
    """
    Generate default post_process configuration based on attributes.
    """
    source = protocol_config['extracts']['target_region'].get('source', 'genome')
    is_dna_mode = (source == 'genome')
    
    post_process = {
        'filters': {},
        'sorts': {
            'is_ascending': [],
            'is_descending': []
        }
    }
    
    # Generate filters for target_region attributes
    if 'target_gc' in attributes:
        post_process['filters']['target_gc'] = {
            'condition': 'target_gc >= 0.2 & target_gc <= 0.8'  # GC is 0-1 fraction
        }
    
    if 'target_tm' in attributes:
        post_process['filters']['target_tm'] = {
            'condition': 'target_tm >= 50 & target_tm <= 90'  # Tm in Celsius
        }
    
    # Mode-specific filters
    if is_dna_mode:
        if 'target_kmer_count' in attributes:
            post_process['filters']['target_kmer_count'] = {
                'condition': 'target_kmer_count <= 100'
            }
    else:
        if 'target_mapped_genes' in attributes:
            post_process['filters']['target_mapped_genes'] = {
                'condition': 'target_mapped_genes <= 10'
            }
    
    # Generate filters for probe/part attributes (only Tm filters for parts)
    for attr_name in attributes.keys():
        if attr_name.startswith('target_'):
            continue
        
        # Add Tm filters for all probes/parts
        if attr_name.endswith('_tm'):
            post_process['filters'][attr_name] = {
                'condition': f'{attr_name} >= 50 & {attr_name} <= 90'
            }
        
        # Add GC filters for probe-level only (not parts)
        if attr_name.endswith('_gc') and '.' not in attributes[attr_name]['target']:
            post_process['filters'][attr_name] = {
                'condition': f'{attr_name} >= 0.2 & {attr_name} <= 0.8'
            }
    
    # Generate sorts
    # Ascending: GC and Tm (prefer moderate values)
    for attr_name in attributes.keys():
        if attr_name.endswith('_gc') or attr_name.endswith('_tm'):
            post_process['sorts']['is_ascending'].append(attr_name)
    
    # Descending: fold_score, self_match, mapped_genes, kmer_count (prefer lower values = better)
    for attr_name in attributes.keys():
        if any(attr_name.endswith(suffix) for suffix in ['_fold', '_self_match', '_mapped_genes', '_kmer_count']):
            post_process['sorts']['is_descending'].append(attr_name)
    
    return post_process


def _validate_and_normalize_protocol(protocol_config: dict) -> dict:
    """
    Validate protocol configuration and inject defaults for optional fields.
    Dynamically generates attributes and post_process based on probes structure.
    """
    # 1. Check required top-level keys
    required_keys = ['genome', 'targets', 'extracts', 'encoding', 'probes']
    missing_keys = [k for k in required_keys if k not in protocol_config]
    if missing_keys:
        raise ValueError(f"Protocol is missing required keys: {', '.join(missing_keys)}")
    
    # Check extracts.target_region
    if 'target_region' not in protocol_config.get('extracts', {}):
        raise ValueError("Protocol must define 'extracts.target_region'")
    
    # 2. Determine mode (DNA vs RNA)
    source = protocol_config['extracts']['target_region'].get('source', 'genome')
    is_dna_mode = (source == 'genome')

    # 2.1 Clean up user-provided post_process (remove empty stubs and DNA-only keys in RNA mode)
    # Agents/users sometimes write placeholders like:
    #   post_process:
    #     filters: {}
    #     avoid_otp: {}
    #     equal_space: {}
    # These should be treated as "missing" so defaults can be generated, and RNA mode
    # must not carry DNA-only steps.
    pp = protocol_config.get('post_process')
    if isinstance(pp, dict):
        if not is_dna_mode:
            pp.pop('avoid_otp', None)
            pp.pop('equal_space', None)
        # Drop empty/None/list stubs at top-level
        pp = {k: v for k, v in pp.items() if v not in ({}, [], None)}
        protocol_config['post_process'] = pp
    
    # 3. Auto-complete attributes if missing (dynamic generation based on probes structure)
    if 'attributes' not in protocol_config or not protocol_config['attributes']:
        log.info(f"Attributes missing or empty. Auto-generating from probes structure for mode: {'DNA' if is_dna_mode else 'RNA'}")
        protocol_config['attributes'] = _generate_default_attributes(protocol_config)
    
    # 4. Auto-complete post_process if missing (dynamic generation based on attributes)
    if 'post_process' not in protocol_config or not protocol_config['post_process']:
        log.info("Post-process configuration missing or empty. Auto-generating from attributes.")
        protocol_config['post_process'] = _generate_default_post_process(
            protocol_config, 
            protocol_config['attributes']
        )
    
    # 5. Auto-complete summary if missing (dynamic generation based on mode and attributes)
    if 'summary' not in protocol_config or not protocol_config['summary']:
        log.info(f"Summary configuration missing or empty. Auto-generating with report_name: {'dna_report' if is_dna_mode else 'rna_report'}")
        protocol_config['summary'] = _generate_default_summary(
            protocol_config,
            protocol_config['attributes']
        )
    
    return protocol_config


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
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
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
        
        # Load and validate protocol
        protocol_path = Path(protocol)
        with open(protocol_path, 'r', encoding='utf-8') as f:
            protocol_config = yaml.safe_load(f) or {}
            
        if not isinstance(protocol_config, dict):
            raise ValueError("Protocol YAML must be a mapping (dict)")
            
        # Normalize protocol (inject defaults)
        protocol_config = _validate_and_normalize_protocol(protocol_config)
        
        uprobe = UProbeAPI(
            protocol_config=protocol_config,
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        result_df = uprobe.run_workflow(
            raw_csv=raw,
            continue_on_invalid_targets=continue_invalid,
            threads=threads
        )
        if not result_df.empty:
            log.info(f"Workflow completed successfully with {len(result_df)} final probes!")
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
            output_dir=Path('./temp') 
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
            output_dir=Path('./temp')  
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
        if not uprobe.validate_targets(continue_on_invalid=continue_invalid):
            log.error("Target validation failed!")
            sys.exit(1)
        
        df_targets = uprobe.generate_target_seqs()
        
        if df_targets.empty:
            log.error("No target sequences generated!")
            sys.exit(1)
        else:
            log.info(f"Generated {len(df_targets)} target sequences successfully!")
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
        log.info("Post-processing probes...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
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
@click.option('--protocol', '-p', type=click.Path(exists=True),
              help='Path to protocol config file (YAML). Used if no strategy is specified.')
@click.option('--output', '-o', default='./barcodes', type=click.Path(),
              help='Output directory for barcode files. [default: ./barcodes]')
@click.option('--strategy', '-s', type=click.Choice(['max_orthogonality', 'max_size', 'precomputed', 'pcr', 'sequencing']),
              help='Generation strategy to use.')
@click.option('--name', default='barcodes', help='Name for the generated barcode set.')
@click.option('--num-barcodes', type=int, help='Number of barcodes to generate.')
@click.option('--length', type=int, help='Length of each barcode.')
@click.option('--k-constraint', type=int, help='K-mer constraint for max_size strategy.')
@click.option('--library-name', help='Name of precomputed library (e.g., "kishi2018").')
@click.option('--alphabet', default='ACT', help='Nucleotide alphabet to use.')
@click.option('--gc-limits', help='GC content limits (min,max), e.g., "25,75".')
@click.option('--prevent-patterns', help='Comma-separated patterns to prevent, e.g., "AAAA,TTTT".')
@click.option('--save/--no-save', default=True, help='Save barcodes to a CSV file.')
@click.option('--analyze/--no-analyze', default=False, help='Analyze and save quality metrics.')
def generate_barcodes(protocol, output, strategy, name, num_barcodes, length, k_constraint,
                      library_name, alphabet, gc_limits, prevent_patterns, save, analyze):
    """
    Generate DNA barcode sequences.

    Can generate from a protocol file or from command-line arguments.
    """
    try:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        uprobe = UProbeAPI(
            protocol_config=Path(protocol) if protocol else {},
            genomes_config={},
            output_dir=output_dir,
            require_genome=False
        )
        if protocol:
            log.info("Generating barcodes from protocol file...")
            barcode_sets = uprobe.generate_barcodes()
        elif strategy:
            log.info(f"Generating barcodes using '{strategy}' strategy...")            
            params = {'strategy': strategy}
            if length:
                params['length'] = length
            if alphabet:
                params['alphabet'] = alphabet
            if gc_limits:
                params['gc_limits'] = [int(x.strip()) for x in gc_limits.split(',')]
            if prevent_patterns:
                params['prevent_patterns'] = [x.strip() for x in prevent_patterns.split(',')]            
            if strategy in ['max_orthogonality', 'pcr', 'sequencing']:
                if not num_barcodes:
                    raise click.UsageError("Option '--num-barcodes' is required for this strategy.")
                params['num_barcodes'] = num_barcodes
                if strategy == 'pcr':
                    params.setdefault('length', 8)
                    params.setdefault('alphabet', 'ACGT')
                    params.setdefault('gc_limits', (params['length']//4, 3*params['length']//4))
                    params.setdefault('prevent_patterns', ["AAAA", "TTTT", "CCCC", "GGGG"])
                elif strategy == 'sequencing':
                    params.setdefault('length', 12)
                    params.setdefault('alphabet', 'ACGT')
                    params.setdefault('gc_limits', (params['length']//3, 2*params['length']//3))
                    params.setdefault('prevent_patterns', ["AAA", "TTT", "CCC", "GGG"])
            elif strategy == 'max_size':
                if not k_constraint or not length:
                    raise click.UsageError("Options '--k-constraint' and '--length' are required for max_size strategy.")
                params['k_constraint'] = k_constraint
            elif strategy == 'precomputed':
                if not library_name:
                    raise click.UsageError("Option '--library-name' is required for precomputed strategy.")
                params['library_name'] = library_name
            if save:
                params['save_file'] = f"{name}.csv"           
            if analyze:
                params['analyze_quality'] = True
            barcode_config = {name: params}
            barcode_sets = uprobe.run_barcode_generation(barcode_config)            
        else:
            raise click.UsageError("Either '--protocol' or '--strategy' must be provided.")
        if not barcode_sets:
            log.warning("No barcodes were generated.")
        else:
            log.info(f"Generated {len(barcode_sets)} barcode set(s) successfully!")
    except Exception as e:
        log.error(f"Barcode generation failed: {e}", exc_info=log.getEffectiveLevel() == logging.DEBUG)
        sys.exit(1)


@cli.command(name='generate-report')
@click.option('--protocol', '-p', required=True, type=click.Path(exists=True),
              help='Path to probe design protocol configuration file (YAML).')
@click.option('--genomes', '-g', required=True, type=click.Path(exists=True),
              help='Path to genome configuration file (YAML).')
@click.option('--probes', required=True, type=click.Path(exists=True),
              help='Path to processed probe results CSV file.')
@click.option('--output', '-o', default='./results', type=click.Path(),
              help='Output directory for report files. [default: ./results]')
@click.option('--no-plots', is_flag=True,
              help='Skip plot generation and only create text reports.')
@click.option('--pdf', is_flag=True, default=True,
              help='Generate PDF version of reports (default: enabled).')
@click.option('--no-pdf', is_flag=True,
              help='Skip PDF generation and only create markdown reports.')
def generate_report(protocol, genomes, probes, output, no_plots, pdf, no_pdf):
    """
    Generate interpretation report and plots for probe results.
    
    Creates detailed explanations of probe data columns and visualization plots
    to help users understand and select optimal probes.
    """
    try:
        import pandas as pd
        
        log.info("Generating probe analysis report...")
        uprobe = UProbeAPI(
            protocol_config=Path(protocol),
            genomes_config=Path(genomes),
            output_dir=Path(output)
        )
        df_probes = pd.read_csv(probes)       
        if df_probes.empty:
            log.error("No probe data found in the input file!")
            sys.exit(1)
        generate_pdf = pdf and not no_pdf
        results = uprobe.generate_report(df_probes, include_plots=not no_plots, generate_pdf=generate_pdf)
        n_reports = len(results.get('reports', []))
        n_plots = len(results.get('plots', []))
        n_pdfs = len(results.get('pdfs', []))        
        if n_reports + n_plots + n_pdfs == 0:
            log.warning("No reports or plots were generated. Check your protocol configuration.")
        else:
            log.info(f"Report generation completed!")
            if n_reports > 0:
                log.info(f"Generated {n_reports} markdown report(s)")
            if n_pdfs > 0:
                log.info(f"Generated {n_pdfs} PDF report(s)")
            if n_plots > 0:
                log.info(f"Generated {n_plots} visualization plot(s)")        
    except Exception as e:
        log.error(f"Report generation failed: {e}")
        sys.exit(1)


@cli.command()
def agent():
    """Start an interactive session with the U-Probe Agent."""
    import asyncio
    try:
        from uprobe.agent.uprobe_agent import run_interactive_session
    except ImportError as e:
        log.error(f"Failed to import U-Probe Agent modules: {e}")
        log.error("Please ensure all agent dependencies are installed.")
        sys.exit(1)
    log.info("Starting U-Probe Agent interactive session...")
    log.info("This will launch a conversational agent to help you design probes.")
    asyncio.run(run_interactive_session())


@cli.command()
def version():
    """Show the U-Probe version."""
    click.echo(f"U-Probe version {__version__}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
