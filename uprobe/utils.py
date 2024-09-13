import sys
import logging
import os
from os.path import exists

def get_logger(name):
    log = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stderr)
    LOGGING_FMT = "%(name)-20s %(levelname)-7s @ %(asctime)s: %(message)s"
    LOGGING_DATE_FMT = "%m/%d/%y %H:%M:%S"
    handler.setFormatter(logging.Formatter(fmt=LOGGING_FMT, datefmt=LOGGING_DATE_FMT))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
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