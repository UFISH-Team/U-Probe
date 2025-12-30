import asyncio
import re
from typing import Dict, List, Optional, Union

import yaml

from uprobe.api import UProbeAPI
from uprobe.gen.barcodes import quick_generate

from pantheon.toolset import ToolSet, tool

DEFAULT_PROTOCOL = {
    "name": "",
    "description": "Protocol for designing probes with U-Probe Agent",
    "genome": "",  # This will be updated by the agent
    "extracts": {
        "target_region": {
            "source": "",
            "length": int,
            "overlap": int,
        }
    },
    "targets": [],  # This will be filled by the agent
    "encoding": {},  # This will be filled by the agent
    "probes": {
    },
    "attributes": {},  # This will be filled by the agent
    "post_process": {
        "filters": {}
    },
    "summary": {
        "report_name": "rna_report", # or dna_report
        "attributes": ['']
    }
}

class UProbeToolSet(ToolSet):
    @tool
    async def design_probe(self, 
                           gene_names: List[str], 
                           species: str, 
                           encoding: Optional[Dict[str, Dict[str, str]]] = None, 
                           barcode_length: Optional[int] = None, 
                           extracts: Optional[Dict[str, Union[str, int, float]]] = None,
                           probes_yaml: Optional[str] = None):
        """
        Designs probes for a list of target genes in a specific species, with optional customizations.
        
        Args:
            gene_names: A list of gene names to design probes for.
            species: The name of the target species (e.g., 'human', 'mouse').
            encoding: An optional dictionary specifying barcodes for each gene. e.g. {"gene1": {"BC1": "ACTG"}, "gene2": {"BC1": "GTCA"}}
            barcode_length: If encoding is not provided, specify a length to auto-generate barcodes.
            extracts: An optional dictionary to customize extraction parameters.
                      For example: {"source": "genome", "length": 80, "overlap": 10}.
                      'source' can be one of ['genome', 'exon', 'CDS', 'UTR'].
            probes_yaml: An optional YAML string to define a custom probe structure.
        """
        print(f"Starting probe design for genes {gene_names} in species {species}.")
        
        try:
            # Create a protocol for this specific run
            run_protocol = DEFAULT_PROTOCOL.copy()
            run_protocol["targets"] = gene_names
            run_protocol["genome"] = species
            run_protocol["name"] = f"{'_'.join(gene_names)}_{species}_probes"

            # Dynamically set the report name based on the extract source
            if extracts and extracts.get('source') == 'genome':
                run_protocol['summary']['report_name'] = 'dna_report'
            else:
                run_protocol['summary']['report_name'] = 'rna_report'

            # Handle custom probe structure from YAML
            if probes_yaml:
                try:
                    custom_probes = yaml.safe_load(probes_yaml)
                    if 'probes' in custom_probes:
                        run_protocol['probes'] = custom_probes['probes']
                        print("Using custom probe structure from user input.")
                    else:
                        return {"success": False, "message": "YAML for probe structure is missing the root 'probes' key."}
                except yaml.YAMLError as e:
                    return {"success": False, "message": f"Error parsing probes_yaml: {e}"}

            # Dynamically generate attributes based on probe type (DNA/RNA)
            if 'probes' in run_protocol:
                is_dna_probe = extracts and extracts.get('source') == 'genome'
                
                if is_dna_probe:
                    # DNA-specific attributes
                    attributes_to_calc = {
                        "gcContent": "gc_content", "tm": "annealing_temperature",
                        "selfMatch": "self_match", "foldScore": "fold_score",
                        "mappedSites": "mapped_sites", "kmerCount": "kmer_count"
                    }
                else:
                    # RNA-specific attributes
                    attributes_to_calc = {
                        "gcContent": "gc_content", "tm": "annealing_temperature",
                        "selfMatch": "self_match", "foldScore": "fold_score",
                        "mappedGenes": "n_mapped_genes"
                    }
                
                new_attributes = {}
                summary_attributes = []

                for probe_name, probe_details in run_protocol['probes'].items():
                    if 'parts' in probe_details:
                        for part_name, part_details in probe_details['parts'].items():
                            if 'expr' in part_details and 'target_region' in part_details['expr']:
                                for attr_suffix, attr_type in attributes_to_calc.items():
                                    attr_name = f"{probe_name}_{part_name}_{attr_suffix}"
                                    new_attributes[attr_name] = {
                                        'target': f"{probe_name}.{part_name}",
                                        'type': attr_type
                                    }
                                    # For DNA kmerCount, add some defaults if not present
                                    if is_dna_probe and attr_type == "kmer_count":
                                        new_attributes[attr_name].update({'kmer_len': 35, 'threads': 10, 'size': '1G', 'aligner': 'jellyfish'})
                                    # For DNA mappedSites, add some defaults if not present
                                    if is_dna_probe and attr_type == "mapped_sites":
                                         new_attributes[attr_name].update({'aligner': 'bowtie2'})
                                    # For RNA mappedGenes, add some defaults if not present
                                    if not is_dna_probe and attr_type == "n_mapped_genes":
                                         new_attributes[attr_name].update({'aligner': 'bowtie2', 'min_mapq': 30})
                                    summary_attributes.append(attr_name)
                
                run_protocol['attributes'] = new_attributes
                run_protocol['summary']['attributes'] = list(set(summary_attributes)) # Ensure unique
                print(f"Dynamically generated {len(new_attributes)} attributes for {'DNA' if is_dna_probe else 'RNA'} probe type.")

            # Handle custom extracts
            if extracts:
                valid_sources = ['genome', 'exon', 'CDS', 'UTR']
                if 'source' in extracts and extracts['source'] not in valid_sources:
                    return {"success": False, "message": f"Invalid extracts source: '{extracts['source']}'. Must be one of {valid_sources}."}
                run_protocol['extracts']['target_region'].update(extracts)

            # Handle encoding
            if encoding:
                run_protocol['encoding'] = encoding
                print("Using user-provided encoding.")
            elif barcode_length and probes_yaml:
                # Dynamically find all unique barcode names (e.g., BC1, BC2) from the probes_yaml
                barcode_names = sorted(list(set(re.findall(r"encoding\[target\]\['(.*?)'\]", probes_yaml))))

                if not barcode_names:
                    print("Barcode length was provided, but no barcode expressions (e.g., \"encoding[target]['BC1']\") were found in the probe structure. No barcodes generated.")
                else:
                    print(f"Found barcode names in probe structure: {barcode_names}. Generating barcodes of length {barcode_length}.")
                    num_barcodes_to_generate = len(gene_names) * len(barcode_names)
                    all_barcodes = quick_generate(num_barcodes_to_generate, barcode_length)

                    if len(all_barcodes) < num_barcodes_to_generate:
                        return {"success": False, "message": f"Failed to generate enough unique barcodes. Requested {num_barcodes_to_generate}, got {len(all_barcodes)}."}

                    barcode_iterator = iter(all_barcodes)
                    generated_encoding = {}
                    for gene in gene_names:
                        generated_encoding[gene] = {
                            bc_name: next(barcode_iterator) for bc_name in barcode_names
                        }
                    
                    run_protocol['encoding'] = generated_encoding
                    print("Successfully generated and assigned dynamic barcodes.")
            elif barcode_length:
                print("Warning: `barcode_length` was provided, but no `probes_yaml` was given to parse for barcode names. No barcodes were generated.")

            # Ensure output directory exists
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # Initialize U-Probe API
            uprobe = UProbeAPI(
                protocol_config=run_protocol,
                genomes_config=GENOMES_CONFIG_PATH,
                output_dir=OUTPUT_DIR
            )

            # Run the workflow
            result_df = await asyncio.to_thread(
                uprobe.run_workflow,
                continue_on_invalid_targets=True
            )

            if not result_df.empty:
                csv_output = ""
                # Try to find and read the output CSV file to display to the user
                if hasattr(uprobe, '_csv_filename') and uprobe._csv_filename:
                    csv_path = OUTPUT_DIR / uprobe._csv_filename
                    if csv_path.is_file():
                        try:
                            csv_content = csv_path.read_text(encoding="utf-8", errors="replace")
                            csv_output = f"Here are the results:\n\n```csv\n{csv_content}```\n\n"
                        except Exception as e:
                            csv_output = f"Could not read the result file: {e}\n"

                # Build convenient links to CSV and HTML report for frontend
                csv_url = ""
                if hasattr(uprobe, '_csv_filename') and uprobe._csv_filename:
                    csv_url = f"/agent/files/{uprobe._csv_filename}"

                html_url = ""
                try:
                    # Find the most recent HTML report for this run
                    pattern_prefix = run_protocol.get("name", "probes") + "_report_"
                    html_candidates = sorted(
                        [p for p in OUTPUT_DIR.glob("*.html") if p.name.startswith(pattern_prefix)],
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    if html_candidates:
                        html_url = f"/agent/files/{html_candidates[0].name}"
                except Exception:
                    pass

                links_text = ""
                if html_url or csv_url:
                    links_text = "\n" + (f"Open HTML report: {html_url}\n" if html_url else "") + (f"Download CSV: {csv_url}\n" if csv_url else "")

                message = f"Successfully designed {len(result_df)} probes. {csv_output}The full results are available.{links_text}"
                return {"success": True, "message": message, "output_dir": str(OUTPUT_DIR)}
            else:
                message = "Workflow completed, but no probes were generated. This could be due to invalid targets or strict filters."
                return {"success": False, "message": message}

        except FileNotFoundError as e:
            error_message = f"Configuration file not found: {e}. Please ensure '{GENOMES_CONFIG_PATH}' exists."
            print(error_message)
            return {"success": False, "message": error_message}
        except ValueError as e:
            error_message = f"A value error occurred: {e}. This might be due to an invalid species name or target."
            print(error_message)
            return {"success": False, "message": error_message}
        except Exception as e:
            error_message = f"An unexpected error occurred during the probe design workflow: {e}"
            print(error_message)
            return {"success": False, "message": error_message}