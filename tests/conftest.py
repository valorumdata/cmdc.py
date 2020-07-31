import os

import pytest

import ccd


@pytest.fixture(scope="session")
def client():
    return ccd.Client(apikey=os.environ.get("CCD_API_KEY", None))
