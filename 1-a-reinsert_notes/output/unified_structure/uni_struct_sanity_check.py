import os
import re
from PyTib.common import open_file, write_file

files = [a for a in os.listdir('.') if a != 'uni_struct_sanity_check.py']

for f in files:
    print(f)
    raw = open_file('./' + f)
    lines = raw.split('\n-')
    print('ok')
    if '[]' in lines[-1]:
        last_element = lines[-1].strip().split('\n')
        empty = True
        for l in last_element:
            if not l.endswith('[]'):
                empty = False

        if empty:
            del lines[-1]

    write_file('./'+f, '\n-'.join(lines))
