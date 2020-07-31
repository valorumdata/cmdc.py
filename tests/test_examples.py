import inspect

import pandas as pd
import pytest

import covidcountydata.examples


@pytest.mark.parametrize(
    "func", [x[1] for x in inspect.getmembers(covidcountydata.examples, inspect.isfunction)]
)
def test_examples(client, func):
    df = func(client)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] > 0
