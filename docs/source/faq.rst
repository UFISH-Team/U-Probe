Frequently Asked Questions
==========================

General Questions
-----------------

What is U-Probe?
~~~~~~~~~~~~~~~~~

U-Probe is a comprehensive tool for designing DNA/RNA probes for various molecular biology applications including FISH, PCR, and sequencing. It automates the entire workflow from target selection to quality-filtered probe generation.

What makes U-Probe different from other probe design tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **End-to-end workflow**: Complete automation from genome to final probes
- **Highly configurable**: YAML-based configuration for any probe design
- **Quality-focused**: Comprehensive attribute calculation and filtering
- **Flexible design**: Support for complex multi-part probes
- **Multiple applications**: FISH, PCR, sequencing, and custom designs
- **Python API**: Programmatic access for pipeline integration

Installation and Setup
-----------------------

Which Python versions are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe supports Python 3.9 and higher. Python 3.11 is recommended for best performance.

Do I need to install external tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, U-Probe requires:

- **Bowtie2** for sequence alignment
- **BLAST+** for similarity searches
- **Jellyfish** (optional) for k-mer counting

See the :doc:`installation` guide for details.

Can I use U-Probe on Windows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, but with limitations. The external bioinformatics tools (Bowtie2, BLAST) need to be installed separately. We recommend using Windows Subsystem for Linux (WSL) or Docker for the best experience.

Can I run U-Probe without installing Python?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! You can create a standalone executable using PyInstaller. See the :doc:`installation` guide for instructions.

Configuration
-------------

How do I find the correct gene names for my organism?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gene names must match those in your GTF annotation file. To find available names:

.. code-block:: bash

   # Search for a specific gene
   grep -i "GAPDH" /path/to/annotation.gtf
   
   # List all gene names
   awk '$3=="gene"' /path/to/annotation.gtf | \
   grep -o 'gene_name "[^"]*"' | sort | uniq

Can I design probes for multiple species?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Create separate genome configurations for each species:

.. code-block:: yaml

   # genomes.yaml
   human_hg38:
     fasta: "/data/human/hg38.fa"
     gtf: "/data/human/hg38.gtf"
   
   mouse_mm39:
     fasta: "/data/mouse/mm39.fa" 
     gtf: "/data/mouse/mm39.gtf"

Then use separate protocols for each species or design cross-species probes with appropriate attributes.

How do I design probes for custom genomic regions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use coordinate-based extraction:

.. code-block:: yaml

   extracts:
     target_region:
       source: "genome"
       length: 200
       coordinates:
         - "chr1:1000000-1002000"
         - "chr2:500000-501000"

What's the difference between "exon", "gene", and "genome" extraction?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **exon**: Extracts from annotated exonic regions only (spliced sequences)
- **gene**: Extracts from entire gene regions including introns
- **genome**: Extracts from specified genomic coordinates

Choose based on your application:
- FISH probes: usually "exon" or "gene"
- Genomic PCR: "genome" with coordinates
- RNA detection: "exon"

Probe Design
------------

How do I design FISH probes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basic FISH probe configuration:

.. code-block:: yaml

   probes:
     fish_probe:
       template: "{target_binding}TTTTTT{fluorophore_site}"
       parts:
         target_binding:
           length: 25
           expr: "rc(target_region[0:25])"
         fluorophore_site:
           expr: "encoding[gene_name]['fluorophore']"

See :doc:`examples` for complete FISH configurations.

How do I design PCR primers?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For PCR primer pairs:

.. code-block:: yaml

   probes:
     forward_primer:
       template: "{seq}"
       parts:
         seq:
           length: 22
           expr: "target_region[0:22]"
     
     reverse_primer:
       template: "{seq}"
       parts:
         seq:
           length: 22
           expr: "rc(target_region[-22:])"

Can I use custom sequences in my probes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Use literal sequences in quotes:

.. code-block:: yaml

   probes:
     custom_probe:
       template: "{primer}{target_binding}{adapter}"
       parts:
         primer:
           expr: "'ACGTACGT'"  # Fixed sequence
         target_binding:
           length: 25
           expr: "target_region[0:25]"
         adapter:
           expr: "'TGCATGCA'"

