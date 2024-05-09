import secrets
from pathlib import Path
import pandas as pd
from ._attributes import (
    count_n_bowtie2_aligned_genes,
    cal_temp, cal_gc_content,
    cal_target_fold_score,
    cal_self_match
)


def add_attributes(
        df_probes: pd.DataFrame,
        protocol: dict,
        genome: dict,
        workdir: Path
        ) -> pd.DataFrame:
    attributes: dict = protocol['attributes']
    # random str
    task_id = secrets.token_hex(6)
    attr: dict
    for attr_name, attr in attributes.items():
        target = attr['target']
        target_seqs = df_probes[target]
        seqnames = df_probes['id']
        recname2seq = dict(zip(seqnames, target_seqs))
        attr_type: str = attr['type']
        if attr_type == "n_mapped_genes":
            # TODO
            continue
            if attr['aligner'] == "bowtie2":
                assert genome['bowtie2_index'] is not None
                vals = count_n_bowtie2_aligned_genes(
                    str(workdir), recname2seq, task_id,
                    genome['bowtie2_index'],
                    attr.get("threads", 10),
                )
            else:
                raise NotImplementedError(
                    f"Aligner {attr['aligner']} is not implemented."
                )
        elif attr_type.lower() == "annealing_temperature":
            vals = [cal_temp(seq) for seq in target_seqs]
        elif attr_type.lower() == "gc_content":
            vals = [cal_gc_content(seq) for seq in target_seqs]
        elif attr_type.lower() == "fold_score":
            vals = [cal_target_fold_score(seq) for seq in target_seqs]
        elif attr_type.lower() == "self_match":
            vals = [cal_self_match(seq) for seq in target_seqs]
        else:
            raise NotImplementedError(
                f"Attribute type {attr_type} is not implemented."
            )
        df_probes[attr_name] = vals
    return df_probes
