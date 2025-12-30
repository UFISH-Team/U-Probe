import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import loguru
import os.path as osp
import yaml
from rich.console import Console

from pantheon.agent import Agent
from pantheon.toolset import ToolSet, tool
from pantheon.team.aat import AgentAsToolTeam
from pantheon.toolsets.python import PythonInterpreterToolSet
from pantheon.toolsets.file_manager import FileManagerToolSet
from pantheon.toolsets.scraper import ScraperToolSet  
from pantheon.toolsets.shell import ShellToolSet     
from pantheon.utils.display import print_agent_message

from uprobe.agent.probeset import UProbeToolSet

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"

# --- Configuration ---
WORK_DIR = Path("/home/qzhang/new/U-Probe/tests/workdir")
OUTPUT_DIR = WORK_DIR / "output"
GENOMES_CONFIG_PATH = Path("/home/qzhang/new/U-Probe/tests/data/genomes.yaml")
WORK_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def main(workdir: str, prompt: str | None = None, log_level: str = "WARNING"):
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level=log_level)
    workpath = osp.abspath(workdir)

    # ==============================================================================
    # Leader
    # ==============================================================================
    LEADER_INSTRUCTIONS = """
    You are the leader agent for the U-Probe System.

    ### Capabilities
    - You can manage a `Panel_Designer` (Analyst/Researcher) and `Probe_Designer` (Builder).
    - You can also check files in the workdir.

    ### Workflow
    1.  Understand Goal: Does the user have data? Or just a biological question?
    2.  Research/Analyze: 
        - If user has data -> ask `Panel_Designer` to analyze it.
        - If user has NO data (e.g., "Design a panel for Lung Cancer") -> ask `Panel_Designer` to **search the web** and propose a gene list based on literature.
    3.  Validate: Ask user to confirm the gene list.
    4.  Execute: Command `Probe_Designer` to design the probes.
        - CRITICAL: When asking `Probe_Designer`, you MUST provide information:
            - Species (Genome)
            - Target List (Genes or Regions, optional sequence input)
            - Type of Probe (DNA or RNA). This helps them generate the correct YAML.
            - Probes constructions. Expected to yaml format.
            - Any other information that is needed to design the probes(attributes, post_process, etc).
    """

    leader = Agent(
        name="Leader",
        model="gpt-5",
        instructions=LEADER_INSTRUCTIONS
    )

    await leader.toolset(FileManagerToolSet("file_manager", path=workpath))

    # ==============================================================================
    # Panel Designer
    # ==============================================================================
    PANEL_DESIGNER_INSTRUCTIONS = """
    You are an analysis expert in Single-Cell and Spatial Omics data analysis.
    You will receive the instruction from the leader agent for different kinds of analysis tasks.

    ### Capabilities
    - You can analyze the data using PythonInterpreterToolSet.
    - You can search the web using ScraperToolSet.
    - You can manage files using FileManagerToolSet.

    # Workflow
    Here is some typical workflows you should follow for some specific analysis tasks.

    ## Workflow for dataset understanding:
    When you get a dataset, you should first check the dataset structure and the metadata by running some python code.
    For single-cell and spatial data:

    1. Understand the basic structure, get the basic information, including:
    - File format: h5ad, mtx, loom, spatialdata, ...etc
    - The number of cell/gene
    - The number of batch/condition ...
    - If the dataset is a spatial data / multi-modal data or not
    - Whether the dataset is already processed or not
    + If yes, what analysis has been performed, for example, PCA, UMAP, clustering, ...etc
    + If yes, the value in the expression matrix is already normalized or not
    - The .obs, .var, .obsm, .uns ... in adata or other equivalent variables in other data formats,
    Try to understand the meaning of each column, and variables by printing the head of the dataframe.

    2. Understand the data quality, and perform the basic preprocessing:
    Check the data quality by running some python code, try to produce some figures to check:
    + The distribution of the total UMI count per cell, gene number detected per cell.
    + The percentage of Mitochondrial genes per cell.
    + ...
    Based on the figures, and the structure of the dataset,
    If the dataset is not already processed, you should perform the basic preprocessing:
    + Filtering out cells with low UMI count, low gene number, high mitochondrial genes percentage, ...etc
    + Normalization: log1p, scale, ...etc
    + Dimensionality reduction: PCA, UMAP, ...etc
    + If the dataset contain different batches:
        - Plot the UMAP of different batches, and observe the differences to see whether there are any batch effects.
        - If there are batch effects, try to use the `harmonypy` package to perform the batch correction.
    + Clustering:
    - Do leiden clustering with different resolutions and draw the UMAP for each resolution
    - observe the umaps, and decide the best resolution
    + Marker gene identification:
    - Identify the differentially expressed genes between different clusters
    + Cell type annotation:
    - Based on the DEGs for each cluster, guess the cell type of each cluster,
        and generate a table for the cell type annotation, including the cell type, confidence score, and the reason.
    - If the dataset is a spatial data, try also combine the spatial distribution of the cells to help with the cell type annotation.
    - Draw the cell type labels on the umap plot.
    + Check marker gene specificity:
    - Draw dotplot/heatmap
    - Observe the figure, and summarize whether the marker gene is specific to the cell type.

    3. Understand different condition / samples
    + If the dataset contains different condition / samples,
    you should perform the analysis for each condition / sample separately.
    + Then you should produce the figures for comparison between different condition / samples.
    For example, a dataset contains 3 timepoints, you should produce:
    - UMAP of different timepoints
    - Barplot showing the number of cells in each timepoint
    - ...
    """
    panel_designer = Agent(
        name="Panel Designer",
        model="gpt-5",
        instructions=PANEL_DESIGNER_INSTRUCTIONS
    )

    await panel_designer.toolset(PythonInterpreterToolSet("python"))
    await panel_designer.toolset(ShellToolSet("shell"))
    await panel_designer.toolset(ScraperToolSet("scraper"))
    await panel_designer.toolset(FileManagerToolSet("file_manager", path=workpath))

    # ==============================================================================
    # Probe Designer
    # ==============================================================================
    PROBE_DESIGNER_INSTRUCTIONS = """
    You are an expert in probe design for all kinds of FISH probe design tasks.
    You will receive the instruction from the leader agent for different kinds of probe design tasks.
    Here is the typical workflow you should follow for probe design tasks.

    ### Workflow for probe design:
    1. extract the information from the goal:
     - get the species or genome, it corresponds to the genomes.yaml file. Such as hg19, mouse
     - target list, it can be a list of genes(RNA) or regions(DNA), or a sequence.
     - type of probe, it can be DNA or RNA.
     - extracts: An dictionary to customize extraction parameters.
                      For example: {"source": "genome", "length": 80, "overlap": 10}.
                      'source' can be one of ['genome', 'exon', 'CDS', 'UTR'].
        if source is 'genome', the probe type is DNA, otherwise it is RNA.
     - probes constructions. Expected to yaml format.
     - attributes, optional. It is the attributes of the probes, such as gc content, melting temperature, etc.
     - post_process, optional. It is the post_process of the probes, such as filter the probes based on the attributes.
     - summary, optional. It is the summary of the probes, such as the report name, the attributes to report.
    2. design the probes:
    - call the `design_probe` tool to design the probes.
    - the `design_probe` tool will return html report (contain csv data) and the probes yaml file.
    """
    probe_designer = Agent(
        name="Probe Designer",
        model="gpt-5",
        instructions=PROBE_DESIGNER_INSTRUCTIONS
    )

    await probe_designer.toolset(UProbeToolSet("design_probe"))
    await probe_designer.toolset(FileManagerToolSet("file_manager", path=workpath))

    # ==============================================================================
    # Team
    # ==============================================================================
    team = AgentAsToolTeam(leader, [panel_designer, probe_designer])

    console = Console()

    if prompt is None:
        prompt_path = osp.join(workpath, "prompt.md")
        try:
            with open(prompt_path, "r") as f:
                prompt = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    await team.run(prompt)
  
if __name__ == "__main__":
    asyncio.run(main(workdir=WORK_DIR, prompt=None, log_level="WARNING"))