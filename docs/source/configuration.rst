Configuration Files
===================

U-Probe uses two main YAML configuration files to define your probe design workflow. This guide explains the structure and options for both configuration files.

Overview
--------

U-Probe requires two configuration files:

1. **genomes.yaml** - Defines genome resources and paths
2. **protocol.yaml** - Defines probe design parameters and workflow

These files use YAML format, which is human-readable and easy to edit. YAML is sensitive to indentation, so use consistent spacing (preferably 2 spaces per level).

Genomes Configuration (genomes.yaml)
------------------------------------

The genomes configuration file maps genome names to their file paths and indexing options.

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: yaml

   genome_name:
     description: "Human readable description"
     species: "Species name"
     fasta: "/path/to/genome.fa"
     gtf: "/path/to/annotation.gtf"
     align_index:
       - bowtie2
       - blast
     jellyfish: false

Required Fields
~~~~~~~~~~~~~~~

**fasta** (*string*)
  Path to the genome FASTA file. This file contains the reference genome sequences.

  .. code-block:: yaml

     fasta: "/data/genomes/hg38/hg38.fa"

**gtf** (*string*)
  Path to the gene annotation GTF file. Used for extracting gene coordinates and validating targets.

  .. code-block:: yaml

     gtf: "/data/genomes/hg38/gencode.v38.annotation.gtf"

**align_index** (*list*)
  List of aligners for which to build indices. Supported options:
  
  - ``bowtie2`` - For fast sequence alignment
  - ``blast`` - For sequence similarity searches

  .. code-block:: yaml

     align_index:
       - bowtie2
       - blast

Optional Fields
~~~~~~~~~~~~~~~

**description** (*string*)
  Human-readable description of the genome.

  .. code-block:: yaml

     description: "Human genome build 38 (GRCh38)"

**species** (*string*)
  Scientific species name.

  .. code-block:: yaml

     species: "Homo sapiens"

**out** (*string*)
  Output directory for genome indices. Defaults to the same directory as FASTA file.

  .. code-block:: yaml

     out: "/data/genomes/hg38/indices"

**jellyfish** (*boolean*)
  Whether to build Jellyfish k-mer index. Used for k-mer counting attributes. Default: false.

  .. code-block:: yaml

     jellyfish: true

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # genomes.yaml
   human_hg38:
     description: "Human genome build 38"
     species: "Homo sapiens"
     fasta: "/data/genomes/hg38/hg38.fa"
     gtf: "/data/genomes/hg38/gencode.v38.annotation.gtf"
     out: "/data/genomes/hg38/indices"
     align_index:
       - bowtie2
       - blast
     jellyfish: true

   mouse_mm39:
     description: "Mouse genome build 39"
     species: "Mus musculus"
     fasta: "/data/genomes/mm39/mm39.fa"
     gtf: "/data/genomes/mm39/gencode.vM27.annotation.gtf"
     align_index:
       - bowtie2
     jellyfish: false

Protocol Configuration (protocol.yaml)
---------------------------------------

The protocol file defines the complete probe design workflow, from target selection to final filtering.

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: "ExperimentName"
   genome: "genome_name"
   targets: [...]
   extracts: {...}
   probes: {...}
   encoding: {...}
   attributes: {...}
   post_process: {...}

Core Sections
~~~~~~~~~~~~~

**name** (*string*)
  Unique name for your experiment. Used in output filenames.

  .. code-block:: yaml

     name: "FISH_Probes_v1"

**genome** (*string*)
  Name of the genome to use (must match a key in genomes.yaml).

  .. code-block:: yaml

     genome: "human_hg38"

**targets** (*list*)
  List of target gene names or identifiers. These must exist in your GTF file.

  .. code-block:: yaml

     targets:
       - "GAPDH"
       - "ACTB"
       - "TP53"
       - "ENSG00000141510"  # Gene IDs also supported

