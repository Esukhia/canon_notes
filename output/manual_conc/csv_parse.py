from collections import defaultdict
from PyTib.common import open_file, write_file

raw = open_file('./chonjuk - Feuille 1.csv').split('\n')
legend = raw[0].split(',')
del raw[0]
raw = '\n'.join(raw)

# prepare the structure
notes = defaultdict(list)
for note in raw.split('---')[1:]:
    parts = note.split('\n')
    type = ''
    for num, p in enumerate(parts[0].split(',')):
        if p == 'x':
            type = legend[num]
    eds = {}
    for e in range(1, 5):
        ed = parts[e].split(':')[0]
        text = parts[e].split(',')[0].split(': ')[1]
        text = text.strip("' ")
        eds[ed] = text
    notes[type].append(eds)

# general statistics of the main categories
print('ok')