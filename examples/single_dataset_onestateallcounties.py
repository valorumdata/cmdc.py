"""
This example loads the within county mobility data for a single
state (CA) and all dates
"""
import cmdc

c = cmdc.Client()

c.mobility_devices(state="CA")
# Could also do any of the below
# c.mobility_devices(state=6)
# c.mobility_devices(state="California")
# c.mobility_devices(state="06")
df = c.fetch()
