Common Workflows
================

This guide covers common probe design workflows and best practices for different molecular biology applications.

FISH Probe Design
-----------------

Fluorescence in situ hybridization (FISH) requires probes with specific characteristics for optimal performance.

Basic FISH Protocol
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # fish_protocol.yaml
   name: "FISH_Experiment"
   genome: "human_hg38"
   
   targets:
     - "GAPDH"
     - "ACTB"
     - "TP53"
   
   extracts:
     target_region:
       source: "exon"
       length: 100
       overlap: 25
   
   probes:
     fish_probe:
       template: "{binding_region}TTTTTT{fluorophore_site}"
       parts:
         binding_region:
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
     secondary_structure:
       target: fish_probe
       type: fold_score
   
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.45 & gc_content <= 0.55"
       melting_temp:
         condition: "melting_temp >= 50 & melting_temp <= 60"
       secondary_structure:
         condition: "secondary_structure < 0.3"

PCR Primer Design
-----------------

Design primers for PCR amplification with proper spacing and characteristics.

PCR Primer Protocol
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # pcr_protocol.yaml
   name: "PCR_Primers"
   genome: "human_hg38"
   
   targets:
     - "BRCA1"
     - "BRCA2"
   
   extracts:
     target_region:
       source: "exon"
       length: 200
       overlap: 0
   
   probes:
     forward_primer:
       template: "{primer_sequence}"
       parts:
         primer_sequence:
           length: 20
           expr: "target_region[0:20]"
     
     reverse_primer:
       template: "{primer_sequence}"
       parts:
         primer_sequence:
           length: 20
           expr: "rc(target_region[-20:])"
   
   attributes:
     fwd_gc:
       target: forward_primer
       type: gc_content
     fwd_tm:
       target: forward_primer
       type: annealing_temperature
     rev_gc:
       target: reverse_primer
       type: gc_content
     rev_tm:
       target: reverse_primer
       type: annealing_temperature
   
   post_process:
     filters:
       fwd_gc:
         condition: "fwd_gc >= 0.4 & fwd_gc <= 0.6"
       rev_gc:
         condition: "rev_gc >= 0.4 & rev_gc <= 0.6"
       tm_difference:
         condition: "abs(fwd_tm - rev_tm) <= 5"

Sequencing Probe Design
-----------------------

Design probes for targeted sequencing applications.

Capture Probe Protocol
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # capture_protocol.yaml
   name: "Capture_Sequencing"
   genome: "human_hg38"
   
   targets:
     - "EGFR"
     - "KRAS" 
     - "PIK3CA"
   
   extracts:
     target_region:
       source: "exon"
       length: 80
       overlap: 40
   
   probes:
     capture_probe:
       template: "{adapter}{target_binding}{adapter2}"
       parts:
         adapter:
           expr: "'ACACTCTTTCCCTACACGACGCTCTTCCGATCT'"
         target_binding:
           length: 50
           expr: "target_region[15:65]"
         adapter2:
           expr: "'AGATCGGAAGAGCGGTTCAGCAGGAATGCCGAG'"
   
   attributes:
     gc_content:
       target: capture_probe
       type: gc_content
     melting_temp:
       target: capture_probe
       type: annealing_temperature
     off_targets:
       target: target_binding
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
   
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.35 & gc_content <= 0.65"
       melting_temp:
         condition: "melting_temp >= 55 & melting_temp <= 70"
       off_targets:
         condition: "off_targets <= 10"

Best Practices
--------------

Quality Control
~~~~~~~~~~~~~~~

Always include comprehensive quality control:

.. code-block:: yaml

   attributes:
     # Basic properties
     gc_content:
       target: main_probe
       type: gc_content
     melting_temp:
       target: main_probe  
       type: annealing_temperature
     
     # Specificity checks
     off_targets:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30
     
     # Secondary structure
     self_complementarity:
       target: main_probe
       type: self_match
     folding_propensity:
       target: main_probe
       type: fold_score
     
     # Abundance filters (if using Jellyfish)
     repetitive_kmers:
       target: main_probe
       type: kmer_count
       kmer_length: 15
       kmer_threshold: 1000

Iterative Design
~~~~~~~~~~~~~~~~

Use iterative refinement:

.. code-block:: bash

   # 1. Start with relaxed filters
   uprobe run -p initial_protocol.yaml -g genomes.yaml --raw

   # 2. Analyze results and adjust filters
   # Edit protocol.yaml based on raw results

   # 3. Refine with stricter filters
   uprobe run -p refined_protocol.yaml -g genomes.yaml

