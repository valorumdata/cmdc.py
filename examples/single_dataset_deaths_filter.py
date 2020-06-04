"""
This example loads a subset of the demographic data by selecting
a few variables and a few fips codes
"""
import cmdc

c = cmdc.Client()

c.covid(fips="<100", variable="deaths_total", value=">100")
df = c.fetch()
