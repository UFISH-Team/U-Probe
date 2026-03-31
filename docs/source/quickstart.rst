=================
Quick Start Guide
=================

This guide provides a rapid introduction to U-Probe, demonstrating how to design your first set of probes using both the interactive Web UI and the automated Command-Line Interface (CLI).

Prerequisites
-------------

Before proceeding, ensure you have:

1. Successfully installed U-Probe (see :doc:`installation`).
2. Downloaded a reference genome (FASTA format).
3. Downloaded the corresponding gene annotation file (GTF format).

Method 1: Interactive Web UI (New!)
-----------------------------------

For a visual and intuitive design experience, U-Probe provides a built-in web server. This is the recommended approach for users who prefer graphical interfaces over command-line tools.

1. **Launch the Server:**

   .. code-block:: bash

      uprobe server --host 127.0.0.1 --port 8000

2. **Access the Dashboard:**
   Open your web browser and navigate to ``http://127.0.0.1:8000``. 

3. **Design Probes:**
   Follow the on-screen instructions to upload your genome/GTF files, select target genes, define probe structures, and set filtering criteria. The UI will guide you through the entire process and visualize the results.

Method 2: Command-Line Automated Run
--------------------------------------------------

For high-throughput or reproducible workflows, the CLI is highly efficient. U-Probe requires two YAML configuration files to execute a run.

Step 1: Prepare Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``genomes.yaml`` to define your reference paths:

.. code-block:: yaml

   # genomes.yaml
   GRCh38:
     fasta: "/path/to/GRCh38.fasta"
     gtf: "/path/to/GRCh38.gtf"
     align_index:
       - bowtie2

Create a ``protocol.yaml`` to define your design parameters:

.. code-block:: yaml

   # protocol.yaml
   name: my_first_design
   genome: GRCh38
   targets:
     - GAPDH
     - ACTB
   
   extracts:
     target_region:
       source: exon
       length: 30
       overlap: 15

   probes:
     main_probe:
       template: "{part1}"
       parts:
         part1:
           expr: "rc(target_region)"

Step 2: Execute the Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the complete end-to-end pipeline with a single command:

.. code-block:: bash

   uprobe run -p protocol.yaml -g genomes.yaml -o ./results --threads 8

This command automatically performs:
1. Genome index construction (if not already present).
2. Target sequence extraction.
3. Probe construction based on the defined DAG structure.
4. Thermodynamic and off-target attribute calculation.
5. Final filtering and output generation.

Step 3: Review Results
~~~~~~~~~~~~~~~~~~~~~~

Upon completion, navigate to the ``./results`` directory. You will find CSV files containing the generated probes, their sequences, and all calculated attributes (e.g., GC content, Tm, off-target hits).

----------
Next Steps
----------

* Understand the full potential of YAML configurations in the :doc:`configuration` guide.
* Explore advanced use cases in the :doc:`examples` section.
* Learn how to integrate U-Probe into your scripts using the :doc:`python_api`.
