Examples
========

This page provides complete, working examples for common probe design scenarios.

Example 1: Basic FISH Probes
-----------------------------

Design simple FISH probes for visualizing gene expression.

Configuration Files
~~~~~~~~~~~~~~~~~~~

**genomes.yaml:**

.. code-block:: yaml

   human_hg38:
     description: "Human genome GRCh38"
     species: "Homo sapiens"
     fasta: "/data/genomes/hg38/hg38.fa"
     gtf: "/data/genomes/hg38/gencode.v38.annotation.gtf"
     align_index:
       - bowtie2
       - blast

**fish_protocol.yaml:**

.. code-block:: yaml

   name: "Basic_FISH_Probes"
   genome: "human_hg38"
   
   targets:
     - "GAPDH"
     - "ACTB"
     - "TP53"
   
   extracts:
     target_region:
       source: "exon"
       length: 100
       overlap: 20
   
   probes:
     fish_probe:
       template: "{spacer}{target_binding}{fluorophore_site}"
       parts:
         spacer:
           expr: "'TTTTTT'"
         target_binding:
           length: 25
           expr: "rc(target_region[0:25])"
         fluorophore_site:
           expr: "encoding[gene_name]['fluorophore']"
   
   encoding:
     GAPDH:
       fluorophore: "ACGTACGTACGTACGT"
     ACTB:
       fluorophore: "TGCATGCATGCATGCA"
     TP53:
       fluorophore: "CGATCGATCGATCGAT"
   
   attributes:
     gc_content:
       target: fish_probe
       type: gc_content
     melting_temp:
       target: fish_probe
       type: annealing_temperature
   
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.45 & gc_content <= 0.55"
       melting_temp:
         condition: "melting_temp >= 50 & melting_temp <= 60"

Running the Example
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Complete workflow
   uprobe run -p fish_protocol.yaml -g genomes.yaml -o fish_results/ --raw

   # Step by step
   uprobe validate-targets -p fish_protocol.yaml -g genomes.yaml
   uprobe generate-targets -p fish_protocol.yaml -g genomes.yaml -o fish_results/
   uprobe construct-probes -p fish_protocol.yaml -g genomes.yaml \
     --targets fish_results/target_sequences.csv -o fish_results/
   uprobe post-process -p fish_protocol.yaml -g genomes.yaml \
     --probes fish_results/constructed_probes.csv -o fish_results/ --raw

Expected Output
~~~~~~~~~~~~~~~

The results directory will contain:

- ``Basic_FISH_Probes_YYYYMMDD_HHMMSS.csv`` - Filtered probes
- ``Basic_FISH_Probes_YYYYMMDD_HHMMSS_raw.csv`` - All designed probes

Example output structure:

.. code-block:: text

   gene_name,target_region,fish_probe,gc_content,melting_temp
   GAPDH,ATGCGTACG...,TTTTTTCGTACGATACGTACGTACGTACGT,0.48,55.2
   ACTB,CGATCGATA...,TTTTTTTATCGATCTGCATGCATGCATGCA,0.52,58.7
   TP53,GCTAGCTAG...,TTTTTTCTAGCTACCGATCGATCGATCGAT,0.50,56.1

Example 2: PCR Primer Design
-----------------------------

Design primer pairs for PCR amplification of target regions.

**pcr_protocol.yaml:**