How do I reference other probes in expressions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the probe name in expressions:

.. code-block:: yaml

   probes:
     probe_1:
       template: "{seq}"
       parts:
         seq:
           expr: "target_region[0:20]"
     
     probe_2:
       template: "{partial}"
       parts:
         partial:
           expr: "probe_1[5:15]"  # Uses part of probe_1

Quality Control
---------------

What quality metrics should I use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Essential attributes for most applications:

.. code-block:: yaml

   attributes:
     gc_content:
       target: main_probe
       type: gc_content
     melting_temp:
       target: main_probe
       type: annealing_temperature
     off_targets:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
     secondary_structure:
       target: main_probe
       type: self_match

How do I set appropriate filter thresholds?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with wide ranges and tighten based on results:

.. code-block:: yaml

   post_process:
     filters:
       # Start relaxed
       gc_content:
         condition: "gc_content >= 0.3 & gc_content <= 0.7"
       
       # Then tighten for final design
       # gc_content:
       #   condition: "gc_content >= 0.45 & gc_content <= 0.55"

Use the ``--raw`` flag to examine distributions before setting final thresholds.

Why are all my probes being filtered out?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common causes:

1. **Too strict filters**: Relax conditions temporarily
2. **Failed attribute calculations**: Check for missing indices or files
3. **Inappropriate probe design**: Verify expressions are valid
4. **Target region issues**: Try different extraction parameters

Use ``uprobe --verbose run --raw`` to diagnose.

Performance
-----------

How can I speed up probe design?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Increase threads**: ``uprobe run -t 16``
2. **Use efficient extraction**: "exon" is faster than "gene"
3. **Reduce expensive attributes**: Skip fold_score and kmer_count for initial designs
4. **Process in batches**: Split large target lists

.. code-block:: yaml

   # Fast configuration
   extracts:
     target_region:
       source: "exon"
       length: 100
   
   attributes:
     # Keep only essential fast attributes
     gc_content:
       target: main_probe
       type: gc_content

How much memory does U-Probe need?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Memory usage depends on:

- Genome size (human genome ~8GB for indices)
- Number of targets (1000 genes ~1-2GB)
- Sequence lengths and overlap
- Attribute calculations

For large genomes with many targets, consider 16GB+ RAM.

Can I run U-Probe on a cluster?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! U-Probe is designed for cluster usage:

.. code-block:: bash

   # SLURM example
   #SBATCH --cpus-per-task=16
   #SBATCH --mem=32G
   
   uprobe run -p protocol.yaml -g genomes.yaml -t 16

Output and Results
------------------

What do the output columns mean?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard columns include:

- **gene_name**: Target gene identifier
- **target_region**: Extracted genomic sequence
- **[probe_name]**: Designed probe sequences
- **[attribute_name]**: Calculated quality metrics
- **chromosome, start, end**: Genomic coordinates

How do I interpret quality metrics?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Metric
     - Good Range
     - Notes
   * - gc_content
     - 0.4-0.6
     - Higher = stronger binding, harder to denature
   * - melting_temp
     - 50-65°C
     - Depends on application temperature
   * - self_match
     - <0.7
     - Lower = less secondary structure
   * - n_mapped_genes
     - ≤5
     - Lower = more specific

Can I export results in other formats?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe outputs CSV files which can be easily converted:

.. code-block:: python

   import pandas as pd
   
   # Read CSV
   df = pd.read_csv('results/probes.csv')
   
   # Export to other formats
   df.to_excel('probes.xlsx', index=False)
   df.to_json('probes.json', orient='records')
   df.to_parquet('probes.parquet')

How do I select the best probes from results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   
   df = pd.read_csv('results/probes.csv')
   
   # Top 5 probes per gene by melting temperature
   best_probes = (df.sort_values(['gene_name', 'melting_temp'])
                   .groupby('gene_name')
                   .head(5))
   
   # Filter by multiple criteria
   high_quality = df[
       (df['gc_content'] >= 0.45) & 
       (df['gc_content'] <= 0.55) &
       (df['melting_temp'] >= 55) &
       (df['off_targets'] <= 3)
   ]

