Quick Start Guide
=================

This guide will get you up and running with U-Probe in just a few minutes. We'll walk through a simple probe design workflow from start to finish.

Prerequisites
-------------

Before you begin, make sure you have:

- U-Probe installed (see :doc:`installation`)
- A genome FASTA file
- A gene annotation GTF file
- Basic knowledge of YAML configuration files

Your First Probe Design
------------------------

Let's design probes for some target genes using a simple configuration.

Step 1: Prepare Your Data
~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll need two types of files:

1. **Genome files** (FASTA + GTF)
2. **Configuration files** (YAML)

For this tutorial, we'll assume you have:

- ``/path/to/genome.fa`` - Genome FASTA file
- ``/path/to/annotation.gtf`` - Gene annotation GTF file

Step 2: Create Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create genomes.yaml:**

.. code-block:: yaml

   # genomes.yaml
   human_demo:
     description: "Demo human genome"
     species: "Homo sapiens"
     fasta: "/path/to/genome.fa"
     gtf: "/path/to/annotation.gtf"
     align_index:
       - bowtie2
       - blast
     jellyfish: false

**Create protocol.yaml:**

.. code-block:: yaml

   # protocol.yaml
   name: "MyFirstProbes"
   genome: "human_demo"
   
   # Target genes to design probes for
   targets:
     - "GAPDH"
     - "ACTB"
     - "TP53"
   
   # How to extract target regions
   extracts:
     target_region:
       source: "exon"        # Extract from exons
       overlap: 10           # Overlap between adjacent extracts
       length: 120           # Length of each target region
   
   # Probe design specifications
   probes:
     main_probe:
       template: "{spacer}{target_binding}{barcode}"
       parts:
         spacer:
           length: 10
           expr: "random_seq(10)"
         target_binding:
           length: 25
           expr: "rc(target_region[0:25])"
         barcode:
           length: 15
           expr: "encoding[gene_name]['BC1']"
   
   # Barcode sequences for each gene
   encoding:
     GAPDH:
       BC1: "ACGTACGTACGTACG"
     ACTB:
       BC1: "TGCATGCATGCATGC"
     TP53:
       BC1: "CGATCGATCGATCGA"
   
   # Quality control attributes
   attributes:
     gc_content:
       target: main_probe
       type: gc_content
     melting_temp:
       target: main_probe
       type: annealing_temperature
   
   # Filtering criteria
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.4 & gc_content <= 0.6"
       melting_temp:
         condition: "melting_temp >= 50 & melting_temp <= 65"

Step 3: Run the Complete Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now run U-Probe with a single command:

.. code-block:: bash

   uprobe run \
     --protocol protocol.yaml \
     --genomes genomes.yaml \
     --output results/ \
     --threads 4 \
     --raw

This command will:

1. Build genome indices (if needed)
2. Validate your target genes
3. Extract target regions
4. Design probes
5. Calculate quality attributes
6. Apply filters
7. Save results to CSV files

Step 4: Examine the Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check the results directory:

.. code-block:: bash

   ls results/
   # Output:
   # MyFirstProbes_20240131_143022.csv      # Filtered probes
   # MyFirstProbes_20240131_143022_raw.csv  # All probes (if --raw used)

The CSV files contain your designed probes with all calculated attributes:

.. code-block:: text

   gene_name,target_region,main_probe,gc_content,melting_temp,passed_filters
   GAPDH,ATGC...,ACGT...,0.52,58.3,True
   ACTB,CGTA...,TGCA...,0.48,55.7,True
   ...

Step-by-Step Workflow
----------------------

For more control, you can run individual steps:

Step 1: Build Genome Index
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uprobe build-index \
     --protocol protocol.yaml \
     --genomes genomes.yaml \
     --threads 4

Step 2: Validate Targets
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uprobe validate-targets \
     --protocol protocol.yaml \
     --genomes genomes.yaml

Step 3: Generate Target Sequences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uprobe generate-targets \
     --protocol protocol.yaml \
     --genomes genomes.yaml \
     --output results/

Step 4: Design Probes
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uprobe construct-probes \
     --protocol protocol.yaml \
     --genomes genomes.yaml \
     --targets results/target_sequences.csv \
     --output results/

