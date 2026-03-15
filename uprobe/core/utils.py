import sys
import logging
import os
from os.path import exists
import typing as t
from pyfaidx import Fasta
import shutil
import subprocess

def get_logger(name):
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stderr)
        LOGGING_FMT = "%(name)-20s %(levelname)-7s @ %(asctime)s: %(message)s"
        LOGGING_DATE_FMT = "%m/%d/%y %H:%M:%S"
        handler.setFormatter(logging.Formatter(fmt=LOGGING_FMT, datefmt=LOGGING_DATE_FMT))
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        log.propagate = False
    return log

def get_base_map():
    base_map = [b'\0' for i in range(256)]
    base_map[ ord('A') ] = b'T'
    base_map[ ord('T') ] = b'A'
    base_map[ ord('C') ] = b'G'
    base_map[ ord('G') ] = b'C'
    base_map[ ord('a') ] = b't'
    base_map[ ord('t') ] = b'a'
    base_map[ ord('c') ] = b'g'
    base_map[ ord('g') ] = b'c'
    base_map[ ord('N') ] = b'N'
    base_map[ ord('n') ] = b'n'
    base_map = bytes(b''.join(base_map))
    return base_map

BASEMAP = get_base_map()
def reverse_complement(seq):
    # Handle pandas Series by converting to string
    if hasattr(seq, 'iloc') and hasattr(seq, 'values'):  # Check if it's a pandas Series
        seq = str(seq.iloc[0]) if len(seq) > 0 else str(seq.values[0])
    elif hasattr(seq, '__iter__') and not isinstance(seq, str):
        # Handle other iterable types that might be passed
        seq = str(seq)
    
    res = seq[::-1]
    res = res.translate(BASEMAP)
    return res

def get_tmp_dir(basename):
    i = 0
    dirname = lambda: f"{basename}.{i}"
    while exists(dirname()):
        i += 1
    os.mkdir(dirname())
    return dirname()

def self_match(probe: str, min_match = 4):
    length = len(probe)
    probe_re = reverse_complement(probe)
    match_pairs = 0
    for i in range(0,length-min_match+1):
        tem = probe[i:min_match+i]
        for j in range(0,length-min_match+1):
            tem_re = probe_re[j:min_match+j]
            if tem == tem_re and i + j + min_match - 2 != length:
                match_pairs = match_pairs + 1
    return match_pairs

def write_fastq(outdir, gene, recname2seq: t.Mapping[str, str]):
    fq = f'{outdir}/{gene}.fq'
    with open(fq, 'w') as f:
        for recname, seq in recname2seq.items():
            f.write(f"@{recname}\n")
            f.write(seq+"\n")
            f.write("+\n")
            f.write("~"*len(seq)+"\n")
    return fq

def extract_fasta(fasta_path, target, 
                    min_length, overlap):
    fa = Fasta(str(fasta_path))
    chrom, region = target.split(':')
    start, end = region.split('-')
    seq = fa[chrom][int(start):int(end)].seq.upper()
    seq_list = []
    m = 1
    for i in range(0, len(seq) - min_length + 1,  min_length - overlap):
        tem = seq[i:i + min_length]
        if len(tem) == min_length: 
            sub_start = i + 1  
            sub_end = i + min_length
            sub_region = f"{sub_start}-{sub_end}"
            id = f"{target}_{m}"
            seq_list.append([id, target, sub_region, tem])
            m += 1
    return seq_list
    
def gene_barcode(config: dict) -> dict:
    """
    Generates a dictionary of gene names to anchor barcodes
    """
    gene_barcode_dict = {}
    for target in config['targets']:
        if target in config['encoding']:
            barcodes = config['encoding'][target]
            # Get all barcodes for this target
            barcode_values = []
            for barcode_key in barcodes:
                barcode_value = config['barcode_set'][barcodes[barcode_key]]
                barcode_values.append(barcode_value)
            gene_barcode_dict[target] = tuple(barcode_values)
    return gene_barcode_dict

def check_and_install_tools(tools_list: t.List[str]) -> None:
    """
    Check if tools are available in PATH. If not, try to install via conda.
    """
    missing_tools = []
    for tool in tools_list:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if not missing_tools:
        return

    log = get_logger(__name__)
    log.info(f"Missing tools: {', '.join(missing_tools)}. Attempting auto-installation via conda...")
    
    # Try installing all missing tools at once
    # Mapping tool names to package names if they differ
    # bowtie2 -> bowtie2
    # jellyfish -> jellyfish
    # blast -> blast
    # mmseqs -> mmseqs2
    package_map = {
        'mmseqs': 'mmseqs2'
    }
    
    packages = [package_map.get(tool, tool) for tool in missing_tools]
    
    cmd = ["conda", "install", "-y", "-c", "bioconda"] + packages
    
    try:
        # Check if conda is available
        if not shutil.which("conda"):
            raise EnvironmentError("Conda is not available in PATH. Cannot auto-install tools.")
            
        log.info(f"Running command: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        log.info("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to install tools via conda: {e}")
        log.error("Please install the following tools manually: " + ", ".join(missing_tools))
        sys.exit(1)
    except Exception as e:
        log.error(f"Error during tool installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fasta_path = "/data/zhangqian/genomes/hg38/hg38.fa"
    target = "NC_000017.11:40304334-40362489"
    seq_list = extract_fasta(fasta_path, target)
    for id, region, seq in seq_list:
        print(id, region, seq)