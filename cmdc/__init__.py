from . import client  # noqa: F401
from .client import Client  # noqa: F401
import warnings


warnings.warn(FutureWarning(
    """
    The `cmdc` package has been retired and renamed to `covidcountydata`
    
    Please use `pip install covidcountydata` to install
    
    After installing covidcountydata, you can continue to use the same API that existed here
    """
))
