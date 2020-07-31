import os

import pytest

import covidcountydata as ccd


@pytest.fixture(scope="session")
def client():
    return ccd.Client(apikey=os.environ.get("CCD_API_KEY", None))
