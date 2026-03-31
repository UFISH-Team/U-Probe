========
Examples
========

This section provides complete, copy-pasteable examples for common probe design scenarios using U-Probe.

Example 1: Basic FISH Probes
----------------------------

Design simple FISH probes for visualizing gene expression.

**genomes.yaml:**

.. code-block:: yaml

   GRCh38:
     fasta: "/data/genomes/hg38/hg38.fa"
     gtf: "/data/genomes/hg38/gencode.v38.annotation.gtf"
     align_index:
       - bowtie2

**protocol.yaml:**

.. code-block:: yaml

   name: "Basic_FISH_Probes"
   genome: "GRCh38"
   
   targets:
     - "GAPDH"
     - "ACTB"
   
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
           expr: "rc(target_region[0:25])"
         fluorophore_site:
           expr: "encoding[target]['fluorophore']"
   
   encoding:
     GAPDH:
       fluorophore: "ACGTACGTACGTACGT"
     ACTB:
       fluorophore: "TGCATGCATGCATGCA"
   
   attributes:
     probe_gc:
       target: fish_probe
       type: gc_content
     probe_tm:
       target: fish_probe
       type: annealing_temperature
   
   post_process:
     filters:
       probe_gc:
         condition: "probe_gc >= 0.45 & probe_gc <= 0.55"
       probe_tm:
         condition: "probe_tm >= 50 & probe_tm <= 60"

**Run the workflow:**

.. code-block:: bash

   uprobe run -p protocol.yaml -g genomes.yaml -o ./results

Example 2: Python API Batch Processing
--------------------------------------

Process multiple gene lists programmatically using the Python API.

.. code-block:: python

   import pandas as pd
   from pathlib import Path
   import uprobe

   genes = ["EGFR", "KRAS", "TP53"]

   protocol_dict = {
       "name": "Batch_Design",
       "genome": "GRCh38",
       "targets": genes,
       "extracts": {
           "target_region": {
               "source": "exon",
               "length": 100,
               "overlap": 20
           }
       },
       "probes": {
           "main_probe": {
               "template": "{binding_region}",
               "parts": {
                   "binding_region": {
                       "expr": "rc(target_region[0:30])"
                   }
               }
           }
       },
       "attributes": {
           "gc": {"target": "main_probe", "type": "gc_content"},
           "tm": {"target": "main_probe", "type": "annealing_temperature"}
       },
       "post_process": {
           "filters": {
               "gc": {"condition": "gc >= 0.4 & gc <= 0.6"},
               "tm": {"condition": "tm >= 50 & tm <= 65"}
           }
       }
   }

   api = uprobe.UProbeAPI(
       protocol_config=protocol_dict,
       genomes_config=Path("genomes.yaml"),
       output_dir=Path("./results")
   )

   df_results = api.run_workflow()
   print(f"Successfully generated {len(df_results)} probes.")
