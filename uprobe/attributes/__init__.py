import secrets
from pathlib import Path
import pandas as pd
from ._attributes import (
    count_n_bowtie2_aligned_genes,
    cal_temp, cal_gc_content,
    cal_target_fold_score,
    cal_self_match, cal_target_blocks
)

def add_attributes(
        df_probes: pd.DataFrame,
        protocol: dict,
        genome: dict,
        workdir: Path
) -> pd.DataFrame:
    attributes: dict = protocol['attributes']
    task_id = secrets.token_hex(6)  
    for attr_name, attr in attributes.items():
        target = attr.get('target')
        if target is None:
            print(f"Warning: 'target' key is missing in attribute '{attr_name}'")
            continue
        if target not in df_probes.columns:
            print(f"Warning: '{target}' not found in DataFrame columns.")
            continue  
        attr_type: str = attr.get('type', '').lower() 

        if attr_type == "n_mapped_genes":
            if attr.get('aligner') == "bowtie2":
                assert 'bowtie2' in genome['align_index'] 
                fasta_path = Path(genome['fasta'])
                index_prefix = fasta_path.parent / 'bowtie2_genome' / fasta_path.stem
                outdir = workdir / "tmp"
                outdir.mkdir(exist_ok=True, parents=True)
                vals = df_probes.apply(
                    lambda row: count_n_bowtie2_aligned_genes(
                        str(outdir), {f"{row['exon_name']}_{row['start']}": row[target]}, task_id,
                        str(index_prefix),
                        attr.get("threads", 10), 
                    ), axis=1
                )
            else:
                raise NotImplementedError(
                    f"Aligner {attr['aligner']} is not implemented."
                )
        elif attr_type == "annealing_temperature":
            vals = df_probes[target].apply(cal_temp).round(2)
        elif attr_type == "gc_content":
            vals = df_probes[target].apply(cal_gc_content).round(2)
        elif attr_type == "fold_score":
            vals = df_probes[target].apply(cal_target_fold_score).round(2)
        elif attr_type == "self_match":
            vals = df_probes[target].apply(cal_self_match).round(2)
        elif attr_type == "blocks":
            if 'start' not in df_probes.columns:
                print(f"Warning: 'start' column not found for attribute '{attr_name}'")
                continue
            vals = df_probes.apply(lambda row: cal_target_blocks(row[target], row['start']), axis=1)
        else:
            raise NotImplementedError(
                f"Attribute type {attr_type} is not implemented."
            )
        df_probes[attr_name] = vals
    return df_probes