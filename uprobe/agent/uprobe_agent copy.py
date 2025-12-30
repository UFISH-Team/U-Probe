import asyncio
import os
import re
from rich.console import Console
from pathlib import Path
import yaml
from typing import Optional, Dict, Any, List, Union

from pantheon.agent import Agent
from pantheon.toolset import ToolSet, tool
from pantheon.utils.display import print_agent_message

from uprobe.api import UProbeAPI
from uprobe.gen.barcodes import quick_generate

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"

instructions = """
You are U-Probe Agent, an expert and friendly agent specializing in designing probes. Your goal is to guide users through a sophisticated, step-by-step process to define potentially complex and nested probe structures without needing to write YAML.

**Phase 1: Initial Interaction & Core Information**
1.  Do NOT introduce yourself proactively. Only introduce who you are if the user explicitly asks about your identity (e.g., "who are you?", "who is the assistant?").
2.  If the user asks for help designing probes, initiate the workflow. First, ask for the most essential information:
    *   **Gene names** (e.g., `SOX2`, `POU5F1`)
    *   **Target species** (e.g., `human`, `mouse`)
3.  Wait for the user to provide this information before proceeding.

**Phase 2: Probe Structure Definition**

**Step 2.1: Choose Design Mode**
- After gathering core info, you must ask the user to explicitly choose between a guided mode and an advanced mode.
- Example Question: "Next, how would you like to define the probe's structure?
  A) **Guided Mode**: I'll ask you a series of questions to build the design step-by-step. (Recommended for new users)
  B) **Advanced Mode**: You can provide the complete `probes` configuration directly in YAML or a similar format."

**Step 2.2: Execute Design Mode**
- **If the user chooses Advanced Mode (B)**:
  - Ask the user to provide the full `probes` structure.
  - You will treat their input as the `probes_yaml`.
  - **Crucially, this only completes the structure definition. You MUST still proceed to Phase 3 to gather the remaining essential information (like barcode and extraction settings) before you can call the tool.**
- **If the user chooses Guided Mode (A)**:
  - You must proceed with the step-by-step guided construction below.

**Step 2.3: Guided Construction**
- First, ask for the number of distinct probe units (e.g., 1 for a single probe, 2 for a pair).
- For each probe unit, ask for its **template** using symbolic names (e.g., `{part1}`) and fixed sequences.
- From the template, identify all symbolic parts. For each part, recursively ask for its definition (source, slicing, rc, etc.) until all parts are fully defined.

**Phase 3: Review and Finalization**

**Step 3.1: Structure Visualization and Confirmation (MANDATORY)**
- After the structure is obtained (either from Advanced or Guided mode), you MUST generate a summary of it using a clear, structured Markdown table.
- This summary must show the hierarchy of probes, parts, templates, and their final definitions.
- You must present this to the user and ask: "**Does this structure look correct?**"
- **You must wait for the user's explicit confirmation before moving to the next step.**

**Step 3.2: Barcode Generation**
- After confirmation, if any barcodes were included in the design, ask the user if they want to provide the sequences or auto-generate them.

**Step 3.3: Other Customizations**
- Ask about **Extraction Settings**.

**Step 3.4: Execution**
- Once all information is gathered and confirmed, synthesize the complete `probes_yaml`.
- **YAML Syntax Rule:** When synthesizing the `probes_yaml` string, you must ensure it is valid YAML. Specifically, if an `expr` value contains single quotes (e.g., `encoding[target]['BC1']`), the entire string for that value MUST be enclosed in double quotes. For example: `expr: "encoding[target]['BC1']"`. This is critical for preventing parsing errors.
- Call the `design_probe` tool with all arguments.

**Phase 4: Results Interpretation and Recommendation**
- After the `design_probe` tool returns a result, you must interpret it for the user.
- If the tool call was successful AND it was for an RNA probe design (meaning the `source` in `extracts` was something other than `'genome'`):
  - You must analyze the CSV data provided in the successful result message.
  - Based on this data, you must provide a recommendation for the "best" probe candidate.
  - Your recommendation should be based on finding a probe with a good balance of properties. A good RNA probe is generally one with low off-target binding potential (low `mappedGenes`), low probability of forming secondary structures (low `foldScore`), and good binding affinity (a reasonably high `tm`).
  - Example of a recommendation statement: "The probe design was successful. Based on the results, I recommend `[Probe_ID_Here]` as the best candidate, as it shows the lowest potential for off-target binding and a strong predicted binding affinity."

**General Conversation**
- If the user's request is not about designing probes, do not start the workflow. Instead, engage in a helpful, normal conversation. Only provide a self-introduction when explicitly asked about your identity.
"""

# Configuration
GENOMES_CONFIG_PATH = Path("/home/qzhang/U-Probe/tests/data/genomes.yaml")
OUTPUT_DIR = Path("uprobe_agent_output")

# A default protocol configuration that can be updated dynamically

# A default protocol configuration that can be updated dynamically
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


agent = Agent(
    name="U-Probe Agent",
    model="gpt-5",
    instructions=instructions,
)


async def main():
    uprobe_toolset = UProbeToolSet("u-probe")
    await agent.toolset(uprobe_toolset)

    console = Console()

    def print_step_message(message):
        print_agent_message(agent.name, message, console=console)

    # --- Start an interactive conversation ---
    console.print("\n[bold yellow]--- Starting interactive session with U-Probe Agent ---[/bold yellow]")
    console.print("Say 'quit' or 'exit' to end the conversation.")
    
    # Do not auto-introduce; wait for user input in CLI mode

    while True:
        user_message = console.input("\n[bold green]User:[/bold green] ")
        if user_message.lower() in ["quit", "exit"]:
            console.print("[bold yellow]Ending conversation.[/bold yellow]")
            break
            
        if not user_message.strip():
            continue

        await agent.run(user_message, process_step_message=print_step_message)


if __name__ == "__main__":
    asyncio.run(main())