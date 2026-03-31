===================
Configuration Files
===================

U-Probe is driven by two primary YAML configuration files: ``genomes.yaml`` and ``protocol.yaml``. This design separates reference data from experimental parameters, ensuring high reproducibility and reusability.

Genomes Configuration (genomes.yaml)
------------------------------------

The ``genomes.yaml`` file maps a reference genome identifier to its corresponding file paths and indexing requirements.

.. code-block:: yaml

   GRCh38:
     fasta: "/path/to/GRCh38.fasta"
     gtf: "/path/to/GRCh38.gtf"
     align_index:
       - bowtie2
       - blast
     jellyfish: false

* **fasta**: Absolute or relative path to the reference genome FASTA file.
* **gtf**: Path to the gene annotation GTF file.
* **align_index**: List of aligners (``bowtie2``, ``blast``) for which U-Probe should automatically build indices.
* **jellyfish**: Boolean flag to build a k-mer database for fast specificity screening.

Protocol Configuration (protocol.yaml)
--------------------------------------

The ``protocol.yaml`` file is the core of your probe design. It defines target genes, sequence extraction rules, the Directed Acyclic Graph (DAG) structure of the probes, and the filtering logic.

1. Basic Metadata & Targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: my_rna_probe_design
   genome: GRCh38
   targets:
     - GAPDH
     - ACTB

2. Sequence Extraction (extracts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define how target sequences are extracted from the reference genome.

.. code-block:: yaml

   extracts:
     target_region:
       source: exon  # Options: genome, exon, CDS, UTR
       length: 30
       overlap: 15

3. DAG-Based Probe Construction (probes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe utilizes a Directed Acyclic Graph (DAG) architecture, allowing complex, modular probe construction where parts can reference each other.

.. code-block:: yaml

   probes:
     main_probe:
       template: "{part1}{part2}"
       parts:
         part1:
           expr: "rc(target_region[0:20])" # Reverse complement of the first 20 bases
         part2:
           template: "CC{barcode}AA"
           parts:
             barcode:
               expr: "encoding[target]['BC1']"

* **template**: Constructs sequences using placeholders.
* **expr**: Python-like expressions. Supports functions like ``rc()`` (reverse complement), slicing (``[0:20]``), and dynamic lookups.

4. Gene Encoding (encoding)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Map specific genes to custom barcodes or identifiers.

.. code-block:: yaml

   encoding:
     GAPDH:
       BC1: ACGAGCCTTCCA
     ACTB:
       BC1: CGGTAATGGACT

5. Quality Attributes (attributes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define the biochemical or physical properties to calculate.

.. code-block:: yaml

   attributes:
     target_gc:
       target: target_region
       type: gc_content
     target_tm:
       target: target_region
       type: annealing_temperature
     target_mfe:
       target: target_region
       type: fold_score

Supported attribute types include: ``gc_content``, ``annealing_temperature`` (Tm), ``fold_score`` (MFE via ViennaRNA), ``self_match``, ``mapped_sites`` (Bowtie2), ``n_mapped_genes``, and ``kmer_count``.

6. Post-Processing (post_process)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define strict filters and sorting criteria based on the calculated attributes.

.. code-block:: yaml

   post_process:
     filters:
       target_tm:
         condition: target_tm >= 37 & target_tm <= 47
     sorts:
       is_ascending: 
        - target_gc
       is_descending: 
        - target_mfe

   remove_overlap:
     location_interval: 0 # Ensures probes do not overlap physically

----------
Next Steps
----------

For a comprehensive list of all available parameters and advanced configurations, please refer to the :doc:`config_reference`.