.. code-block:: yaml

   name: "PCR_Primer_Design"
   genome: "human_hg38"
   
   targets:
     - "BRCA1"
     - "BRCA2"
     - "ATM"
   
   extracts:
     target_region:
       source: "exon"
       length: 300  # Larger regions for primer placement
       overlap: 0   # Non-overlapping amplicons
   
   probes:
     forward_primer:
       template: "{primer_seq}"
       parts:
         primer_seq:
           length: 22
           expr: "target_region[0:22]"
     
     reverse_primer:
       template: "{primer_seq}"
       parts:
         primer_seq:
           length: 22
           expr: "rc(target_region[-22:])"
     
     amplicon:
       template: "{full_region}"
       parts:
         full_region:
           expr: "target_region"
   
   attributes:
     # Forward primer properties
     fwd_gc:
       target: forward_primer
       type: gc_content
     fwd_tm:
       target: forward_primer
       type: annealing_temperature
     fwd_hairpin:
       target: forward_primer
       type: fold_score
     
     # Reverse primer properties
     rev_gc:
       target: reverse_primer
       type: gc_content
     rev_tm:
       target: reverse_primer
       type: annealing_temperature
     rev_hairpin:
       target: reverse_primer
       type: fold_score
     
     # Amplicon properties
     amplicon_length:
       target: amplicon
       type: length
     amplicon_gc:
       target: amplicon
       type: gc_content
   
   post_process:
     filters:
       # Primer GC content
       fwd_gc:
         condition: "fwd_gc >= 0.4 & fwd_gc <= 0.6"
       rev_gc:
         condition: "rev_gc >= 0.4 & rev_gc <= 0.6"
       
       # Similar melting temperatures
       tm_similarity:
         condition: "abs(fwd_tm - rev_tm) <= 5"
       
       # Temperature range
       fwd_tm:
         condition: "fwd_tm >= 55 & fwd_tm <= 65"
       rev_tm:
         condition: "rev_tm >= 55 & rev_tm <= 65"
       
       # Minimal secondary structure
       fwd_hairpin:
         condition: "fwd_hairpin < 0.3"
       rev_hairpin:
         condition: "rev_hairpin < 0.3"
       
       # Amplicon size
       amplicon_length:
         condition: "amplicon_length >= 100 & amplicon_length <= 500"

Example 3: Multiplexed Probe Design
------------------------------------

Design probes with unique barcodes for multiplexed detection.

**multiplex_protocol.yaml:**

.. code-block:: yaml

   name: "Multiplexed_Detection"
   genome: "human_hg38"
   
   targets:
     - "CD4"
     - "CD8A"
     - "CD19"
     - "CD56"
     - "CD3E"
   
   extracts:
     target_region:
       source: "exon"
       length: 80
       overlap: 15
   
   probes:
     detection_probe:
       template: "{target_binding}{spacer}{barcode_region}"
       parts:
         target_binding:
           length: 25
           expr: "rc(target_region[10:35])"
         spacer:
           expr: "'AAAAAA'"
         barcode_region:
           template: "{bc1}{linker}{bc2}"
           parts:
             bc1:
               expr: "encoding[gene_name]['BC1']"
             linker:
               expr: "'GGG'"
             bc2:
               expr: "encoding[gene_name]['BC2']"
   
   encoding:
     CD4:
       BC1: "ACGTACGTACGT"
       BC2: "TGCATGCATGCA"
     CD8A:
       BC1: "CGATCGATCGAT"
       BC2: "ATCGATCGATCG"
     CD19:
       BC1: "GCTAGCTAGCTA"
       BC2: "CTAGCTAGCTAG"
     CD56:
       BC1: "TACGTACGTACG"
       BC2: "CATGCATGCATG"
     CD3E:
       BC1: "GATCGATCGATC"
       BC2: "TCGATCGATCGA"
   
   attributes:
     probe_gc:
       target: detection_probe
       type: gc_content
     probe_tm:
       target: detection_probe
       type: annealing_temperature
     target_specificity:
       target: target_binding
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
     barcode_uniqueness:
       target: barcode_region
       type: self_match
   
   post_process:
     filters:
       probe_gc:
         condition: "probe_gc >= 0.4 & probe_gc <= 0.6"
       probe_tm:
         condition: "probe_tm >= 52 & probe_tm <= 62"
       target_specificity:
         condition: "target_specificity <= 3"
       barcode_uniqueness:
         condition: "barcode_uniqueness < 0.5"
     
     sorts:
       is_ascending:
         - "target_specificity"
       is_descending:
         - "probe_tm"

Example 4: Advanced Filtering
------------------------------

Comprehensive quality control with multiple filtering criteria.

**advanced_protocol.yaml:**

