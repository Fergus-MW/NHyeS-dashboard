import pandas as pd

def norm_str(s: pd.Series) -> pd.Series:
    return s.astype('string').str.strip().str.upper()
