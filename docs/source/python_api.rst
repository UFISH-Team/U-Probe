Python API Guide
================

U-Probe provides a clean Python API for programmatic access and integration into other bioinformatics pipelines. This guide covers how to use U-Probe from Python scripts and notebooks.

Overview
--------

The U-Probe Python API is built around the :class:`uprobe.UProbeAPI` class, which provides methods for each step of the probe design workflow. This allows you to:

- Integrate U-Probe into existing Python pipelines
- Customize the workflow programmatically
- Process results using pandas DataFrames
- Build interactive applications and notebooks

Quick Start
-----------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from uprobe import UProbeAPI

   # Initialize the API
   uprobe = UProbeAPI(
       protocol_config=Path("protocol.yaml"),
       genomes_config=Path("genomes.yaml"),
       output_dir=Path("results")
   )

   # Run the complete workflow
   probes_df = uprobe.run_workflow(
       raw_csv=True,
       continue_on_invalid_targets=False,
       threads=10
   )

   # Access the results
   print(f"Generated {len(probes_df)} probes")
   print(probes_df.head())

Step-by-Step Workflow
~~~~~~~~~~~~~~~~~~~~~

For more control over the process:

.. code-block:: python

   import pandas as pd
   from pathlib import Path
   from uprobe import UProbeAPI

   # Initialize
   uprobe = UProbeAPI(
       protocol_config=Path("protocol.yaml"),
       genomes_config=Path("genomes.yaml"), 
       output_dir=Path("results")
   )

   # Step 1: Build genome index
   uprobe.build_genome_index(threads=10)

   # Step 2: Validate targets
   if not uprobe.validate_targets(continue_on_invalid=False):
       print("Target validation failed")
       exit(1)

   # Step 3: Generate target sequences
   df_targets = uprobe.generate_target_seqs()
   if df_targets.empty:
       print("No target sequences generated")
       exit(1)

   # Step 4: Construct probes
   df_probes = uprobe.construct_probes(df_targets)
   if df_probes.empty:
       print("No probes constructed")
       exit(1)

   # Step 5: Combine data
   df_combined = pd.concat([
       df_targets.reset_index(drop=True),
       df_probes.reset_index(drop=True)
   ], axis=1)

   # Step 6: Post-process (add attributes and filter)
   df_final = uprobe.post_process_probes(df_combined, raw_csv=True)
   print(f"Final probes: {len(df_final)}")

   # Step 7: Generate barcodes (optional)
   barcodes = uprobe.generate_barcodes()

API Reference
-------------

UProbeAPI Class
~~~~~~~~~~~~~~~

.. currentmodule:: uprobe

.. autoclass:: UProbeAPI
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Handling
~~~~~~~~~~~~~~~~~~~~~~~

The API accepts configuration in multiple formats:

**From Files:**

.. code-block:: python

   uprobe = UProbeAPI(
       protocol_config=Path("protocol.yaml"),
       genomes_config=Path("genomes.yaml"),
       output_dir=Path("results")
   )

**From Dictionaries:**

.. code-block:: python

   protocol_dict = {
       'name': 'MyExperiment',
       'genome': 'human_hg38',
       'targets': ['GAPDH', 'ACTB'],
       # ... rest of protocol
   }

   genomes_dict = {
       'human_hg38': {
           'fasta': '/path/to/genome.fa',
           'gtf': '/path/to/annotation.gtf',
           'align_index': ['bowtie2', 'blast']
       }
   }

   uprobe = UProbeAPI(
       protocol_config=protocol_dict,
       genomes_config=genomes_dict,
       output_dir=Path("results")
   )

Working with Results
--------------------

DataFrame Structure
~~~~~~~~~~~~~~~~~~~

U-Probe returns results as pandas DataFrames with the following structure:

**Target Sequences DataFrame:**

.. code-block:: python

   df_targets = uprobe.generate_target_seqs()
   print(df_targets.columns)
   # ['gene_name', 'gene_id', 'target_region', 'chromosome', 'start', 'end', 'strand']

**Probe DataFrame:**

.. code-block:: python

   df_probes = uprobe.construct_probes(df_targets)  
   print(df_probes.columns)
   # ['probe_1', 'probe_2', ...]  # Depends on probe configuration

**Final DataFrame:**

