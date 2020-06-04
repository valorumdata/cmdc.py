import inspect
import os

import pandas as pd
import pytest

import cmdc.examples


@pytest.fixture(scope="session")
def client():
    return cmdc.Client(apikey=os.environ.get("CMDC_API_KEY", None))


@pytest.mark.parametrize(
    "func", [x[1] for x in inspect.getmembers(cmdc.examples, inspect.isfunction)]
)
def test_examples(client, func):
    df = func(client)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] > 0