.. code-block:: yaml

   name: "Advanced_Quality_Control"
   genome: "human_hg38"
   
   targets:
     - "EGFR"
     - "KRAS"
     - "PIK3CA"
     - "AKT1"
   
   extracts:
     target_region:
       source: "exon"
       length: 120
       overlap: 30
   
   probes:
     main_probe:
       template: "{binding_region}"
       parts:
         binding_region:
           length: 40
           expr: "target_region[40:80]"
   
   attributes:
     # Basic properties
     gc_content:
       target: main_probe
       type: gc_content
     melting_temp:
       target: main_probe
       type: annealing_temperature
     
     # Specificity analysis
     off_targets_bowtie:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
     off_targets_blast:
       target: main_probe
       type: n_mapped_genes
       aligner: blast
       e_value: 0.001
     
     # Secondary structure
     self_complementarity:
       target: main_probe
       type: self_match
     folding_energy:
       target: main_probe
       type: fold_score
     
     # Sequence complexity
     repetitive_kmers:
       target: main_probe
       type: kmer_count
       kmer_length: 10
       kmer_threshold: 100
       kmer_file: "genome.jf"
     
     # Target region properties
     target_gc:
       target: target_region
       type: gc_content
     target_complexity:
       target: target_region
       type: complexity_score
   
   post_process:
     filters:
       # Primary filters
       gc_content:
         condition: "gc_content >= 0.45 & gc_content <= 0.55"
       melting_temp:
         condition: "melting_temp >= 55 & melting_temp <= 65"
       
       # Specificity filters
       off_targets_bowtie:
         condition: "off_targets_bowtie <= 5"
       off_targets_blast:
         condition: "off_targets_blast <= 10"
       
       # Structure filters
       self_complementarity:
         condition: "self_complementarity < 0.7"
       folding_energy:
         condition: "folding_energy < 0.4"
       
       # Complexity filters
       repetitive_kmers:
         condition: "repetitive_kmers <= 3"
       target_complexity:
         condition: "target_complexity > 0.3"
     
     sorts:
       is_ascending:
         - "off_targets_bowtie"
         - "self_complementarity"
         - "folding_energy"
       is_descending:
         - "melting_temp"
         - "target_complexity"
     
     remove_overlap:
       location_interval: 25

Python API Examples
-------------------

Example 5: Programmatic Probe Design
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from uprobe import UProbeAPI
   import pandas as pd
   import matplotlib.pyplot as plt

   # Configuration
   protocol_config = {
       'name': 'Programmatic_Design',
       'genome': 'human_hg38',
       'targets': ['GAPDH', 'ACTB', 'TP53'],
       'extracts': {
           'target_region': {
               'source': 'exon',
               'length': 100,
               'overlap': 20
           }
       },
       'probes': {
           'main_probe': {
               'template': '{binding_region}',
               'parts': {
                   'binding_region': {
                       'length': 30,
                       'expr': 'rc(target_region[0:30])'
                   }
               }
           }
       },
       'attributes': {
           'gc_content': {'target': 'main_probe', 'type': 'gc_content'},
           'melting_temp': {'target': 'main_probe', 'type': 'annealing_temperature'}
       },
       'post_process': {
           'filters': {
               'gc_content': {'condition': 'gc_content >= 0.4 & gc_content <= 0.6'},
               'melting_temp': {'condition': 'melting_temp >= 50 & melting_temp <= 65'}
           }
       }
   }

   # Run design
   uprobe = UProbeAPI(
       protocol_config=protocol_config,
       genomes_config=Path('genomes.yaml'),
       output_dir=Path('results')
   )

   results = uprobe.run_workflow(raw_csv=True)

   # Analysis and visualization
   print(f"Generated {len(results)} probes")
   print(results[['gene_name', 'gc_content', 'melting_temp']].describe())

   # Plot results
   fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

   # GC content distribution
   ax1.hist(results['gc_content'], bins=20, alpha=0.7)
   ax1.set_xlabel('GC Content')
   ax1.set_ylabel('Frequency')
   ax1.set_title('GC Content Distribution')

   # Melting temperature vs GC content
   ax2.scatter(results['gc_content'], results['melting_temp'], alpha=0.6)
   ax2.set_xlabel('GC Content')
   ax2.set_ylabel('Melting Temperature (°C)')
   ax2.set_title('Tm vs GC Content')

   plt.tight_layout()
   plt.savefig('probe_analysis.png', dpi=300, bbox_inches='tight')
   plt.show()

