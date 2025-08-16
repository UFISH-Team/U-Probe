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
) -> pd.DataFrame:
    attributes: dict = protocol['attributes']
    task_id = secrets.token_hex(6)  
    for attr_name, attr in attributes.items():
        target = attr.get('target')
        if target is None:
            print(f"Warning: 'target' key is missing in attribute '{attr_name}'")
            continue
        
        # Handle naming inconsistency: try both colon and dot formats
        actual_target = target
        if target not in df_probes.columns:
            # Try replacing colon with dot
            dot_target = target.replace(':', '.')
            if dot_target in df_probes.columns:
                actual_target = dot_target
            else:
                print(f"Warning: '{target}' not found in DataFrame columns.")
                print(f"Available columns: {list(df_probes.columns)}")
                continue
        
        attr_type: str = attr.get('type', '').lower() 

        if attr_type == "avoid_otp":
            if attr.get('aligner') == "bowtie2":
                assert 'bowtie2' in genome['align_index'] 
                fasta_path = Path(genome['fasta'])
                index_prefix = fasta_path.parent / 'bowtie2_genome' / fasta_path.stem
                tmp_dir = Path("tmp")
                tmp_dir.mkdir(exist_ok=True, parents=True)
                from uprobe.attributes._attributes import static_otp
                pool_name = df_probes['pool_name'].iloc[0]
                region = df_probes['region'].iloc[0]
                target_seq = df_probes['target_seq'].iloc[0]
                targets = protocol['targets']
                target_regions = [target.split(';')[1] for target in targets if target.split(';')[0] == pool_name]
                counted = static_otp(tmp_dir, pool_name, region, target_seq, index_prefix, attr.get("threads", 10), target_regions, attr.get("density_thresh", 1e-5), attr.get("avoid_target_overlap", True), attr.get("search_range", (-10**6, 10**6)))
                df_probes[f'{attr_name}_in_target'] = [counted[i][1][0] for i in range(len(counted))]
                df_probes[f'{attr_name}_out_target'] = [counted[i][1][1] for i in range(len(counted))]
                df_probes[f'{attr_name}_ratio'] = [counted[i][1][0]/(counted[i][1][0] + counted[i][1][1]) for i in range(len(counted))]
                import shutil
                shutil.rmtree(tmp_dir)
            else:
                raise NotImplementedError(
                    f"Aligner {attr['aligner']} is not implemented."
                )

        if attr_type == "n_mapped_genes":
            if attr.get('aligner') == "bowtie2":
                assert 'bowtie2' in genome['align_index'] 
                fasta_path = Path(genome['fasta'])
                index_prefix = fasta_path.parent / 'bowtie2_genome' / fasta_path.stem
                tmp_dir = Path("tmp")
                tmp_dir.mkdir(exist_ok=True, parents=True)
                recname2seq = {f"{row['exon_name']}_{row['start']}": row['target_region'] for (_, row) in df_probes.iterrows()}
                n_mapped_genes = count_n_bowtie2_aligned_genes(tmp_dir, recname2seq, task_id, index_prefix, attr.get("min_mapq", 30), attr.get("threads", 10))
                n_mapped_genes = [n_mapped_genes[f"{row['exon_name']}_{row['start']}"] for _, row in df_probes.iterrows()]
                df_probes[attr_name] = n_mapped_genes
                import shutil
                shutil.rmtree(tmp_dir)
            else:
                raise NotImplementedError(
                    f"Aligner {attr['aligner']} is not implemented."
                )
        elif attr_type == "annealing_temperature":
            vals = df_probes[actual_target].apply(cal_temp).round(2)
            df_probes[attr_name] = vals
        elif attr_type == "gc_content":
            vals = df_probes[actual_target].apply(cal_gc_content).round(2)
            df_probes[attr_name] = vals
        elif attr_type == "fold_score":
            vals = df_probes[actual_target].apply(cal_target_fold_score).round(2)
            df_probes[attr_name] = vals
        elif attr_type == "self_match":
            vals = df_probes[actual_target].apply(cal_self_match).round(2)
            df_probes[attr_name] = vals
        elif attr_type == "blocks":
            if 'start' not in df_probes.columns:
                print(f"Warning: 'start' column not found for attribute '{attr_name}'")
                continue
            vals = df_probes.apply(lambda row: cal_target_blocks(row[actual_target], row['start']), axis=1)
            df_probes[attr_name] = vals
        else:
            raise NotImplementedError(
                f"Attribute type {attr_type} is not implemented."
            )
    return df_probes