.. code-block:: python

   df_final = uprobe.post_process_probes(df_combined)
   print(df_final.columns)
   # ['gene_name', 'target_region', 'probe_1', 'gc_content', 'melting_temp', ...]

Data Analysis and Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import matplotlib.pyplot as plt
   import seaborn as sns

   # Basic statistics
   print(df_final.describe())

   # GC content distribution
   plt.figure(figsize=(10, 6))
   plt.hist(df_final['gc_content'], bins=30, alpha=0.7)
   plt.xlabel('GC Content')
   plt.ylabel('Frequency')
   plt.title('GC Content Distribution of Probes')
   plt.show()

   # Melting temperature vs GC content
   plt.figure(figsize=(10, 6))
   plt.scatter(df_final['gc_content'], df_final['melting_temp'], alpha=0.6)
   plt.xlabel('GC Content')
   plt.ylabel('Melting Temperature (°C)')
   plt.title('Melting Temperature vs GC Content')
   plt.show()

   # Probes per gene
   gene_counts = df_final['gene_name'].value_counts()
   plt.figure(figsize=(12, 6))
   gene_counts.plot(kind='bar')
   plt.title('Number of Probes per Gene')
   plt.xlabel('Gene')
   plt.ylabel('Number of Probes')
   plt.xticks(rotation=45)
   plt.tight_layout()
   plt.show()

Custom Filtering and Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom filtering beyond protocol filters
   high_quality_probes = df_final[
       (df_final['gc_content'] >= 0.45) &
       (df_final['gc_content'] <= 0.55) &
       (df_final['melting_temp'] >= 55) &
       (df_final['melting_temp'] <= 65) &
       (df_final['self_match'] < 0.8)
   ]

   # Select best probes per gene
   best_probes = (df_final
                  .sort_values(['gene_name', 'melting_temp'])
                  .groupby('gene_name')
                  .head(5)  # Top 5 probes per gene
                  )

   # Export filtered results
   high_quality_probes.to_csv('high_quality_probes.csv', index=False)
   best_probes.to_csv('best_probes.csv', index=False)

Advanced Usage
--------------

Dynamic Configuration
~~~~~~~~~~~~~~~~~~~~~

Build configurations programmatically:

.. code-block:: python

   def create_fish_protocol(genes, experiment_name):
       """Create a FISH protocol configuration for given genes."""
       
       # Generate barcodes for each gene
       barcodes = {}
       for i, gene in enumerate(genes):
           # Simple barcode generation (use real barcode design in practice)
           barcodes[gene] = {'BC1': 'A' * 16 if i % 2 == 0 else 'T' * 16}
       
       protocol = {
           'name': experiment_name,
           'genome': 'human_hg38',
           'targets': genes,
           'extracts': {
               'target_region': {
                   'source': 'exon',
                   'length': 120,
                   'overlap': 20
               }
           },
           'probes': {
               'fish_probe': {
                   'template': '{binding}{spacer}{barcode}',
                   'parts': {
                       'binding': {
                           'length': 30,
                           'expr': 'rc(target_region[0:30])'
                       },
                       'spacer': {
                           'expr': "'TTTTTT'"
                       },
                       'barcode': {
                           'expr': "encoding[gene_name]['BC1']"
                       }
                   }
               }
           },
           'encoding': barcodes,
           'attributes': {
               'gc_content': {'target': 'fish_probe', 'type': 'gc_content'},
               'melting_temp': {'target': 'fish_probe', 'type': 'annealing_temperature'}
           },
           'post_process': {
               'filters': {
                   'gc_content': {'condition': 'gc_content >= 0.4 & gc_content <= 0.6'},
                   'melting_temp': {'condition': 'melting_temp >= 50 & melting_temp <= 65'}
               }
           }
       }
       
       return protocol

   # Use the function
   genes = ['GAPDH', 'ACTB', 'TP53']
   protocol = create_fish_protocol(genes, 'AutoGenerated_FISH')

   # Run with generated protocol
   uprobe = UProbeAPI(
       protocol_config=protocol,
       genomes_config=Path('genomes.yaml'),
       output_dir=Path('results')
   )

Batch Processing
~~~~~~~~~~~~~~~~

Process multiple experiments:

