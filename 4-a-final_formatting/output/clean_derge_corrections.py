from pathlib import Path
import re

files = Path('3a-1-page_refs').glob('*.txt')

for f in files:
    content = f.read_text()
    parts = re.split(r'(\[[^ab0-9]*?[0-9]+[ab]\])', content)
    replace = False
    for i in range(0, len(parts), 2):
        part = parts[i]
        if '[' in part:
            replace = True
            part = part.replace('[', '').replace(']', '')
        elif '(' in part:
            replace = True
            part = re.sub(r'\((.*?),.*?\)', r'\1', part)

        if replace:
            parts[i] = part

    if replace:
        content = ''.join(parts)
        f.write_text(content)
