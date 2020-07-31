import urllib.parse
from typing import Any, Dict, List

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.covidcountydata.org"


def setup_session() -> requests.Session:
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=0.2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http


def create_filter_rhs(x: Any) -> str:
    inequalities = {">": "gt", "<": "lt", "!=": "neq"}
    if isinstance(x, (list, tuple, set)):
        # use in
        return f"in.({','.join(map(str, x))})"

    if isinstance(x, str):
        # check for inequality
        for op in inequalities:
            if op in x:
                if f"{op}=" in x:
                    return x.replace(f"{op}=", inequalities[op] + "e.")
                return x.replace(op, inequalities[op] + ".")
    return f"eq.{x}"


def _reshape_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape a DataFrame from long to wide form, adhering to the following
    rules:

    - If the `meta_date` column exists, replace `variable` column with
      {variable}_{meta_date} and then drop `meta_date`
    - Construct a pivot_table where the columns come from the `variable`
      column, values come from the `value` column, and all other columns are
      used as an index
    """
    if df.shape[0] == 0:
        # empty dataframe
        return df

    cols = list(df)
    for c in ["variable", "value"]:
        if c not in cols:
            gh_issues = (
                "https://github.com/CovidCountyData/covidcountydata.py/issues/new"
            )
            msg = (
                f"Column {c} not found in DataFrame. "
                f"Please report a bug at {gh_issues}"
            )
            raise ValueError(msg)
    if "meta_date" in cols:
        if "variable" in cols:
            df["variable"] = (
                df["variable"].astype(str) + "_" + df["meta_date"].astype(str)
            )
            df.drop("meta_date", axis="columns")

    idx = list(set(cols) - {"variable", "value"})
    return df.pivot_table(index=idx, columns="variable", values="value").reset_index()


def _create_query_string(path: str, filters: Dict[str, Any]) -> str:
    """
    Given a path and filters to apply to that path, construct a query string
    """
    prepped_filters = {k: create_filter_rhs(v) for k, v in filters.items()}
    query = BASE_URL + "/" + path
    if len(prepped_filters) > 0:
        query += "?" + urllib.parse.urlencode(prepped_filters)

    return query


def _combine_dfs(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge all `dfs` on common columns (typically in the index)
    """
    out = dfs[0]
    for right in dfs[1:]:
        out = out.merge(right)
    return out
