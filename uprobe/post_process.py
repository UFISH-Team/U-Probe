import pandas as pd


def sort_table(df: pd.DataFrame, keys: list) -> pd.DataFrame:
    """
    Sort the table by the specified columns in the protocol.
    """
    return df.sort_values(by=keys)


def post_process(df: pd.DataFrame, protocol: dict, genome: dict) -> pd.DataFrame:
    """
    Post-process the data frame according to the protocol.
    """
    processes = protocol['post_process']
    for process in processes:
        if isinstance(process, dict):
            if 'sort' in process:
                keys = process['sort']
                df = sort_table(df, keys)
        else:
            if process == "remove_overlap":
                # TODO
                print("Remove overlap")
    return df
