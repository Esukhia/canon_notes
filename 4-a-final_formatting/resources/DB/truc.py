from PyTib.common import open_file, write_file

total = open_file('total.txt').strip().split()

names = open_file('names.txt').strip().split()

real_names = [name.split('_')[1] for name in names]

correspondances = []
for n, name in enumerate(real_names):
    for m, t in enumerate(total):
        if name in t:
            correspondances.append((m, names[n], t))
correspondances = sorted(correspondances)

write_file('results.csv', '\n'.join(['{},{},{}'.format(a[0], a[1], a[2]) for a in correspondances]))