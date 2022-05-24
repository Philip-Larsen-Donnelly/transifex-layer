import sys

# appending a path
sys.path.append('src')

from translayer import tx3
import os

#create an instance of a transifex organisation (pass organisation slug and transifex API token)
org = "hisp-uio"
tx_token = os.getenv("TX_TOKEN")

tx = tx3.tx(org,tx_token)

# test stuff here


# get a list of the projects
projects = tx.projects()
for p in projects:
    if p.name[0:4] in ("pd-te"):
        for l in p.languages():
            print(l.details)

        p.delete_language("l:no")

        for l in p.languages():
            print(l.details)
            
