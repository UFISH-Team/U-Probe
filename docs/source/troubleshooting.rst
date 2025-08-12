Troubleshooting
===============

This guide helps resolve common issues when using U-Probe.

Installation Issues
-------------------

Command not found: uprobe
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** After installation, the ``uprobe`` command is not recognized.

**Solutions:**

1. **Check if installed correctly:**

   .. code-block:: bash

      pip list | grep uprobe
      python -c "import uprobe; print(uprobe.__version__)"

2. **Try using Python module syntax:**

   .. code-block:: bash

      python -m uprobe --help

3. **Check PATH (for --user installs):**

   .. code-block:: bash

      # Add to ~/.bashrc or ~/.zshrc
      export PATH="$HOME/.local/bin:$PATH"

4. **Reinstall in a virtual environment:**

   .. code-block:: bash

      python -m venv uprobe_env
      source uprobe_env/bin/activate
      pip install uprobe

ImportError: No module named 'uprobe'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Python cannot find the uprobe module.

**Solutions:**

1. **Verify installation:**

   .. code-block:: bash

      pip show uprobe

2. **Check Python environment:**

   .. code-block:: bash

      which python
      which pip
      # Ensure both point to the same environment

3. **Reinstall:**

   .. code-block:: bash

      pip uninstall uprobe
      pip install uprobe

Missing dependencies errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Errors about missing packages like pandas, click, etc.

**Solutions:**

1. **Install all requirements:**

   .. code-block:: bash

      pip install -r requirements.txt

2. **Update pip and try again:**

   .. code-block:: bash

      pip install --upgrade pip
      pip install uprobe

3. **For development installs:**

   .. code-block:: bash

      pip install -e ".[dev]"

Configuration Issues
--------------------

FileNotFoundError: [Errno 2] No such file or directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** U-Probe cannot find specified files.

**Solutions:**

1. **Use absolute paths:**

   .. code-block:: yaml

      # Instead of relative paths
      fasta: "genome.fa"
      # Use absolute paths  
      fasta: "/full/path/to/genome.fa"

2. **Check file permissions:**

   .. code-block:: bash

      ls -la /path/to/genome.fa
      # Ensure files are readable

3. **Verify file existence:**

   .. code-block:: bash

      file /path/to/genome.fa
      head -n 5 /path/to/genome.fa

Target validation failed
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Error message "Invalid targets found" or no targets pass validation.

**Solutions:**

1. **Check gene names in GTF:**

   .. code-block:: bash

      # Search for your gene in GTF
      grep -i "GAPDH" /path/to/annotation.gtf
      
      # Check available gene names
      awk '$3=="gene"' /path/to/annotation.gtf | \
      grep -o 'gene_name "[^"]*"' | sort | uniq | head -20

2. **Try different gene identifiers:**

   .. code-block:: yaml

      targets:
        - "GAPDH"           # Gene symbol
        - "ENSG00000111640" # Ensembl ID
        - "2597"            # Entrez ID

3. **Use continue-invalid flag for testing:**

   .. code-block:: bash

      uprobe validate-targets -p protocol.yaml -g genomes.yaml --continue-invalid

4. **Check GTF format:**

   .. code-block:: bash

      # GTF should have these columns:
      # seqname source feature start end score strand frame attribute
      head -n 5 /path/to/annotation.gtf

Invalid YAML syntax
~~~~~~~~~~~~~~~~~~~~

**Problem:** YAML parsing errors.

**Solutions:**

1. **Check indentation (use spaces, not tabs):**

   .. code-block:: yaml

      # Correct
      probes:
        main_probe:          # 2 spaces
          template: "{seq}"  # 4 spaces
      
      # Wrong (tabs or inconsistent spacing)
      probes:
      	main_probe:        # tab character
         template: "{seq}"   # 3 spaces

2. **Validate YAML syntax:**

   .. code-block:: bash

      python -c "import yaml; yaml.safe_load(open('protocol.yaml'))"

3. **Quote strings with special characters:**

   .. code-block:: yaml

      # Quote expressions and conditions
      expr: "rc(target_region[0:20])"
      condition: "gc_content >= 0.4 & gc_content <= 0.6"

Runtime Issues
--------------

No target sequences generated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** The generate-targets step produces an empty result.

**Solutions:**

1. **Check extraction parameters:**

   .. code-block:: yaml

      extracts:
        target_region:
          source: "exon"  # Try "gene" if exons are too short
          length: 50      # Reduce if regions are smaller
          overlap: 10     # Reduce overlap

2. **Verify targets exist:**

   .. code-block:: bash

      uprobe validate-targets -p protocol.yaml -g genomes.yaml -v

3. **Check for gene annotation issues:**

   .. code-block:: bash

      # Look for your gene in GTF
      grep "GAPDH" /path/to/annotation.gtf | head -5

