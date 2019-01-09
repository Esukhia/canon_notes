from pathlib import Path

paths = Path('notes_formatted').glob('T*.txt')

for p in paths:
    p.rename(p.parent / p.name.replace('T', 'D'))


