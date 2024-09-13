

def generate_gene_dict(config: dict) -> dict:
    gene_dict = {}
    for target in config['targets']:
        if target in config['encoding']:
            barcodes = config['encoding'][target]
            anchor1 = config['barcode_set'][barcodes['barcode1']]
            anchor2 = config['barcode_set'][barcodes['barcode2']]
            gene_dict[target] = (anchor1, anchor2)  # 使用元组存储条形码
    return gene_dict
