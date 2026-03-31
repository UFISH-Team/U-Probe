================
Python API Guide
================

U-Probe provides a clean, object-oriented Python API, making it ideal for integration into backend web services, Jupyter Notebooks, or larger bioinformatics pipelines.

The core of the API is the ``UProbeAPI`` class, which processes data using ``pandas.DataFrame``, allowing for seamless downstream analysis.

Quick Start
-----------

To use the API, initialize the ``UProbeAPI`` class with your configuration paths.

.. code-block:: python

   import pandas as pd
   from pathlib import Path
   import uprobe

   # Initialize the API
   api = uprobe.UProbeAPI(
       protocol_config=Path("protocol.yaml"),
       genomes_config=Path("genomes.yaml"),
       output_dir=Path("./results")
   )

   # Run the complete automated workflow
   df_final = api.run_workflow(threads=10)

   # Generate an HTML/PDF report
   api.generate_report(df_final)

Step-by-Step Execution
----------------------

For advanced control, you can execute the pipeline step-by-step. This is particularly useful if you want to inject custom Python logic between steps.

.. code-block:: python

   import pandas as pd
   from pathlib import Path
   import uprobe

   api = uprobe.UProbeAPI(
       protocol_config=Path("protocol.yaml"),
       genomes_config=Path("genomes.yaml"),
       output_dir=Path("./results")
   )

   # 1. Build indices (if necessary)
   api.build_genome_index(threads=10)

   # 2. Validate target genes
   api.validate_targets()

   # 3. Extract target sequences
   df_targets = api.generate_target_seqs()

   # 4. Construct probes based on DAG templates
   df_probes = api.construct_probes(df_targets)

   # 5. Combine and post-process (calculate attributes & filter)
   df_combined = pd.concat([df_targets, df_probes], axis=1)
   df_final = api.post_process_probes(df_combined)

   # 6. Generate report
   api.generate_report(df_final)

Working with Pandas Results
----------------------------------------

Since U-Probe returns standard pandas DataFrames, you can easily perform custom filtering, statistical analysis, or visualization using libraries like ``matplotlib`` or ``seaborn``.

.. code-block:: python

   # View basic statistics of the designed probes
   print(df_final.describe())

   # Custom filtering: Select probes with high GC content
   high_gc_probes = df_final[df_final['gc_content'] > 0.55]

   # Save to CSV
   high_gc_probes.to_csv("high_gc_probes.csv", index=False)

Dynamic Configuration
---------------------

Instead of loading YAML files, you can pass Python dictionaries directly to the API. This is highly useful for building web backends (e.g., FastAPI/Flask) where configurations are generated dynamically from user input.

.. code-block:: python

   protocol_dict = {
       "name": "dynamic_design",
       "genome": "GRCh38",
       "targets": ["GAPDH", "ACTB"],
       # ... other protocol parameters
   }

   genomes_dict = {
       "GRCh38": {
           "fasta": "/path/to/GRCh38.fasta",
           "gtf": "/path/to/GRCh38.gtf",
           "align_index": ["bowtie2"]
       }
   }

   api = uprobe.UProbeAPI(
       protocol_config=protocol_dict,
       genomes_config=genomes_dict,
       output_dir=Path("./results")
   )
   
   df_final = api.run_workflow()

----------
Next Steps
----------

For a comprehensive list of all available parameters and advanced configurations, please refer to the :doc:`config_reference`.
