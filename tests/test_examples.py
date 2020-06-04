import inspect

import pandas as pd
import pytest

import cmdc.examples


@pytest.mark.parametrize(
    "func", [x[1] for x in inspect.getmembers(cmdc.examples, inspect.isfunction)]
)
def test_examples(client, func):
    df = func(client)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] > 0
