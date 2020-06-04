import pathlib
import urllib
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import requests
import us
from email_validator import EmailNotValidError, validate_email
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.covid.valorum.ai"


class NetworkError(Exception):
    def __init__(self, res: requests.Response, msg: str):
        full_msg = (
            msg + f"\n\nRequest failed with code {res.status_code} "
            f"and content {res.content}"
        )
        super().__init__(full_msg)


class Endpoint:
    def __init__(self, client: "Client", path: str, parameters: List[Dict[str, List]]):
        """
        Create a Endpoint builder object

        Parameters
        ----------
        client: Client
            The API Client that should be returned after calling an instance of
            this class
        path: string
            The API path for which the Endpoint will be built
        parameters: List[Dict[str, List]]
            A list of OpenAPI 2.0 parameters for this endpoint
        """
        self.path = path
        self.client = client
        self.parameters = parameters
        self.valid_filters = []
        for p in parameters:
            if isinstance(p, dict) and len(p) == 1 and "$ref" in p:
                # look up parameter
                param = list(p.values())[0]
                prefix = "#/parameters/"
                assert param.startswith(prefix)

                self.valid_filters.append(
                    client._spec["parameters"][param.replace(prefix, "")]
                )

        self.filter_names = [x["name"] for x in self.valid_filters]

    def has_filter(self, param: str) -> bool:
        """
        Check if `param` is a valid parameter for this endpoint
        """
        return param in self.filter_names

    def __call__(self, state=None, **filters) -> "Client":
        """
        Validate a given set of query parameters and confirm they are applicable
        for this endpoint
        """
        if state is not None and self.has_filter("fips"):
            if "fips" in filters:
                msg = f"Both state {state} and fips {filters['fips']} were passed."
                msg += " Only one may be applied at a time"
                raise ValueError(msg)

            filters["fips"] = self.client.fips_in_states(state)

        # process filters
        for name in filters:
            # TODO: add validation of parameter type
            if not self.has_filter(name):
                msg = (
                    f"{self.path} path given filter {name}. "
                    f"Valid filters are {', '.join(self.filter_names)}"
                )
                raise ValueError(msg)

        self.client.add_request(self.path, filters)

        return self.client

    def __repr__(self) -> str:
        filter_names = [x["name"] for x in self.valid_filters]
        description = self.client._spec["paths"]["/" + self.path]["get"]["description"]
        msg = (
            f"Request builder for {self.path} endpoint"
            f"\nValid filters are {', '.join(filter_names)}"
            f"\n\n\n{description}"
        )
        return msg

    @property
    def __doc__(self):
        return self.__repr__()


def create_filter_rhs(x: Any) -> str:
    ineqs = {">": "gt", "<": "lt", "!=": "neq"}
    if isinstance(x, (list, tuple, set)):
        # use in
        return f"in.({','.join(map(str, x))})"

    if isinstance(x, str):
        # check for inequality
        for op in ineqs:
            if op in x:
                if f"{op}=" in x:
                    return x.replace(f"{op}=", ineqs[op] + "e.")
                return x.replace(op, ineqs[op] + ".")
    return f"eq.{x}"


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


