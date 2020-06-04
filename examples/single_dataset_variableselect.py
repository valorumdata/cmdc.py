"""
This example loads a subset of the demographic data by selecting
a few variables and a few fips codes
"""
import cmdc

c = cmdc.Client()

c.demographics(variable=[
    "Total population", "Fraction of population over 65", "Median age",
    "Mean household income",
    "Percent of civilian population with no health insurance"
])
df = c.fetch()
