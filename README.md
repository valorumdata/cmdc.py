# covidcountydata.py

`covidcountydata` is a Python client for accessing the Covid County Data database

Links:

- [Repository](https://github.com/CovidCountyData/covidcountydata.py)
- [Website](https://covidcountydata.org/)

## Covid County Data

The Covid County Data (CCD) project is funded by [Schmidt Futures](https://schmidtfutures.com/) and seeks to simplify the data ingestion process for researchers and policy makers who are working to enact and understand COVID-19 related policies. We accomplish this goal in several ways:

- Collect unique, hard-to-acquire, datasets that are not widely distributed
- Aggregate data collected by other related organizations into a centralized database
- Work with other related organizations to expand and improve their data collection processes
- Build tools, such as this library and the [Julia](https://github.com/CovidCountyData/CovidCountyData.jl) and [R](https://github.com/CovidCountyData/covidcountydataR), to simplify the data ingestion process

More information about our project and what data is collected can be found on our [website](https://covidcountydata.org/).

We are always looking to hear from both those who would like to help us build CCD and those who would like use CCD. [Please reach out to us](https://covidcountydata.org/contact)!

## Installation

This package is available on the [Python Package Index (pypi)](https://pypi.org/project/covidcountydata/) and can be installed by

```bash
pip install covidcountydata
```


## Datasets

You can always find the available datasets in the client object by writing:

```python3
# NOTE: we assume you have aliased the covidcountydata import as
#       ccd in future code examples
import covidcountydata as ccd

c = ccd.Client()
print(c.datasets)
```

You can also find documentation for these datasets [online](https://covidcountydata.org/data-api). This documentation will include more detailed information about the variables included in a particular dataset, where the data comes from, and any caveats that you should be aware of. We encourage you to read about the data you use to ensure that it is appropriate for your intended analysis -- A failure to understand the data you work with guarantees the failure of any subsequent analysis.


### Data keys

All of the data in our database is indexed by one or more common "keys". These keys are:

- `vintage`: The date and time that the data was downloaded into our database. We collect this because of the rapidly eveolving nature of the data and it is important to have a record of when data was changed/corrected/updated.
- `dt`: The date and time that an observation corresponds to. For series like COVID tests administered this may a daily frequency, but, for others like unemployment it may be a weekly or monthly frequency.
- `fips`: The Federal Information Processing Standards number which is used to represent the state/county.
- `meta_date`: For infrequently observed and slow moving data sets, such as demographics, we use the `meta_date` column rather than `dt` because we will associate the values from the `meta_date` with many values of `dt`.

Whenever two series with common keys are loaded together, they will be merged on their common keys.

## API Keys

The CCD data is publicly available and free of charge. We intend to keep it that way.

We do have an API key system for a few reasons:

1. To understand usage patterns that might help us prioritize work going forward
2. To understand the breadth of our user base. We want to make sure we are as helpful to as many groups as possible and keeping a rough idea of how many groups there are is a good benchmark!

The CCD library can automatically handle API keys for you.

If opt in to using an API key, please run the `register` method on the client as shown below:

```python3
c = ccd.Client()
c.register()
```

You will be prompted for your email address. After entering a valid email address we will issue an API key, store it on your machine, and automatically apply it to all future requests to our servers.

If at any time you would like to remove your API key, please delete the file `~/.covidcountydata/apikey`

## Examples

We provide a few simple examples here in the README, but you can find additional examples in the `examples` folder.

### Simple Example: Single dataset for all FIPS

The example below loads all within county mobility data

```python
import covidcountydata as ccd
c = ccd.Client()

c.mobility_devices()
df = c.fetch()
```

### Simple Example: Single dataset for single county

The example below loads just demographic information for Travis County in Texas.

Notice that we can select a particular geography by specifying the fips code. We can do similar things for any of they keys listed previously.

```python
c = ccd.Client()
c.demographics(fips=48453)
df = c.fetch()
```

### Simple Example: Single dataset for all counties in a state

The example below loads just demographic information for all counties in Texas.

Notice that we can select a particular geography by specifying the fips code. We can do similar things for any of they keys listed previously.

```python
c = ccd.Client()
c.demographics(state=48)
df = c.fetch()
```


### Intermediate Example: Multiple datasets for single county

The example below loads covid and demographic data and showcases how to chain calls to multiple datasets together. It will automatically merge and return these datasets.

Note that applying a filter to any of the datasets (in this case `fips=6037`) will apply it to all datasets.

```python
c = ccd.Client()
(
    c
    .covid(fips=6037)
    .demographics()
)
df = c.fetch()
```

### Intermediate Example: Multiple datasets for all counties within one state

The example below

### Advanced Example: Multiple datasets with multiple filters and variable selection

The example below loads data from three datasets for a particular FIPS code, using a particular date of demographics, and selects certain variables from the datasets.

```python
c = ccd.Client()
(
    c
    .economics(meta_date="2018-01-01", variable="GDP_All industry total")
    .covid(fips=6037)
    .demographics(variable="Total population")
)
df = c.fetch()
```

There are more examples in the `covidcountydata/examples.py` file. We encourage you to explore them and to reach out if you have questions!