.. code-block:: python

   import os
   from pathlib import Path

   def batch_process_protocols(protocol_dir, genomes_file, base_output_dir):
       """Process multiple protocol files in batch."""
       
       results = {}
       protocol_dir = Path(protocol_dir)
       base_output_dir = Path(base_output_dir)
       
       for protocol_file in protocol_dir.glob('*.yaml'):
           print(f"Processing {protocol_file.name}...")
           
           # Create output directory for this experiment
           output_dir = base_output_dir / protocol_file.stem
           output_dir.mkdir(parents=True, exist_ok=True)
           
           try:
               # Initialize API
               uprobe = UProbeAPI(
                   protocol_config=protocol_file,
                   genomes_config=Path(genomes_file),
                   output_dir=output_dir
               )
               
               # Run workflow
               df_results = uprobe.run_workflow(raw_csv=True, threads=8)
               
               # Store results
               results[protocol_file.stem] = {
                   'success': True,
                   'num_probes': len(df_results),
                   'output_dir': output_dir,
                   'dataframe': df_results
               }
               
               print(f"✓ {protocol_file.stem}: {len(df_results)} probes generated")
               
           except Exception as e:
               results[protocol_file.stem] = {
                   'success': False,
                   'error': str(e),
                   'output_dir': output_dir
               }
               print(f"✗ {protocol_file.stem}: Failed - {e}")
       
       return results

   # Usage
   results = batch_process_protocols('protocols/', 'genomes.yaml', 'batch_results/')

   # Summary
   successful = sum(1 for r in results.values() if r['success'])
   total = len(results)
   print(f"\nBatch processing complete: {successful}/{total} successful")

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Use multiprocessing for large datasets:

.. code-block:: python

   from multiprocessing import Pool
   from functools import partial

   def process_gene_subset(gene_subset, protocol_template, genomes_config):
       """Process a subset of genes."""
       
       # Create protocol for this subset
       protocol = protocol_template.copy()
       protocol['targets'] = gene_subset
       protocol['name'] = f"Subset_{hash(tuple(gene_subset))}"
       
       # Process
       output_dir = Path(f"results/subset_{hash(tuple(gene_subset))}")
       uprobe = UProbeAPI(protocol, genomes_config, output_dir)
       return uprobe.run_workflow()

   def parallel_gene_processing(all_genes, protocol_template, genomes_config, batch_size=10):
       """Process genes in parallel batches."""
       
       # Split genes into batches
       gene_batches = [all_genes[i:i+batch_size] for i in range(0, len(all_genes), batch_size)]
       
       # Create partial function with fixed arguments
       process_func = partial(
           process_gene_subset,
           protocol_template=protocol_template,
           genomes_config=genomes_config
       )
       
       # Process in parallel
       with Pool() as pool:
           results = pool.map(process_func, gene_batches)
       
       # Combine results
       combined_df = pd.concat(results, ignore_index=True)
       return combined_df

Error Handling
--------------

Robust Error Handling
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from uprobe import UProbeAPI
   import logging

   def robust_probe_design(protocol_path, genomes_path, output_path):
       """Probe design with comprehensive error handling."""
       
       try:
           # Initialize
           uprobe = UProbeAPI(protocol_path, genomes_path, output_path)
           
           # Validate targets first
           if not uprobe.validate_targets(continue_on_invalid=True):
               logging.warning("Some targets are invalid, continuing with valid ones")
           
           # Generate targets
           df_targets = uprobe.generate_target_seqs()
           if df_targets.empty:
               raise ValueError("No target sequences could be generated")
           
           logging.info(f"Generated {len(df_targets)} target sequences")
           
           # Construct probes
           df_probes = uprobe.construct_probes(df_targets)
           if df_probes.empty:
               raise ValueError("No probes could be constructed")
           
           logging.info(f"Constructed {len(df_probes)} initial probes")
           
           # Post-process
           df_combined = pd.concat([df_targets.reset_index(drop=True), 
                                    df_probes.reset_index(drop=True)], axis=1)
           df_final = uprobe.post_process_probes(df_combined, raw_csv=True)
           
           if df_final.empty:
               logging.warning("No probes passed quality filters")
           else:
               logging.info(f"Final result: {len(df_final)} high-quality probes")
           
           return df_final
           
       except FileNotFoundError as e:
           logging.error(f"File not found: {e}")
           return None
       except ValueError as e:
           logging.error(f"Value error: {e}")
           return None
       except Exception as e:
           logging.error(f"Unexpected error: {e}")
           return None

Integration Examples
--------------------