Batch Processing
~~~~~~~~~~~~~~~~

For large gene sets:

.. code-block:: bash

   # Split into batches
   split -l 50 all_genes.txt batch_
   
   # Process each batch
   for batch in batch_*; do
     # Create protocol for this batch
     python create_protocol.py $batch > protocol_$batch.yaml
     uprobe run -p protocol_$batch.yaml -g genomes.yaml -o results_$batch/
   done

Multi-Species Workflows
-----------------------

Comparative Studies
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Use separate protocols for each species
   # human_protocol.yaml
   name: "Human_Probes"
   genome: "human_hg38"
   targets: ["GAPDH", "ACTB"]
   
   # mouse_protocol.yaml  
   name: "Mouse_Probes"
   genome: "mouse_mm39"
   targets: ["Gapdh", "Actb"]  # Note: different gene names

.. code-block:: bash

   # Process both species
   uprobe run -p human_protocol.yaml -g genomes.yaml -o human_results/
   uprobe run -p mouse_protocol.yaml -g genomes.yaml -o mouse_results/

Cross-Species Conservation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Design probes that work across species:

.. code-block:: yaml

   attributes:
     human_specificity:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
       genome: human_hg38
     
     mouse_specificity:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2  
       genome: mouse_mm39
   
   post_process:
     filters:
       cross_species:
         condition: "human_specificity <= 3 & mouse_specificity <= 3"

Troubleshooting Workflows
-------------------------

Low Probe Yield
~~~~~~~~~~~~~~~

If getting too few probes:

1. **Relax filters:**

.. code-block:: yaml

   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.3 & gc_content <= 0.7"  # Wider range

2. **Increase overlap:**

.. code-block:: yaml

   extracts:
     target_region:
       overlap: 50  # More overlapping regions

3. **Use different source regions:**

.. code-block:: yaml

   extracts:
     target_region:
       source: "gene"  # Include introns

Poor Probe Quality
~~~~~~~~~~~~~~~~~~

If probes have quality issues:

1. **Add more stringent attributes:**

.. code-block:: yaml

   attributes:
     hairpin_formation:
       target: main_probe
       type: fold_score
     dimer_formation:
       target: main_probe
       type: self_match

2. **Filter repetitive sequences:**

.. code-block:: yaml

   attributes:
     repetitive_content:
       target: main_probe
       type: kmer_count
       kmer_length: 12
       kmer_threshold: 100
   
   post_process:
     filters:
       repetitive_content:
         condition: "repetitive_content <= 5"

Optimization Strategies
-----------------------

Parameter Sweeping
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Systematic parameter optimization
   import itertools
   from uprobe import UProbeAPI

   # Parameter ranges
   gc_ranges = [(0.4, 0.6), (0.35, 0.65), (0.3, 0.7)]
   tm_ranges = [(50, 60), (45, 65), (40, 70)]
   
   best_result = None
   best_count = 0
   
   for gc_range, tm_range in itertools.product(gc_ranges, tm_ranges):
       # Update protocol
       protocol['post_process']['filters']['gc_content']['condition'] = \
           f"gc_content >= {gc_range[0]} & gc_content <= {gc_range[1]}"
       protocol['post_process']['filters']['melting_temp']['condition'] = \
           f"melting_temp >= {tm_range[0]} & melting_temp <= {tm_range[1]}"
       
       # Test
       uprobe = UProbeAPI(protocol, genomes_config, output_dir)
       results = uprobe.run_workflow()
       
       if len(results) > best_count:
           best_count = len(results)
           best_result = (gc_range, tm_range)
   
   print(f"Best parameters: GC {best_result[0]}, Tm {best_result[1]}")

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

For large-scale projects:

.. code-block:: yaml

   # Optimize for speed
   extracts:
     target_region:
       source: "exon"  # Faster than "gene"
       length: 100     # Shorter regions process faster
   
   # Minimize expensive attributes
   attributes:
     # Skip time-consuming calculations
     basic_gc:
       target: main_probe
       type: gc_content
     # Comment out expensive ones:
     # fold_score: ...
     # kmer_count: ...

Next Steps
----------

- Explore specific :doc:`examples` for your application
- Learn about :doc:`troubleshooting` common issues
- Check the :doc:`config_reference` for all options
