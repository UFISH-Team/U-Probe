import os
import typing as T
from pathlib import Path
import pandas as pd
import sys
import time

import yaml

from uprobe.utils import get_logger
from uprobe.attributes import add_attributes
from uprobe.tools import  build_genome
from uprobe.gen.fun import generate_target_seqs, validate_targets
from uprobe.gen.probe import construct_probes
from uprobe.process import post_process

log = get_logger(__name__)

def parse_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    res = yaml.load(content, Loader=yaml.FullLoader)
    return res

def check_protocol_yaml(res: dict):
    assert "genome" in res, "genome key not found"
    assert "name" in res, "name key not found"


def construct_workflow(
        protocol_yaml: T.Union[Path, dict],
        genomes_yaml: T.Union[Path, dict],
        output_csv: Path,
        workdir: Path = Path("."),
        raw_csv: bool = False,
        ) -> T.Callable:

    log.info("--------------------------------")
    log.info("constructing workflow")
    log.info("--------------------------------")

    if isinstance(protocol_yaml, dict):
        protocol = protocol_yaml
    else:
        log.info("parsing protocol yaml")
        protocol = parse_yaml(protocol_yaml)
        check_protocol_yaml(protocol)
    
    if isinstance(genomes_yaml, dict):
        genomes = genomes_yaml
    else:
        log.info("parsing genomes yaml")
        genomes = parse_yaml(genomes_yaml)

    genome_name = protocol['genome']
    genome = genomes[genome_name]

    fasta_path = Path(genome['fasta'])
    assert fasta_path.exists(), f"genome fasta file not found: {fasta_path}"
    log.info(f"found genome fasta file: {fasta_path}")

    gtf_path = Path(genome['gtf'])
    assert gtf_path.exists(), f"genome gtf file not found: {gtf_path}"
    log.info(f"found genome gtf file: {gtf_path}")

    log.info("--------------------------------")
    log.info("building genome index")
    genome = build_genome(genome, threads=60)

    log.info("--------------------------------")
    workdir.mkdir(parents=True, exist_ok=True)
    os.chdir(workdir)

    def workflow():
        log.info(f"changed working directory to: {os.getcwd()}")
        log.info(f"running workflow name: {protocol['name']}")
        
        targets = protocol["targets"]
        
        # validate targets
        log.info("--------------------------------")
        log.info("** validating targets:")
        valid, valid_targets, invalid_targets = validate_targets(targets, gtf_path)
        
        if not valid:
            log.error("invalid targets, please check the targets in the protocol yaml file")
            log.error(f"invalid targets: {invalid_targets}")
            log.info("you can continue using the valid targets, or exit the program")
            
            # prompt user to continue
            user_input = input("continue using the valid targets?(y/n): ")
            if user_input.lower() != 'y':
                log.info("user choose to exit the program")
                sys.exit(1)
            else:
                log.info(f"continue using the valid targets: {valid_targets}")
                # update targets in protocol
                protocol["targets"] = valid_targets
        log.info("--------------------------------")
        log.info("** generating target region sequences...")
        df_targets = generate_target_seqs(
            protocol['extracts']['target_region']['source'],
            protocol["targets"],
            genome['fasta'],
            genome['gtf'],
            overlap = protocol['extracts']['target_region']['overlap'],
            min_length=protocol['extracts']['target_region']['length'],
        )
        
        if df_targets.empty:
            log.error("no target sequences generated. please check your targets and extraction parameters")
            return
            
        contexts = []
        encoding_dict = protocol['encoding']
        for _, row in df_targets.iterrows():
            contexts.append({
            "target_region": row['target_region'],
            "gene_id": row['gene_id'],
            "gene_name": row['gene'],
            "encoding": encoding_dict,})

        log.info("--------------------------------")
        log.info("** constructing probes:")
        probe_df = construct_probes(workdir, protocol, contexts)

        if probe_df.empty:
            log.error("no probes constructed. please check your probe construction parameters")
            return
            
        log.info(f"generated {probe_df.shape[0]} probes for {df_targets['gene'].unique().shape[0]} targets")
        
        try:
            df = pd.concat([df_targets, probe_df], axis=1)
            log.info("--------------------------------")
            log.info("** adding attributes to probes:")
            df = add_attributes(df, protocol, genome, workdir)
            
            time_str = time.strftime("%Y%m%d_%H%M%S")
            if raw_csv:
                raw_path = f"raw_{output_csv.stem}_{time_str}.csv"
                log.info(f"saving raw results to csv: {raw_path}")
                df.to_csv(raw_path, index=False)
            
            log.info("--------------------------------")
            log.info("** post-processing the results:")
            df_before = df.shape[0]
            df = post_process(df, protocol)
            df_after = df.shape[0]
            
            log.info(f"post-processing: {df_before} rows before, {df_after} rows after, {df_before - df_after} rows removed")

            if df.shape[0] == 0:
                log.warning("no results after post-processing. please check your filtering criteria")
            else:                
                output_path = f"{output_csv.stem}_{time_str}.csv"
                log.info(f"saving post-processed results to csv: {output_path}")
                df.to_csv(output_path, index=False)
                log.info(f"successfully saved {df.shape[0]} probes to csv: {output_path}")
            log.info("--------------------------------")
            log.info("** workflow completed")
        except Exception as e:
            log.error(f"error during post-processing: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            log.info("--------------------------------")
            log.info("** workflow completed with error")
    return workflow


if __name__ == "__main__":
    import fire
    def main(
            protocol_yaml: T.Union[Path, str, dict],
            genomes_yaml: T.Union[Path, str, dict],
            output_csv: str, # the name of the output csv file
            workdir: str = "tests", # the working directory
            raw_csv: bool = False): 
        workflow = construct_workflow(
            Path(protocol_yaml),
            Path(genomes_yaml),
            Path(output_csv),
            Path(workdir),
            raw_csv
        )
        workflow()
    fire.Fire(main)
