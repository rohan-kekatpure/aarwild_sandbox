import re
from pathlib import Path
from collections import Counter

logfile = Path('logs.csv')
with logfile.open() as f:
    lines = f.read().splitlines()

not_found = []
for line in lines:
    g = re.search(r'/api/event/not-found/[\w\d]+/([\w\d]+)/([\w\d]+)', line)
    if g is not None:
        not_found.append(g.groups())

counts = Counter(not_found)
print(counts)



