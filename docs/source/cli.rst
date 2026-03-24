Command Line Interface
======================

U-Probe provides a comprehensive command-line interface (CLI) for all probe design operations. This reference covers all available commands and their options.

Overview
--------

After installation, U-Probe is available via the ``uprobe`` command. The CLI is organized into subcommands, each handling a specific aspect of the probe design workflow.

.. code-block:: bash

   uprobe [OPTIONS] COMMAND [ARGS]...

Global Options
--------------

These options are available for all commands:

.. option:: --version

   Show the U-Probe version and exit.

.. option:: --verbose, -v

   Enable verbose logging. Shows detailed progress information.

.. option:: --quiet, -q  

   Suppress all output except errors. Useful for scripting.

.. option:: --help

   Show help message and exit.

Commands Overview
-----------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Command
     - Description
   * - :ref:`agent`
     - Start an interactive AI session to help design probes (Recommended)
   * - :ref:`run`
     - Execute the complete probe design workflow
   * - :ref:`build-index`  
     - Build genome indices for alignment tools
   * - :ref:`validate-targets`
     - Validate target genes against genome annotation
   * - :ref:`generate-targets`
     - Generate target region sequences from genome
   * - :ref:`construct-probes`
     - Construct probes from target sequences
   * - :ref:`post-process`
     - Add attributes and apply filters to probes
   * - :ref:`generate-barcodes`
     - Generate DNA barcode sequences
   * - :ref:`generate-report`
     - Generate interpretation report and plots for probe results
   * - :ref:`version`
     - Show version information

.. _agent:

agent
-----

Start an interactive session with the U-Probe AI Agent. This is the recommended way for beginners to use U-Probe, as the AI will guide you through the configuration and execution process via natural language.

.. code-block:: bash

   uprobe agent

.. _run:

run
---

Execute the complete probe design workflow from start to finish.

.. code-block:: bash

   uprobe run [OPTIONS]

This command runs the entire pipeline: genome indexing, target validation, sequence generation, probe construction, filtering, and saving results.

**Options:**

.. option:: --protocol, -p PATH

   **Required.** Path to probe design protocol configuration file (YAML).

.. option:: --genomes, -g PATH

   **Required.** Path to genome configuration file (YAML).

.. option:: --output, -o PATH

   Output directory. Default: ``./results``

.. option:: --raw

   Save unfiltered raw probe data in addition to filtered results.

.. option:: --continue-invalid

   Continue execution even if some targets are invalid.

.. option:: --threads, -t INTEGER

   Number of threads for computation. Default: ``10``

**Examples:**

.. code-block:: bash

   # Basic run
   uprobe run -p protocol.yaml -g genomes.yaml

   # With custom output and threading
   uprobe run -p protocol.yaml -g genomes.yaml -o my_results/ -t 8

.. _build-index:

build-index
-----------

Build genome indices for alignment tools (Bowtie2, BLAST).

.. code-block:: bash

   uprobe build-index -p protocol.yaml -g genomes.yaml -t 10

.. _validate-targets:

validate-targets
----------------

Validate target genes against the genome annotation file.

.. code-block:: bash

   uprobe validate-targets -p protocol.yaml -g genomes.yaml

.. _generate-targets:

generate-targets
----------------

Generate target region sequences from the genome.

.. code-block:: bash

   uprobe generate-targets -p protocol.yaml -g genomes.yaml -o ./results

.. _construct-probes:

construct-probes
----------------

Construct probes from target sequences.

.. code-block:: bash

   uprobe construct-probes -p protocol.yaml -g genomes.yaml --targets results/target_sequences.csv -o ./results

.. _post-process:

post-process
------------

Add quality attributes and apply filters to probes.

.. code-block:: bash

   uprobe post-process -p protocol.yaml -g genomes.yaml --probes results/constructed_probes.csv -o ./results

.. _generate-barcodes:

generate-barcodes
-----------------

Generate DNA barcode sequences based on protocol or specific strategies.

.. code-block:: bash

   uprobe generate-barcodes -p protocol.yaml -o ./barcodes

.. _generate-report:

generate-report
---------------

Generate interpretation report and plots for probe results.

.. code-block:: bash

   uprobe generate-report -p protocol.yaml -g genomes.yaml --probes results/probes.csv -o ./results

.. _version:

version
-------

Show the U-Probe version information.

.. code-block:: bash

   uprobe version

Workflow Examples
-----------------

Complete Workflow
~~~~~~~~~~~~~~~~~

Run everything with one command:

.. code-block:: bash

   uprobe run \
     --protocol experiment.yaml \
     --genomes genomes.yaml \
     --output results/ \
     --threads 8 \
     --raw \
     --verbose

Step-by-Step Workflow
~~~~~~~~~~~~~~~~~~~~~

For more control, run individual steps:

.. code-block:: bash

   # 1. Build indices
   uprobe build-index -p experiment.yaml -g genomes.yaml -t 8

   # 2. Validate configuration
   uprobe validate-targets -p experiment.yaml -g genomes.yaml

   # 3. Generate target sequences
   uprobe generate-targets -p experiment.yaml -g genomes.yaml -o results/

   # 4. Construct probes
   uprobe construct-probes -p experiment.yaml -g genomes.yaml --targets results/target_sequences.csv -o results/

   # 5. Add attributes and filter
   uprobe post-process -p experiment.yaml -g genomes.yaml --probes results/constructed_probes.csv -o results/ --raw

   # 6. Generate report
   uprobe generate-report -p experiment.yaml -g genomes.yaml --probes results/probes_*.csv -o results/

Next Steps
----------

Now that you know the CLI commands:

1. Learn about the :doc:`python_api` for programmatic access
2. Explore :doc:`workflow` for common use cases
3. Check out :doc:`examples` for real-world applications
4. Refer to :doc:`troubleshooting` if you encounter issues