Example 6: Batch Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from pathlib import Path
   from uprobe import UProbeAPI

   def process_gene_list(gene_file, output_prefix):
       """Process a list of genes from a file."""
       
       # Read genes from file
       with open(gene_file, 'r') as f:
           genes = [line.strip() for line in f if line.strip()]
       
       # Create protocol
       protocol = {
           'name': f'{output_prefix}_batch',
           'genome': 'human_hg38',
           'targets': genes,
           'extracts': {
               'target_region': {
                   'source': 'exon',
                   'length': 100,
                   'overlap': 20
               }
           },
           'probes': {
               'probe': {
                   'template': '{seq}',
                   'parts': {
                       'seq': {
                           'length': 25,
                           'expr': 'rc(target_region[0:25])'
                       }
                   }
               }
           },
           'attributes': {
               'gc': {'target': 'probe', 'type': 'gc_content'},
               'tm': {'target': 'probe', 'type': 'annealing_temperature'}
           },
           'post_process': {
               'filters': {
                   'gc': {'condition': 'gc >= 0.4 & gc <= 0.6'},
                   'tm': {'condition': 'tm >= 50 & tm <= 65'}
               }
           }
       }
       
       # Process
       uprobe = UProbeAPI(
           protocol_config=protocol,
           genomes_config=Path('genomes.yaml'),
           output_dir=Path(f'batch_results/{output_prefix}')
       )
       
       return uprobe.run_workflow(raw_csv=True)

   # Process multiple gene lists
   gene_lists = ['oncogenes.txt', 'tumor_suppressors.txt', 'kinases.txt']
   
   all_results = {}
   for gene_list in gene_lists:
       if os.path.exists(gene_list):
           prefix = gene_list.replace('.txt', '')
           print(f"Processing {gene_list}...")
           results = process_gene_list(gene_list, prefix)
           all_results[prefix] = results
           print(f"Generated {len(results)} probes for {prefix}")

   # Summary
   total_probes = sum(len(df) for df in all_results.values())
   print(f"\nTotal probes generated: {total_probes}")

Running the Examples
--------------------

Command Line Execution
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Download example files (if available)
   wget https://github.com/UFISH-Team/U-Probe/tree/main/examples/

   # Run basic FISH example
   cd examples/basic_fish/
   uprobe run -p fish_protocol.yaml -g genomes.yaml -o results/ --raw

   # Run PCR primer example
   cd ../pcr_primers/
   uprobe run -p pcr_protocol.yaml -g genomes.yaml -o results/ --verbose

   # Run multiplexed example
   cd ../multiplexed/
   uprobe run -p multiplex_protocol.yaml -g genomes.yaml -o results/

Python Script Execution
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run programmatic example
   python programmatic_design.py

   # Run batch processing example
   python batch_processing.py

Customizing Examples
--------------------

Modify Target Lists
~~~~~~~~~~~~~~~~~~~

Change the target genes in any protocol:

.. code-block:: yaml

   targets:
     - "YOUR_GENE1"
     - "YOUR_GENE2"
     - "YOUR_GENE3"

Adjust Quality Filters
~~~~~~~~~~~~~~~~~~~~~~

Make filters more or less stringent:

.. code-block:: yaml

   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.3 & gc_content <= 0.7"  # More relaxed
       melting_temp:
         condition: "melting_temp >= 60 & melting_temp <= 65"  # More stringent

Add Custom Attributes
~~~~~~~~~~~~~~~~~~~~~

Include additional quality metrics:

.. code-block:: yaml

   attributes:
     probe_length:
       target: main_probe
       type: length
     target_mappings:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2

Troubleshooting Examples
------------------------

If examples don't work:

1. **Check file paths** in genomes.yaml
2. **Verify gene names** exist in your GTF file  
3. **Install required dependencies** (bowtie2, blast)
4. **Use smaller target lists** for testing
5. **Check the** :doc:`troubleshooting` **guide**

For more help:

- Check :doc:`troubleshooting` for common issues
- Review :doc:`configuration` for detailed options
- Ask questions on `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_
