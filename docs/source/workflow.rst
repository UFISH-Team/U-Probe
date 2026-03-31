================
Common Workflows
================

This guide outlines common probe design workflows tailored for specific molecular biology applications. By adjusting the ``protocol.yaml``, U-Probe can be adapted for FISH, PCR, and targeted sequencing.

FISH Probe Design
-----------------

Fluorescence *in situ* hybridization (FISH) probes require high specificity and strict thermodynamic properties to ensure optimal binding and minimal background noise.

.. code-block:: yaml

   name: "FISH_Experiment"
   genome: "GRCh38"
   targets:
     - "GAPDH"
     - "ACTB"
   
   extracts:
     target_region:
       source: "exon"
       length: 30
       overlap: 15
   
   probes:
     fish_probe:
       template: "{spacer}{binding_region}{fluorophore_site}"
       parts:
         spacer:
           expr: "'TTTTTT'"
         binding_region:
           expr: "rc(target_region)"
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
     probe_mfe:
       target: fish_probe
       type: fold_score
   
   post_process:
     filters:
       probe_gc:
         condition: "probe_gc >= 0.45 & probe_gc <= 0.55"
       probe_tm:
         condition: "probe_tm >= 37 & probe_tm <= 47"
       probe_mfe:
         condition: "probe_mfe > -5.0" # Avoid strong secondary structures

PCR Primer Design
----------------------------------------

For PCR amplification, you typically need a forward and reverse primer flanking a target region.

.. code-block:: yaml

   name: "PCR_Primers"
   genome: "GRCh38"
   targets:
     - "BRCA1"
   
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
           expr: "target_region[0:20]"
     
     reverse_primer:
       template: "{primer_sequence}"
       parts:
         primer_sequence:
           expr: "rc(target_region[-20:])"
   
   attributes:
     fwd_tm:
       target: forward_primer
       type: annealing_temperature
     rev_tm:
       target: reverse_primer
       type: annealing_temperature
   
   post_process:
     filters:
       tm_difference:
         condition: "abs(fwd_tm - rev_tm) <= 5" # Ensure similar melting temps

Targeted Sequencing
----------------------------------------

Capture probes for sequencing often require adapters and strict off-target filtering.

.. code-block:: yaml

   name: "Capture_Sequencing"
   genome: "GRCh38"
   targets:
     - "EGFR"
   
   extracts:
     target_region:
       source: "exon"
       length: 120
       overlap: 60
   
   probes:
     capture_probe:
       template: "{adapter1}{target_binding}{adapter2}"
       parts:
         adapter1:
           expr: "'ACACTCTTTCCCTACACGACGCTCTTCCGATCT'"
         target_binding:
           expr: "rc(target_region)"
         adapter2:
           expr: "'AGATCGGAAGAGCGGTTCAGCAGGAATGCCGAG'"
   
   attributes:
     off_targets:
       target: target_binding
       type: n_mapped_genes
       aligner: bowtie2
   
   post_process:
     filters:
       off_targets:
         condition: "off_targets == 1" # Highly specific

-------------------------
Troubleshooting Workflows
-------------------------

Low Probe Yield
~~~~~~~~~~~~~~~
If U-Probe returns too few probes:

1. **Relax Filters:** Widen the acceptable GC content or Tm ranges.
2. **Increase Overlap:** Reduce the stride length in the ``extracts`` section to evaluate more candidate regions.
3. **Change Source:** Switch from ``exon`` to ``gene`` to include intronic regions.

Poor Specificity
~~~~~~~~~~~~~~~~
If probes have high off-target potential:

1. Enable ``n_mapped_genes`` or ``kmer_count`` attributes.
2. Apply strict filters (e.g., ``off_targets == 1``).