No probes constructed
~~~~~~~~~~~~~~~~~~~~~

**Problem:** The construct-probes step fails or produces no output.

**Solutions:**

1. **Check probe expressions:**

   .. code-block:: yaml

      probes:
        test_probe:
          template: "{simple_part}"
          parts:
            simple_part:
              length: 20
              expr: "target_region[0:20]"  # Simple expression

2. **Verify encoding mappings:**

   .. code-block:: yaml

      # Ensure all target genes have encoding entries
      encoding:
        GAPDH:  # Must match target name exactly
          BC1: "ACGTACGTACGT"

3. **Test with minimal probe:**

   .. code-block:: yaml

      probes:
        minimal:
          expr: "target_region[0:25]"

All probes filtered out
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Post-processing removes all probes.

**Solutions:**

1. **Use --raw flag to see unfiltered probes:**

   .. code-block:: bash

      uprobe run -p protocol.yaml -g genomes.yaml --raw

2. **Relax filtering conditions:**

   .. code-block:: yaml

      post_process:
        filters:
          gc_content:
            condition: "gc_content >= 0.2 & gc_content <= 0.8"  # Very relaxed

3. **Check attribute calculations:**

   .. code-block:: yaml

      # Remove problematic attributes temporarily
      attributes:
        basic_gc:
          target: main_probe
          type: gc_content
        # Comment out complex attributes:
        # off_targets: ...

4. **Examine raw results:**

   .. code-block:: python

      import pandas as pd
      df = pd.read_csv('results/experiment_raw.csv')
      print(df.describe())  # Check attribute distributions
      print(df[df['gc_content'].isna()])  # Find failed calculations

Performance Issues
------------------

Slow execution
~~~~~~~~~~~~~~

**Problem:** U-Probe runs very slowly.

**Solutions:**

1. **Increase thread count:**

   .. code-block:: bash

      uprobe run -p protocol.yaml -g genomes.yaml -t 16

2. **Use faster extraction:**

   .. code-block:: yaml

      extracts:
        target_region:
          source: "exon"  # Faster than "gene"
          length: 100     # Shorter regions

3. **Reduce expensive attributes:**

   .. code-block:: yaml

      attributes:
        # Keep fast attributes
        gc_content:
          target: main_probe
          type: gc_content
        # Remove slow ones temporarily:
        # fold_score: ...
        # kmer_count: ...

4. **Process in batches:**

   .. code-block:: bash

      # Split large target lists
      uprobe run -p small_batch.yaml -g genomes.yaml

Memory issues
~~~~~~~~~~~~~

**Problem:** Out of memory errors or system becomes unresponsive.

**Solutions:**

1. **Process smaller batches:**

   .. code-block:: yaml

      targets:
        - "GAPDH"
        - "ACTB"
        # Process 5-10 genes at a time for large genomes

2. **Reduce sequence length:**

   .. code-block:: yaml

      extracts:
        target_region:
          length: 80   # Shorter sequences use less memory
          overlap: 15

3. **Skip memory-intensive attributes:**

   .. code-block:: yaml

      # Avoid these for large datasets:
      # - n_mapped_genes with blast
      # - kmer_count
      # - complex fold_score calculations

Index building fails
~~~~~~~~~~~~~~~~~~~~

**Problem:** Genome index building fails or crashes.

**Solutions:**

1. **Check available disk space:**

   .. code-block:: bash

      df -h /path/to/genome/directory

2. **Verify genome file integrity:**

   .. code-block:: bash

      file /path/to/genome.fa
      head -n 10 /path/to/genome.fa
      tail -n 10 /path/to/genome.fa

3. **Build indices manually:**

   .. code-block:: bash

      # Bowtie2
      bowtie2-build /path/to/genome.fa /path/to/indices/genome
      
      # BLAST
      makeblastdb -in /path/to/genome.fa -dbtype nucl -out /path/to/indices/genome

4. **Use pre-built indices:**

   .. code-block:: yaml

      # Point to existing indices
      human_hg38:
        fasta: "/data/hg38.fa"
        gtf: "/data/hg38.gtf"
        out: "/data/existing_indices"  # Pre-built indices location

Attribute Calculation Issues
----------------------------

Melting temperature calculation fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Tm calculation produces NaN values or errors.

**Solutions:**

1. **Check sequence validity:**

   .. code-block:: python

      # Sequences should only contain ATCG
      import re
      def check_sequence(seq):
          return bool(re.match('^[ATCG]*$', seq))

2. **Handle short sequences:**

   .. code-block:: yaml

      # Ensure minimum sequence length
      probes:
        main_probe:
          parts:
            binding:
              length: 15  # Minimum for reliable Tm calculation

Off-target calculation fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Alignment-based attributes fail.

**Solutions:**

