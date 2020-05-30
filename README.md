# cmdc.py
Python client for accessing the COVID Modeling Data Collaborative database


Example:

```python
c = Client()
(
    c
    .economics(meta_date="2018-01-01", variable="GDP_All industry total")
    .covid(fips=6037)
    .demographics(variable="Total population")
)
df = c.fetch()
```