Jupyter Notebook Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # In a Jupyter notebook
   %matplotlib inline
   import pandas as pd
   import matplotlib.pyplot as plt
   from uprobe import UProbeAPI

   # Interactive probe design
   uprobe = UProbeAPI("protocol.yaml", "genomes.yaml", "results")
   df_results = uprobe.run_workflow(raw_csv=True)

   # Interactive visualization
   fig, axes = plt.subplots(2, 2, figsize=(15, 10))
   
   # GC content histogram
   axes[0,0].hist(df_results['gc_content'], bins=20, alpha=0.7)
   axes[0,0].set_title('GC Content Distribution')
   
   # Melting temperature histogram  
   axes[0,1].hist(df_results['melting_temp'], bins=20, alpha=0.7)
   axes[0,1].set_title('Melting Temperature Distribution')
   
   # Scatter plot
   axes[1,0].scatter(df_results['gc_content'], df_results['melting_temp'])
   axes[1,0].set_xlabel('GC Content')
   axes[1,0].set_ylabel('Melting Temperature')
   
   # Probes per gene
   gene_counts = df_results['gene_name'].value_counts()
   axes[1,1].bar(range(len(gene_counts)), gene_counts.values)
   axes[1,1].set_xticks(range(len(gene_counts)))
   axes[1,1].set_xticklabels(gene_counts.index, rotation=45)
   axes[1,1].set_title('Probes per Gene')
   
   plt.tight_layout()
   plt.show()

Flask Web Application
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import Flask, request, jsonify, render_template
   from uprobe import UProbeAPI
   import tempfile
   import yaml

   app = Flask(__name__)

   @app.route('/')
   def index():
       return render_template('index.html')

   @app.route('/api/design_probes', methods=['POST'])
   def design_probes():
       try:
           # Get configuration from request
           protocol_config = request.json['protocol']
           genomes_config = request.json['genomes']
           
           # Create temporary output directory
           with tempfile.TemporaryDirectory() as temp_dir:
               uprobe = UProbeAPI(
                   protocol_config=protocol_config,
                   genomes_config=genomes_config,
                   output_dir=temp_dir
               )
               
               # Run workflow
               df_results = uprobe.run_workflow()
               
               # Convert to JSON
               results = df_results.to_dict('records')
               
               return jsonify({
                   'success': True,
                   'num_probes': len(results),
                   'probes': results
               })
               
       except Exception as e:
           return jsonify({
               'success': False,
               'error': str(e)
           }), 400

   if __name__ == '__main__':
       app.run(debug=True)

Best Practices
--------------

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # For large datasets, process in chunks
   def process_large_dataset(genes, chunk_size=100):
       all_results = []
       
       for i in range(0, len(genes), chunk_size):
           chunk = genes[i:i+chunk_size]
           
           # Process chunk
           protocol = create_protocol_for_genes(chunk)
           uprobe = UProbeAPI(protocol, genomes_config, output_dir)
           chunk_results = uprobe.run_workflow()
           
           all_results.append(chunk_results)
           
           # Clear memory if needed
           del uprobe, chunk_results
           
       return pd.concat(all_results, ignore_index=True)

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_protocol(protocol_dict):
       """Validate protocol configuration before running."""
       
       required_keys = ['name', 'genome', 'targets', 'extracts', 'probes']
       for key in required_keys:
           if key not in protocol_dict:
               raise ValueError(f"Missing required key: {key}")
       
       if not isinstance(protocol_dict['targets'], list):
           raise ValueError("Targets must be a list")
       
       if len(protocol_dict['targets']) == 0:
           raise ValueError("At least one target must be specified")
       
       # Add more validation as needed
       return True

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging

   # Configure logging for U-Probe
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('uprobe.log'),
           logging.StreamHandler()
       ]
   )

   # Now U-Probe will log to both file and console
   uprobe = UProbeAPI(protocol_config, genomes_config, output_dir)
   results = uprobe.run_workflow()

Next Steps
----------

Now that you understand the Python API:

1. Explore :doc:`examples` for real-world use cases
2. Check :doc:`workflows` for common patterns  
3. Review the complete :doc:`api_reference`
4. Learn about :doc:`troubleshooting` for common issues

.. note::
   The Python API provides the same functionality as the CLI but with more flexibility for custom workflows and integration. Use the API when you need programmatic control or want to build applications on top of U-Probe.