Step 5: Post-Process (Add Attributes & Filter)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uprobe post-process \
     --protocol protocol.yaml \
     --genomes genomes.yaml \
     --probes results/constructed_probes.csv \
     --output results/ \
     --raw

Understanding the Output
------------------------

Probe CSV Columns
~~~~~~~~~~~~~~~~~

The output CSV files contain these key columns:

- **gene_name**: Target gene identifier
- **target_region**: Extracted genomic sequence
- **[probe_name]**: Designed probe sequence(s)
- **[attribute_name]**: Calculated quality metrics
- **passed_filters**: Whether the probe passed all filters

Quality Metrics
~~~~~~~~~~~~~~~

Common quality attributes include:

- **gc_content**: GC content (0.0 to 1.0)
- **annealing_temperature**: Melting temperature (°C)
- **self_match**: Self-complementarity score
- **fold_score**: Secondary structure propensity
- **mapped_genes**: Off-target binding potential

Customizing Your Design
-----------------------

Probe Structure
~~~~~~~~~~~~~~~

Modify the probe template to change structure:

.. code-block:: yaml

   probes:
     forward_probe:
       template: "{primer}{target_binding}"
       parts:
         primer:
           expr: "'ACGTACGT'"  # Fixed primer sequence
         target_binding:
           length: 20
           expr: "target_region[10:30]"
     
     reverse_probe:
       template: "{target_binding}{primer}"
       parts:
         target_binding:
           length: 20
           expr: "rc(target_region[30:50])"
         primer:
           expr: "'TGCATGCA'"

Target Extraction
~~~~~~~~~~~~~~~~~

Change how target regions are extracted:

.. code-block:: yaml

   extracts:
     target_region:
       source: "genome"      # Extract from anywhere in genome
       length: 200           # Longer regions
       overlap: 50           # More overlap
       # Custom genomic coordinates
       coordinates:
         - "chr1:1000000-1001000"
         - "chr2:2000000-2001000"

Quality Filters
~~~~~~~~~~~~~~~

Adjust filtering criteria:

.. code-block:: yaml

   post_process:
     filters:
       # Stricter GC content
       gc_content:
         condition: "gc_content >= 0.45 & gc_content <= 0.55"
       
       # Temperature range
       melting_temp:
         condition: "melting_temp >= 55 & melting_temp <= 60"
       
       # Exclude high off-targets
       mapped_genes:
         condition: "mapped_genes <= 3"

Common Use Cases
----------------

FISH Probes
~~~~~~~~~~~

For fluorescence in situ hybridization:

.. code-block:: yaml

   probes:
     fish_probe:
       template: "{target_binding}{spacer}{fluorophore_binding}"
       parts:
         target_binding:
           length: 30
           expr: "rc(target_region[0:30])"
         spacer:
           expr: "'TTTTTT'"  # Poly-T spacer
         fluorophore_binding:
           expr: "encoding[gene_name]['fluorophore']"

PCR Primers
~~~~~~~~~~~

For amplification-based methods:

.. code-block:: yaml

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

Troubleshooting
---------------

No Targets Found
~~~~~~~~~~~~~~~~

If no target sequences are generated:

1. Check gene names in your GTF file
2. Verify ``source`` parameter (exon, gene, etc.)
3. Reduce ``length`` or ``overlap`` parameters

No Probes Pass Filters
~~~~~~~~~~~~~~~~~~~~~~

If all probes are filtered out:

1. Relax filtering conditions
2. Check attribute calculations
3. Use ``--raw`` to see all designed probes

Performance Issues
~~~~~~~~~~~~~~~~~~

For large genomes or many targets:

1. Increase ``--threads`` parameter
2. Process targets in smaller batches
3. Use SSD storage for genome files

Next Steps
----------

Now that you've completed your first probe design:

1. Explore more :doc:`examples` for different applications
2. Learn about advanced :doc:`workflows`
3. Customize your designs using the :doc:`config_reference`
4. Integrate U-Probe into your pipelines with the :doc:`python_api`

.. tip::
   Join our `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_ to share your designs and get help from the community!
