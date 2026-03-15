import csv
from pathlib import Path
from fastapi import HTTPException
import configparser

def load_barcodes_from_csv(file_path: Path) -> dict:
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CSV file not found")
    barcodes_dict = {}
    with file_path.open(mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2: 
                barcode, sequence = row
                barcodes_dict[barcode] = sequence
    return barcodes_dict

def yaml_to_genelist(yaml: dict) -> list:

    genelist = []
    for gene in yaml['targets']:
        gene_info = [gene]
        for barcode in yaml['encoding'][gene].values():
            barcode_seq = yaml['barcode_set'].get(barcode, '')
            gene_info.append(barcode_seq)
        genelist.append(gene_info)
    return genelist

def yaml_to_poollist(yaml: dict) -> list:

    poollist = []
    for pool in yaml['pool_list']:
        name = pool['name']
        location = pool['location']
        numbers = pool['numbers']
        density = ['density']
        poollist.append([name, location, numbers, density])
    return poollist

def yaml_to_txt(yaml: dict, out_txt: Path) -> Path:
    if out_txt is None:
        raise ValueError("The output path is None")
    print(f"Writing poollist to {out_txt}")
    pool_list = yaml.get('pool_list', [])
    with open(out_txt, 'w') as f:
        for pool in pool_list:
            line = f"{pool['name']};{pool['location']};{pool['numbers']};{pool['density']}\n"
            f.write(line)
    return out_txt

def genelist_to_txt(genelist: list, out_txt: Path) -> Path:
    if out_txt is None:
        raise ValueError("The output path is None")
    if not isinstance(genelist, list) or not genelist:
        raise ValueError("Genelist is empty or not a list")
    print(f"Writing genelist to {out_txt}")
    with open(out_txt, 'w') as f:
        anchor1 = ''
        anchor2 = ''
        for gene_base in genelist:
            if len(gene_base) == 4:
                anchor1 = gene_base[1]
                anchor2 = gene_base[2]
                f.write(f"{gene_base[0]}\t{anchor1}\t{anchor2}\t{gene_base[3]}\n")
            elif len(gene_base) == 3:
                anchor1 = gene_base[1]
                anchor2 = gene_base[2]
                f.write(f"{gene_base[0]}\t{anchor1}\t{anchor2}\n")
            elif len(gene_base) == 2:
                f.write(f"{gene_base[0]}\t{anchor1}\t{anchor2}\t{gene_base[1]}\n")
            elif len(gene_base) == 1:
                f.write(f"{gene_base[0]}\t{anchor1}\t{anchor2}\n")
    return out_txt
    
def update_ini_from_yaml(ini_file: str, yaml_content: dict, work_dir: str, samples_txt: str, fasta: str, index_prefix: str, jf: str) -> str:

    config = configparser.ConfigParser()
    config.read(ini_file)
    
    if yaml_content['probetype'] == 'DNA-FISH':

        probe_len = yaml_content['probes']['fish_probe']['length']
        overlap = yaml_content['probes']['fish_probe']['overlap']
        box_move = probe_len - overlap
        
        name = yaml_content.get('name')
        res_dir = f'{work_dir}/results_{name}'
        
        if 'GLOBAL' in config:
            config['GLOBAL']['working_dir'] = work_dir
            config['GLOBAL']['result_dir'] = res_dir
            config['GLOBAL']['path_samples'] = samples_txt
        
        if 'CANDIDATE' in config:
            config['CANDIDATE']['len_subseq'] = str(probe_len)
            config['CANDIDATE']['box_move'] = str(box_move)

        if 'EXTRACT_FA' in config:
            config['EXTRACT_FA']['refe_fasta'] = fasta

        if 'ALIGN' in config:
            config['ALIGN']['bw2-index'] = index_prefix

        if 'KMER' in config:
            config['KMER']['jf_file'] = jf

        output_ini_file = f'{work_dir}/config_probe_{name}.ini'
    
    with open(output_ini_file, 'w') as configfile:
        config.write(configfile)

    return output_ini_file
