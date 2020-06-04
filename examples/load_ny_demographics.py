import cmdc

# Create client
c = cmdc.Client()

# Create the underlying request (NY is FIPS code 36)
c.demographics(fips=36)

# Fetch the output from database
df = c.fetch()  # Output is a pandas DataFrame