1. **Verify indices exist:**

   .. code-block:: bash

      ls -la /path/to/indices/
      # Should contain .bt2 files for bowtie2

2. **Test aligner manually:**

   .. code-block:: bash

      # Test bowtie2
      echo "ATCGATCGATCGATCG" | bowtie2 -x /path/to/indices/genome -

3. **Use alternative aligner:**

   .. code-block:: yaml

      attributes:
        off_targets:
          target: main_probe
          type: n_mapped_genes
          aligner: blast  # Try blast if bowtie2 fails

K-mer counting fails
~~~~~~~~~~~~~~~~~~~~

**Problem:** kmer_count attributes produce errors.

**Solutions:**

1. **Check Jellyfish database:**

   .. code-block:: bash

      jellyfish info genome.jf

2. **Build Jellyfish database:**

   .. code-block:: bash

      jellyfish count -m 15 -s 1000000000 -t 8 -o genome.jf genome.fa

3. **Use alternative complexity measures:**

   .. code-block:: yaml

      # Instead of kmer_count, use:
      attributes:
        sequence_complexity:
          target: main_probe
          type: complexity_score

Data Format Issues
------------------

Unexpected output format
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Output CSV has unexpected columns or values.

**Solutions:**

1. **Check probe names match:**

   .. code-block:: yaml

      # Probe names become column names
      probes:
        my_probe:  # Creates column 'my_probe'
          template: "{seq}"

2. **Verify attribute names:**

   .. code-block:: yaml

      attributes:
        probe_gc:     # Creates column 'probe_gc'
          target: my_probe
          type: gc_content

3. **Examine raw output:**

   .. code-block:: bash

      uprobe run -p protocol.yaml -g genomes.yaml --raw
      # Check _raw.csv file for all calculated values

Missing sequences in output
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Some expected probes are missing from results.

**Solutions:**

1. **Check filtering criteria:**

   .. code-block:: yaml

      # Very permissive filters for debugging
      post_process:
        filters:
          anything_goes:
            condition: "True"  # Passes everything

2. **Look for errors in logs:**

   .. code-block:: bash

      uprobe --verbose run -p protocol.yaml -g genomes.yaml 2>&1 | tee log.txt

3. **Check intermediate files:**

   .. code-block:: bash

      ls -la results/
      wc -l results/*.csv  # Count lines in each file

Getting Help
------------

Check Logs
~~~~~~~~~~

Always run with verbose output for troubleshooting:

.. code-block:: bash

   uprobe --verbose run -p protocol.yaml -g genomes.yaml 2>&1 | tee uprobe.log

Minimal Test Case
~~~~~~~~~~~~~~~~~

Create a minimal test to isolate issues:

.. code-block:: yaml

   # minimal_test.yaml
   name: "minimal_test"
   genome: "human_hg38"
   targets: ["GAPDH"]  # Just one target
   
   extracts:
     target_region:
       source: "exon"
       length: 50
       overlap: 10
   
   probes:
     simple:
       expr: "target_region[0:20]"
   
   # No attributes or filters initially

Report Issues
~~~~~~~~~~~~~

When reporting issues, include:

1. **U-Probe version:** ``uprobe version``
2. **Full error message and traceback**
3. **Configuration files (anonymized)**
4. **System information:** OS, Python version
5. **Steps to reproduce**

Where to Get Help
~~~~~~~~~~~~~~~~~

1. **Documentation:** Check this documentation first
2. **GitHub Issues:** `Report bugs <https://github.com/UFISH-Team/U-Probe/issues>`_
3. **GitHub Discussions:** `Ask questions <https://github.com/UFISH-Team/U-Probe/discussions>`_
4. **Examples:** Review working examples in the repository

Common Error Messages
---------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Error Message
     - Solution
   * - "Genome 'X' not found"
     - Check genome name matches genomes.yaml key
   * - "No targets specified"
     - Add targets list to protocol.yaml
   * - "Invalid expression: X"
     - Check probe expression syntax
   * - "Attribute calculation failed"
     - Verify required files and indices exist
   * - "No data to concatenate"
     - Check that previous steps generated output
   * - "YAML parsing error"
     - Check indentation and syntax
   * - "Permission denied"
     - Check file permissions and disk space
   * - "Index not found"
     - Run build-index command first

Prevention Tips
---------------

1. **Start simple:** Begin with basic configurations and add complexity gradually
2. **Validate early:** Use ``validate-targets`` before full runs
3. **Test with subsets:** Use small target lists for initial testing  
4. **Use version control:** Track configuration changes
5. **Document decisions:** Comment your configuration files
6. **Regular backups:** Keep backups of working configurations

Next Steps
----------

If you're still having issues:

1. Review the :doc:`examples` for working configurations
2. Check the :doc:`config_reference` for detailed option descriptions
3. Ask for help on `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_