Integration
-----------

Can I use U-Probe in my Python pipeline?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Use the Python API:

.. code-block:: python

   from uprobe import UProbeAPI
   
   uprobe = UProbeAPI(protocol_dict, genomes_dict, output_dir)
   results = uprobe.run_workflow()
   
   # Process results with pandas
   filtered_results = results[results['gc_content'] > 0.5]

How do I integrate U-Probe with other tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe works well with:

- **Primer3**: Import U-Probe designs for primer optimization
- **OligoAnalyzer**: Validate secondary structures
- **BLAST**: Additional specificity checking
- **Custom pipelines**: Use CSV outputs as input to downstream tools

Can I run U-Probe in Docker?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Create a Dockerfile:

.. code-block:: dockerfile

   FROM python:3.11
   
   RUN apt-get update && apt-get install -y bowtie2 ncbi-blast+
   
   COPY . /app
   WORKDIR /app
   RUN pip install .
   
   ENTRYPOINT ["uprobe"]

Applications
------------

What applications is U-Probe suitable for?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **FISH**: Fluorescence in situ hybridization probes
- **PCR**: Primer design for amplification
- **qPCR**: Quantitative PCR probes and primers
- **Sequencing**: Capture probes for targeted sequencing
- **Microarrays**: Oligonucleotide probe design
- **Biosensors**: Detection probe design
- **Custom**: Any application requiring designed oligonucleotides

Can U-Probe design riboprobes for RNA ISH?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While U-Probe designs DNA probes, you can adapt the output for riboprobe synthesis by:

1. Designing DNA probes with U-Probe
2. Adding T7/T3/SP6 promoter sequences
3. Using the sequences for in vitro transcription

Is U-Probe suitable for clinical applications?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe is a research tool. For clinical applications:

1. Validate all designs experimentally
2. Follow relevant regulatory guidelines
3. Consider using established clinical probe sets
4. Implement additional quality controls

Getting More Help
------------------

Where can I find more examples?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Check the :doc:`examples` section
- Browse the `GitHub repository <https://github.com/UFISH-Team/U-Probe>`_ examples folder
- Look at test configurations in ``tests/data/``

How do I contribute to U-Probe?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the :doc:`contributing` guide for:

- Reporting bugs
- Requesting features
- Contributing code
- Improving documentation

Where do I report bugs or request features?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Bugs**: `GitHub Issues <https://github.com/UFISH-Team/U-Probe/issues>`_
- **Feature requests**: `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_
- **General questions**: GitHub Discussions

How often is U-Probe updated?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe is actively maintained with:

- Bug fixes as needed
- Regular feature updates
- Security patches
- Documentation improvements

Check the :doc:`changelog` for recent updates.

Can I get commercial support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

U-Probe is open-source software. For commercial support or custom development:

- Contact the development team through GitHub
- Consider hiring contributors for consulting
- Explore academic collaborations

Troubleshooting Questions
-------------------------

Why is my installation failing?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common solutions:

1. Update pip: ``pip install --upgrade pip``
2. Use virtual environment
3. Install system dependencies first
4. Check Python version (≥3.9 required)

See :doc:`troubleshooting` for detailed help.

Why can't U-Probe find my genes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Check gene names match GTF file exactly
2. Try different name formats (symbol, Ensembl ID, etc.)
3. Verify GTF file format and encoding
4. Use case-sensitive matching

Why is probe design so slow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Reduce target list size
2. Increase thread count
3. Skip expensive attributes initially
4. Use faster extraction methods
5. Consider hardware limitations

See :doc:`troubleshooting` for performance optimization tips.

Still Have Questions?
---------------------

If your question isn't answered here:

1. Check the complete documentation
2. Search existing GitHub issues and discussions
3. Ask on `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_
4. Review the :doc:`troubleshooting` guide

The U-Probe community is here to help!
