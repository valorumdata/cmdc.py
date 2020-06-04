"""
This example loads the within county mobility data for a single
state (CA) and all dates
"""
import cmdc

c = cmdc.Client()

c.mobility_devices(state=["CA", "TX"])
# Could replace "CA" or "TX" with ("Californa", 6, "06") or
# ("Texas", 48, "48") respectively
df = c.fetch()
