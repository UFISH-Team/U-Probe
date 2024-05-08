
import pandas as pd

# Ascending
def sort_n_mapped_genes(res_df: pd.DataFrame,
                        sort_by: str = 'n_mapped_genes',
                        is_ascending: bool = False
                        ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_circle_fold_score(res_df: pd.DataFrame,
                           sort_by: str = 'circle_fold_score',
                           is_ascending: bool = True
                           ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_self_match_circle(res_df: pd.DataFrame,
                        sort_by: str = 'self_match_circle',
                        is_ascending: bool = True
                        ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_amp_fold_score(res_df: pd.DataFrame,
                        sort_by: str = 'amp_fold_score',
                        is_ascending: bool = True
                        ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_self_match_amp(res_df: pd.DataFrame,
                        sort_by: str = 'self_match_amp',
                        is_ascending: bool = True
                        ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_target_blocks(res_df: pd.DataFrame,
                       sort_by: str = 'target_blocks',
                       is_ascending: bool = False
                       ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_target_fold_score(res_df: pd.DataFrame,
                           sort_by: str = 'target_fold_score',
                           is_ascending: bool = True
                           ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df

def sort_tm_region(res_df: pd.DataFrame,
                   sort_by: str = 'tm_region',
                   is_ascending: bool = True
                   ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df


# Descending
def sort_n_trans(res_df: pd.DataFrame,
                 sort_by: str = 'n_trans',
                    is_ascending: bool = False
                    ) -> pd.DataFrame:
    res_df = res_df.sort_values(by=sort_by, ascending=is_ascending, inplace=True)
    res_df = res_df.reset_index(drop=True)
    return res_df