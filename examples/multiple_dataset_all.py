"""
This example loads multiple datasets (demographics and covid) for all
us fips
"""
import cmdc

c = cmdc.Client()

c.demographics().covid()
df = c.fetch()