class Client:
    def __init__(self, apikey: Optional[str] = None):
        """
        API Client for the CMDC database

        Parameters
        ----------
        apikey : str (Optional)
            The API key to access the system. This is an optional
            argument and `Client` can create one for you through
            the `register` method.

        Examples
        --------

        Construct a client:

        ```python
        >>> c = Client()
        ```

        Use the client to request an API key (will be prompted for email address)

        ```ipython
        c.register()
        ```

        Build a dataset for Orange County, Florida:

        ```ipython
        # TODO: implement these docs
        ```

        """
        self._current_request: Dict[Dict[str, Any]] = {}
        self.sess = setup_session()
        self._set_key(apikey)
        self._counties = None
        res = self.sess.get(BASE_URL + "/swagger.json")
        if not res.ok:
            msg = "Could not request the API structure. Please try again!"
            raise NetworkError(res, msg)
        self._spec = res.json()

        if self.key is None:
            msg = (
                "No API key found. Please request a "
                "free API key by calling the `register` method"
            )
            print(msg)

    ## county/state map
    @property
    def counties(self):
        if self._counties is None:
            # fetch
            res = self.sess.get(BASE_URL + "/counties")
            if not res.ok:
                raise ValueError("Failed to get list of counties")

            self._counties = pd.DataFrame(res.json())
            self._counties["state"] = (
                self._counties["fips"].astype(str).str.zfill(5).str[:2].astype(int)
            )

        return self._counties

    def fips_in_states(self, states: Union[List[int], int]):
        if isinstance(states, (int, str)):
            states = [states]
        states = [int(us.states.lookup(str(x).zfill(2)).fips) for x in states]
        fips = self.counties.query("state in @states")["fips"].unique()
        return sorted(list(fips)) + states

    ## API key handling
    @property
    def key(self):
        # already loaded -- return
        if self._key is not None:
            return self._key

        # try to load
        keyfile = self._keypath
        if not keyfile.is_file():
            return None
        with open(keyfile, "r") as f:
            self.key = f.read()

        return self._key

    def _set_key(self, x):
        if x is not None:
            self.sess.headers.update({"apikey": x})
        self._key = x

    @key.setter
    def key(self, x):
        return self._set_key(x)

    def register(self, email: Optional[str] = None) -> str:
        if email is None:
            msg = "Please provide an email address to request a free API key: "
            email = input(msg)

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            raise e

        res = requests.post(BASE_URL + "/auth", data=dict(email=email))

        if not res.ok:
            raise NetworkError(res, "Could not request api key.")

        key = res.json()["key"]
        self.key = key
        with open(self._keypath, "w") as f:
            f.write(key)
        print("The API key has been saved and will be used in future sessions")

        return self.key

    @property
    def _keypath(self):
        """
        Path to the file with the user's apikey. Makes sure parent directory
        exists
        """
        home = pathlib.Path.home()
        keyfile = home / ".cmdc" / "apikey"
        keyfile.parent.mkdir(parents=True, exist_ok=True)
        return keyfile

    ## Requests
    def _unionize_filters(self) -> Dict[str, Dict[str, str]]:
        """
        Process filters built up in request. Rules are:

        - If the name of the filter is `variable` it is applied request by
          request. Thus different endpoints can have different values for the
          `variables` filter
        - If the name of the filter is anything else (e.g. vintage, fips, dt,
          meta_date), it is applied to ALL requests

        While processing the common filters, if the value passed in any two
        parts of the request builder are not the same, a ValueError will be
        thrown. For example,

        ```ipython
        c = Client()
        c.economics(fips=12095).demographics(fips=4013)
        c._unionize_filters()
        ```

        Would be an error

        The return value is a dictionary mapping query paths to the filters
        that apply to that request
        """
        common_filters: Dict[str, str] = {}
        out: Dict[str, Dict[str, str]] = {}
        # for each request
        for path, filts in self._current_request.items():
            out[path] = {}

            # for each filter in this request
            for filt_name, filt_val in filts.items():
                # if the filter is for `variable` pass it through directly and
                # do not add it to common_filters
                if filt_name == "variable":
                    out[path][filt_name] = filt_val

                    continue

                # if we have seen this filter, check to make sure we don't have
                # conflicting values
                if filt_name in common_filters:
                    current = common_filters[filt_name]
                    if current != filt_val:
                        msg = (
                            "Found conflicting values for common "
                            f"filter {filt_name}. "
                            f"Found both {filt_val} and {current}"
                        )
                        raise ValueError(msg)
                else:
                    # add this value to the common_filters tracker
                    common_filters[filt_name] = filt_val

        # for each request, add in common filters that apply
        for path in out:
            for filt_name, filt_val in common_filters.items():
                if self.__getattr__(path).has_filter(filt_name):
                    out[path][filt_name] = filt_val

        return out

    def _create_query_string(self, path: str, filters: Dict[str, Any]) -> str:
        """
        Given a path and filters to apply to that path, construct a query string
        """
        prepped_filters = {k: create_filter_rhs(v) for k, v in filters.items()}
        query = BASE_URL + "/" + path
        if len(prepped_filters) > 0:
            query += "?" + urllib.parse.urlencode(prepped_filters)

        return query

    def _url_to_df(self, url: str) -> pd.DataFrame:
        "Make GET request to `url` and parse resulting JSON as DataFrame"
        res = self.sess.get(url)
        if not res.ok:
            raise NetworkError(res, f"Error fetching data from {url}")
        df = pd.DataFrame(res.json())
        for col in ["dt", "meta_date", "vintage"]:
            if col in list(df):
                df[col] = pd.to_datetime(df[col])

        return df

    def _reshape_df(self, df: pd.DataFrame) -> pd.DataFrame:
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
                gh_issues = "https://github.com/valorumdata/cmdc.py/issues/new"
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

        idx = list(set(cols) - set(["variable", "value"]))
        return df.pivot_table(
            index=idx, columns="variable", values="value"
        ).reset_index()

    def _run_queries(self, urls: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """
        Transform a dict mapping paths to request urls, to a dict mapping paths
        to DataFrames with the result of GETting the url
        """
        # TODO: optimize and make async
        return {k: self._url_to_df(v) for k, v in urls.items()}

    def _combine_dfs(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge all `dfs` on common columns (typically in the index)
        """
        out = dfs[0]
        for right in dfs[1:]:
            out = out.merge(right)
        return out

    def fetch(self) -> pd.DataFrame:
        if len(self._current_request) == 0:
            print("You have no requests built up! Try adding a dataset")
            return None
        filters = self._unionize_filters()
        query_strings = {k: self._create_query_string(k, v) for k, v in filters.items()}
        dfs = self._run_queries(query_strings)
        wide_dfs = [self._reshape_df(v) for v in dfs.values()]
        output = self._combine_dfs(wide_dfs)

        self.reset()

        return output

    ## Dynamic query builder
    def __getattr__(self, ds: str) -> Endpoint:
        if ds not in dir(self):
            msg = f"Unknown dataset {ds}. Known datasets are {dir(self)}"
            raise ValueError(msg)

        route = self._spec["paths"]["/" + ds]["get"]
        return Endpoint(self, ds, route["parameters"])

    def __dir__(self) -> List[str]:
        paths = self._spec["paths"]
        return [x.strip("/") for x in paths if x != "/"]

    @property
    def datasets(self):
        return self.__dir__()

    def __repr__(self) -> str:
        out = "CMDC Client"

        if len(self._current_request) > 0:
            out += ". Current request:\n  -"
            req_desc = [f"{k}: {v}" for k, v in self._current_request.items()]
            out += "\n  -".join(req_desc)

        return out

    def add_request(self, path: str, filters: Dict[str, Any]) -> None:
        self._current_request.update({path: filters})

    def reset(self):
        """
        Reset the current query builder.
        """
        self._current_request = {}
        return self
