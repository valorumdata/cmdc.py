"""
This example loads the within county mobility data for all fips
and all dates
"""
import cmdc

c = cmdc.Client()

c.mobility_devices()
df = c.fetch()
