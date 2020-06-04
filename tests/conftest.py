import os

import pytest

import cmdc


@pytest.fixture(scope="session")
def client():
    return cmdc.Client(apikey=os.environ.get("CMDC_API_KEY", None))
