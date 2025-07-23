
import pandas as pd
from pathlib import Path
from uprobe.workflow import parse_yaml
from uprobe.process import post_process

HERE = Path(__file__).parent
path = HERE / "data" / "double_hyb_rca.yaml"
res = parse_yaml(path)

def create_test_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    data = {
        'transcript_name': ['transcript1', 'transcript1', 'transcript2', 'transcript2'],
        'start': [100, 150, 200, 250],
        'end': [120, 170, 220, 260],
        'n_mapped_genes': [{'g42236': 5}, {'g42179': 3}, {'g42180': 4}, {'g42181': 2}],
        'target_fold_score': [60, 70, 50, 40],
        'circle_fold_score': [75, 85, 80, 70],
        'circle_self_match': [1, 0, 1, 1],
        'amp_fold_score': [65, 95, 55, 45],
        'self_match_amp': [1, 0, 1, 1],
        'target_blocks': [10, 15, 20, 25],
        'tm1': [36, 38, 40, 42],
        'tm2': [36, 38, 40, 42],
        'tm3': [36, 38, 40, 42],
        'n_trans': [1, 0, 1, 1],
        'target_gc_content': [0.6, 0.5, 0.55, 0.7],
         'circle_probe': ['ATGGGCCCTA', 'ATGGGCCCCC', 'ATGGGCCCTA', 'ATGGGCCCGG'],
    }
    return pd.DataFrame(data)

def test_post_process():
    # Create a sample DataFrame
    df = create_test_dataframe()
    config = parse_yaml(path)

    # Execute post-processing on the DataFrame using the configuration
    processed_df = post_process(df, config)

    # Check the resulting DataFrame for expected properties
    assert isinstance(processed_df, pd.DataFrame)
    assert not processed_df.empty
    assert all(processed_df['circle_fold_score'] <= 80)  # Check fold score filter
    assert all(processed_df['amp_fold_score'] <= 80)  # Check amp fold score filter
    assert all(processed_df['tm1'].between(35, 45))  # Check TM filter
    assert all(processed_df['tm2'].between(35, 45))  # Check TM filter
    assert all(processed_df['tm3'].between(35, 45))  # Check TM filter
# Check for unique transcript names after overlap removal

    