import pytest
import pandas as pd
from pathlib import Path
from uprobe.workflow import parse_yaml
from uprobe.post_process import process

HERE = Path(__file__).parent
path = HERE / "data" / "double_hyb_rca.yaml"
res = parse_yaml(path)

def create_test_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    data = {
        'transcript_name': ['transcript1', 'transcript1', 'transcript2', 'transcript2'],
        'start': [100, 150, 200, 250],
        'end': [120, 170, 220, 260],
        'n_mapped_genes': [5, 3, 4, 2],
        'target_fold_score': [60, 70, 50, 40],
        'circle_fold_score': [75, 85, 80, 70],
        'circle_self_match': [1, 0, 1, 1],
        'amp_fold_score': [65, 75, 55, 45],
        'self_match_amp': [1, 0, 1, 1],
        'target_blocks': [10, 15, 20, 25],
        'tm': [36, 38, 40, 42],
        'n_trans': [1, 0, 1, 1],
        'gc_content': [0.6, 0.5, 0.55, 0.7],
         'circle_probe': ['ATGGGCCCTA', 'ATGGGCCCCC', 'ATGGGCCCTA', 'ATGGGCCCGG'],
    }
    return pd.DataFrame(data)

def test_post_process():
    # Create a sample DataFrame
    df = create_test_dataframe()
    res = parse_yaml(path)

    res = res['post_process']

    # Run post_process with the parsed YAML data
    processed_df = process(df, res)  # Assuming genome is not used in this context

    # Assertions to validate the output
    assert processed_df is not None  # Ensure the result is not None
    assert isinstance(processed_df, pd.DataFrame)  # Ensure the result is a DataFrame
    
    # Check the shape of the DataFrame if you expect a certain number of rows/columns
    assert processed_df.shape[0] <= df.shape[0]  # After filtering, rows should not increase

    assert processed_df.shape[0] == 1  # Assuming filtering n_mapped_genes < 4
    