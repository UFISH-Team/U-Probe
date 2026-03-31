======================
Command Line Interface
======================

U-Probe provides a robust Command-Line Interface (CLI) tailored for high-throughput bioinformatics pipelines. 

Overview
--------

The ``uprobe`` CLI is organized into subcommands. You can view all available commands by running:

.. code-block:: bash

   uprobe --help

Core Commands
-------------

agent
~~~~~

Starts an interactive session with the U-Probe AI Agent. This command bootstraps a REPL environment where you can design probes through natural language conversation.

.. code-block:: bash

   uprobe agent

server
~~~~~~

Starts the built-in interactive Web UI server.

.. code-block:: bash

   uprobe server --host 127.0.0.1 --port 8000

run
~~~

Executes the complete end-to-end probe design workflow. This is the most commonly used command for automated design.

.. code-block:: bash

   uprobe run -p protocol.yaml -g genomes.yaml -o ./results --threads 10

**Key Options:**

* ``-p, --protocol``: Path to the protocol configuration file.
* ``-g, --genomes``: Path to the genomes configuration file.
* ``-o, --output``: Output directory (default: ``./results``).
* ``-t, --threads``: Number of CPU threads to use.
* ``--raw``: Output unfiltered raw probe data alongside the filtered results.

Step-by-Step Commands
---------------------

For advanced users requiring intermediate outputs, U-Probe allows executing each step of the pipeline individually.

1. Build Genome Indices
~~~~~~~~~~~~~~~~~~~~~~~

Builds required indices for aligners (Bowtie2, BLAST) and k-mer counters (Jellyfish).

.. code-block:: bash

   uprobe build-index -p protocol.yaml -g genomes.yaml -t 10

2. Validate Targets
~~~~~~~~~~~~~~~~~~~

Validates target genes against the provided GTF annotation file.

.. code-block:: bash

   uprobe validate-targets -p protocol.yaml -g genomes.yaml

3. Generate Targets
~~~~~~~~~~~~~~~~~~~

Extracts target region sequences based on the ``extracts`` rules in your protocol.

.. code-block:: bash

   uprobe generate-targets -p protocol.yaml -g genomes.yaml -o ./results

4. Construct Probes
~~~~~~~~~~~~~~~~~~~

Constructs initial probes based on the DAG templates defined in your protocol.

.. code-block:: bash

   uprobe construct-probes -p protocol.yaml -g genomes.yaml --targets ./results/target_sequences.csv -o ./results

5. Post-Process
~~~~~~~~~~~~~~~

Calculates thermodynamic/off-target attributes and applies filters.

.. code-block:: bash

   uprobe post-process -p protocol.yaml -g genomes.yaml --probes ./results/constructed_probes.csv -o ./results

6. Generate Report
~~~~~~~~~~~~~~~~~~

Generates an HTML/PDF visual analysis report for the designed probes.

.. code-block:: bash

   uprobe generate-report -p protocol.yaml -g genomes.yaml --probes ./results/probes_*.csv -o ./results
