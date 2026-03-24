Quick Start Guide
=================

This guide will get you up and running with U-Probe in just a few minutes. We'll show you the easiest way to design your first probes.

Prerequisites
-------------

Before you begin, make sure you have:

- U-Probe installed (see :doc:`installation`)
- A genome FASTA file
- A gene annotation GTF file

Your First Probe Design
------------------------

U-Probe offers an interactive AI Assistant that makes probe design incredibly easy, especially for beginners. You don't need to write complex configuration files manually; the AI will guide you through the process.

Step 1: Start the AI Assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open your terminal and run the following command:

.. code-block:: bash

   uprobe agent

This will launch an interactive chat session.

Step 2: Describe Your Needs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simply tell the AI what you want to do in natural language. For example:

* "I want to design FISH probes for the GAPDH and ACTB genes in the human genome."
* "Help me create a protocol for targeted sequencing of TP53."

The AI will ask you clarifying questions (like where your genome files are located) and automatically generate the necessary `genomes.yaml` and `protocol.yaml` files for you.

Step 3: Let the AI Run the Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the configuration is ready, the AI can execute the U-Probe workflow for you, or you can run it manually using the generated files:

.. code-block:: bash

   uprobe run -p protocol.yaml -g genomes.yaml -o ./results --threads 4

This command will automatically:
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

The generated CSV files contain your designed probes with all calculated attributes:

.. code-block:: text

   gene_name,target_region,main_probe,gc_content,melting_temp,passed_filters
   GAPDH,ATGC...,ACGT...,0.52,58.3,True
   ACTB,CGTA...,TGCA...,0.48,55.7,True
   ...

You can also generate a visual report to better understand your results:

.. code-block:: bash

   uprobe generate-report -p protocol.yaml -g genomes.yaml --probes results/probes_*.csv -o results/

Alternative: Manual Configuration
---------------------------------

If you prefer to write the configuration files yourself without the AI assistant, you need to create two files:

1. **genomes.yaml**: Defines the paths to your FASTA and GTF files.
2. **protocol.yaml**: Defines your target genes, probe structure, and filtering criteria.

Please refer to the :doc:`configuration` and :doc:`cli` sections for detailed instructions on how to manually set up and run U-Probe.

Next Steps
----------

Now that you've completed your first probe design:

1. Explore more :doc:`examples` for different applications
2. Learn about advanced :doc:`workflow`
3. Customize your designs using the :doc:`config_reference`
4. Integrate U-Probe into your pipelines with the :doc:`python_api`

.. tip::
   Join our `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_ to share your designs and get help from the community!
