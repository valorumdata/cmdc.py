"""
This example loads multiple datasets (demographics and covid) for all
us states -- It selects states by only taking fips < 100
"""
import cmdc

c = cmdc.Client()

# Note: Placing a filter in any of the datasets will impose
# the filter for the result!
c.demographics().covid(fips="<100")
df = c.fetch()