Target Extraction (extracts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines how to extract target sequences from the genome.

.. code-block:: yaml

   extracts:
     target_region:
       source: "exon"        # Where to extract from
       length: 120           # Length of each extract
       overlap: 10           # Overlap between adjacent extracts

**source** options:

- ``exon`` - Extract from exonic regions
- ``gene`` - Extract from entire gene regions
- ``genome`` - Extract from specified coordinates

**length** (*integer*)
  Length of each target region in base pairs.

**overlap** (*integer*)
  Overlap between adjacent extracts in base pairs.

Advanced Extraction
~~~~~~~~~~~~~~~~~~~

For custom genomic coordinates:

.. code-block:: yaml

   extracts:
     target_region:
       source: "genome"
       length: 200
       coordinates:
         - "chr1:1000000-1002000"
         - "chr2:500000-501000"
         - "chrX:10000000-10001000"

For gene-specific parameters:

.. code-block:: yaml

   extracts:
     target_region:
       source: "exon"
       length: 120
       overlap: 20
       gene_specific:
         GAPDH:
           length: 150
           overlap: 30
         TP53:
           source: "gene"  # Extract from entire gene for this target

Probe Design (probes)
~~~~~~~~~~~~~~~~~~~~~

The core of probe design - defines probe structure and composition.

Basic Probe Structure
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   probes:
     probe_1:
       template: "{part1}{part2}{part3}"
       parts:
         part1:
           length: 15
           expr: "target_region[0:15]"
         part2:
           length: 10
           expr: "encoding[gene_name]['barcode']"
         part3:
           length: 15
           expr: "rc(target_region[15:30])"

**template** (*string*)
  Defines the overall structure using part names in braces.

**parts** (*dict*)
  Defines each part of the probe.

Part Expressions
~~~~~~~~~~~~~~~~

Parts can use various expressions:

**Direct sequence slicing:**

.. code-block:: yaml

   part1:
     length: 20
     expr: "target_region[0:20]"  # First 20 bases

**Reverse complement:**

.. code-block:: yaml

   part2:
     length: 25
     expr: "rc(target_region[10:35])"  # Reverse complement

**Fixed sequences:**

.. code-block:: yaml

   primer:
     expr: "'ACGTACGTACGT'"  # Fixed sequence (note quotes)

**Barcode lookup:**

.. code-block:: yaml

   barcode:
     expr: "encoding[gene_name]['BC1']"

**Random sequences:**

.. code-block:: yaml

   spacer:
     length: 8
     expr: "random_seq(8)"

**Reference other probes:**

.. code-block:: yaml

   probe_2:
     template: "{part1}"
     parts:
       part1:
         expr: "probe_1[0:15]"  # First 15 bases of probe_1

Nested Templates
~~~~~~~~~~~~~~~~

For complex probe structures:

.. code-block:: yaml

   probes:
     main_probe:
       template: "{binding_region}{barcode_region}"
       parts:
         binding_region:
           template: "{primer}{target}"
           parts:
             primer:
               expr: "'ACGTACGT'"
             target:
               length: 25
               expr: "rc(target_region[0:25])"
         barcode_region:
           template: "TT{barcode}AA"
           parts:
             barcode:
               expr: "encoding[gene_name]['BC1']"

Encoding System (encoding)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Maps genes to barcodes or other identifiers.

.. code-block:: yaml

   encoding:
     GAPDH:
       BC1: "ACGTACGTACGTACG"
       BC2: "TGCATGCATGCATGC"
       fluorophore: "AAAATTTTCCCCGGGG"
     ACTB:
       BC1: "CGATCGATCGATCGA"
       BC2: "ATCGATCGATCGATC"
       fluorophore: "TTTTAAAACCCCGGGG"
     TP53:
       BC1: "GCTAGCTAGCTAGCT"
       BC2: "CTAGCTAGCTAGCTA"
       fluorophore: "CCCCGGGGAAAATTTT"

Quality Attributes (attributes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines quality metrics to calculate for probes.

.. code-block:: yaml

   attributes:
     # GC content of the main probe
     probe_gc:
       target: main_probe
       type: gc_content
     
     # Melting temperature
     probe_tm:
       target: main_probe
       type: annealing_temperature
     
     # Self-complementarity
     probe_selfmatch:
       target: main_probe
       type: self_match
     
     # Secondary structure propensity
     probe_folding:
       target: main_probe
       type: fold_score
     
     # Off-target mapping
     probe_offtargets:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
     
     # K-mer abundance
     probe_kmers:
       target: main_probe
       type: kmer_count
       kmer_length: 10
       kmer_threshold: 100
       kmer_file: "genome.jf"

Attribute Types
~~~~~~~~~~~~~~~

**gc_content**
  GC content (0.0 to 1.0)

**annealing_temperature**
  Melting temperature in Celsius

**self_match**
  Self-complementarity score

**fold_score**
  Secondary structure folding propensity

**n_mapped_genes**
  Number of genes with significant alignment

  Options:
  - ``aligner``: bowtie2 or blast
  - ``min_mapq``: Minimum mapping quality

**kmer_count**
  K-mer abundance in genome

  Options:
  - ``kmer_length``: Length of k-mers
  - ``kmer_threshold``: Abundance threshold
  - ``kmer_file``: Jellyfish database file

Post-Processing (post_process)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines filtering and sorting criteria.

.. code-block:: yaml

   post_process:
     filters:
       probe_gc:
         condition: "probe_gc >= 0.4 & probe_gc <= 0.6"
       probe_tm:
         condition: "probe_tm >= 50 & probe_tm <= 65"
       probe_offtargets:
         condition: "probe_offtargets <= 5"
     
     sorts:
       is_ascending:
         - "probe_tm"
       is_descending:
         - "probe_gc"
         - "probe_selfmatch"
     
     remove_overlap:
       location_interval: 10

Filter Conditions
~~~~~~~~~~~~~~~~~

Use pandas-style boolean expressions:

.. code-block:: yaml

   filters:
     # Range filters
     gc_range:
       condition: "gc_content >= 0.4 & gc_content <= 0.6"
     
     # Threshold filters
     temp_min:
       condition: "melting_temp >= 55"
     
     # Complex conditions
     quality_filter:
       condition: "(gc_content >= 0.45 & melting_temp >= 50) | self_match < 0.8"

Sorting Options
~~~~~~~~~~~~~~~

.. code-block:: yaml

   sorts:
     is_ascending:    # Sort ascending (low to high)
       - "melting_temp"
       - "gc_content"
     is_descending:   # Sort descending (high to low)
       - "self_match"
       - "fold_score"

Overlap Removal
~~~~~~~~~~~~~~~

Remove probes that are too close to each other:

.. code-block:: yaml

   remove_overlap:
     location_interval: 15  # Minimum distance in base pairs

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # protocol.yaml - Complete FISH probe design
   name: "FISH_Experiment_2024"
   genome: "human_hg38"
   
   targets:
     - "GAPDH"
     - "ACTB" 
     - "TP53"
     - "MYC"
   
   extracts:
     target_region:
       source: "exon"
       length: 120
       overlap: 20
   
   probes:
     fish_probe:
       template: "{spacer}{binding}{barcode}{spacer2}"
       parts:
         spacer:
           expr: "'TTTTTT'"
         binding:
           length: 30
           expr: "rc(target_region[0:30])"
         barcode:
           expr: "encoding[gene_name]['fluorophore']"
         spacer2:
           expr: "'AAAAAA'"
   
   encoding:
     GAPDH:
       fluorophore: "ACGTACGTACGTACGTACGT"
     ACTB:
       fluorophore: "TGCATGCATGCATGCATGCA"
     TP53:
       fluorophore: "CGATCGATCGATCGATCGAT"
     MYC:
       fluorophore: "ATCGATCGATCGATCGATCG"
   
   attributes:
     gc_content:
       target: fish_probe
       type: gc_content
     melting_temp:
       target: fish_probe
       type: annealing_temperature
     self_complementarity:
       target: fish_probe
       type: self_match
     off_targets:
       target: fish_probe
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
   
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.45 & gc_content <= 0.55"
       melting_temp:
         condition: "melting_temp >= 55 & melting_temp <= 65"
       self_complementarity:
         condition: "self_complementarity < 0.7"
       off_targets:
         condition: "off_targets <= 3"
     
     sorts:
       is_ascending:
         - "melting_temp"
       is_descending:
         - "gc_content"
     
     remove_overlap:
       location_interval: 15

Best Practices
--------------

File Organization
~~~~~~~~~~~~~~~~~

Keep configuration files organized:

.. code-block:: text

   project/
   ├── config/
   │   ├── genomes.yaml
   │   ├── fish_protocol.yaml
   │   ├── pcr_protocol.yaml
   │   └── sequencing_protocol.yaml
   ├── data/
   └── results/

Version Control
~~~~~~~~~~~~~~~

Track configuration changes:

.. code-block:: yaml

   # Add version info to protocols
   name: "FISH_v2.1"
   version: "2.1"
   date: "2024-01-15"
   description: "Updated probe design with stricter filters"

Validation
~~~~~~~~~~

Always validate configurations before large runs:

.. code-block:: bash

   # Test with a small subset
   uprobe validate-targets -p protocol.yaml -g genomes.yaml

Documentation
~~~~~~~~~~~~~

Document your design choices:

.. code-block:: yaml

   # protocol.yaml
   name: "FISH_Neuronal_Genes"
   
   # Design rationale:
   # - 30bp binding region for high specificity
   # - 6bp poly-T spacer to reduce steric hindrance
   # - Strict GC content for uniform hybridization
   # - Temperature range optimized for 37°C incubation
   
   probes:
     fish_probe:
       template: "{binding_region}TTTTTT{fluorophore_binding}"
       # ... rest of configuration

Next Steps
----------

Now that you understand configuration files:

1. Try the examples in :doc:`examples`
2. Learn about the :doc:`cli` for running your configurations  
3. Explore advanced :doc:`workflows`
4. Check the complete :doc:`config_reference` for all options

.. tip::
   Start with simple configurations and gradually add complexity. Use the ``--raw`` flag to inspect intermediate results and understand how your configuration affects the output.
