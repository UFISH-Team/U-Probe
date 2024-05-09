import pandas as pd
from uprobe.utils import reverse_complement

# target_region: the target mRNA region of the probe
# target_part1: the 5' part of the target_region
# target_part2: the middle part of the target_region
# target_part3: the 3' part of the target_region

# circle probe: part1+part2+part3
def circle_part1(
        target_part1: str
        )-> str:
    tem1_re = reverse_complement(target_part1)
    return tem1_re

def circle_part2(
        barcode1: str = '',
        barcode2: str = ''
        )-> str:
    if barcode2 is not None:
        part2 = barcode1 + "A" + barcode2
    else:
        part2 = barcode1
    return part2
       
def circle_part3(
        target_part2: str
                )-> str:
    tem2_re = reverse_complement(target_part2)
    return tem2_re

def circle_probe(
        target_part1: str,
        target_part2: str,
        barcode1: str = '',
        barcode2: str = ''
        ) -> str:
    part1 = circle_part1(target_part1)
    part2 = circle_part2(barcode1, barcode2)
    part3 = circle_part3(target_part2)
    return part1 + part2 + part3


# amp probe: part1+part2
# 5'->3'
def amp_part1(
        target_part3: str
        )-> str:
    target_part3_re = reverse_complement(target_part3)
    return target_part3_re

def amp_part2(
        target_region: str,
        target_part1: str,
        target_part2: str,
        barcode1: str = '',
        barcode2: str = ''
        ) -> str:
    circle_part2_seq = circle_part2(barcode1, barcode2)
    circle_part2_re = reverse_complement(circle_part2_seq[(len(circle_part2_seq) // 2):])
    part2 = target_region[len(target_part1) + len(target_part2)] + circle_part2_re
    return part2
    
def amp_probe(target_region: str,
              target_part1: str,
              target_part2: str,
              target_part3: str,
              barcode2:str
              ) -> str:
    part1 = amp_part1(target_part3)
    part2 = amp_part2(target_region, target_part1, target_part2, barcode2)
    return part1 + part2

import random
def construct_probes(config, target_seqs):
    probes = []        
    barcode1 = 'AAACCCTTGGCC'
    barcode2 = 'GGGGAAAATTTC'
    for i, target_region in enumerate(target_seqs):
        len1 = config['probes']['circle_probe']['parts']['part1']['length']
        len3 = config['probes']['circle_probe']['parts']['part3']['length']
        target_part1 = target_region[:len1]
        target_part2 = target_region[len1:len1+len3]
        
        circle_probe_seq = circle_probe(target_part1, target_part2, barcode1, barcode2)
        target_part3 = target_region[len1+len3+1:]
        amp_probe_seq = amp_probe(target_region, target_part1, target_part2, target_part3, barcode2)
    
        probe = {
            'circle_probe': circle_probe_seq,
            'circle_probe:part1': circle_part1(target_part1),
            'circle_probe:part2': circle_part2(barcode1, barcode2),
            'circle_probe:part2:barcode1': barcode1,
            'circle_probe:part2:barcode2': barcode2,
            'circle_probe:part3': circle_part3(target_part2),
            'amp_probe': amp_probe_seq,
            'amp_probe:part1': amp_part1(target_part3),
            'amp_probe:part2': amp_part2(target_region, target_part1, target_part2, barcode1, barcode2)
        }
        probes.append(probe)
    return pd.DataFrame(probes)