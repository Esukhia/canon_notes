 
import os
import re
from PyTib.common import open_file, write_file

missing_space = r'^([^ -])'
missing_space_rpl = r' \1'

missing_tsek = r'(ཅོ|སྣར|སྡེ|པེ)(?=):'
missing_tsek_rpl = r'\1་:'

files = [a for a in os.listdir('.') if a != 'conc_sanity_check.py']

for f in files:
    print(f)
    raw = open_file('./' + f)
    raw = re.sub(missing_space, missing_space_rpl, raw)
    raw = re.sub(missing_tsek, missing_tsek_rpl, raw)
    raw = raw.replace('-1-,,,,,,,,,,,,,,,', '-1-,,,,,,,,,,,,,,,')
    write_file('./' + f, raw)
    lines = raw.split('\n')
    for num, line in enumerate(lines):
        toprint = False
        if line.startswith('-'):
            pass
        elif line.startswith(r' ཅོ་:'):
            pass
        elif line.startswith(r' སྣར་:'):
            pass
        elif line.startswith(' སྡེ་:'):
            pass
        elif line.startswith(' པེ་:'):
            pass
        elif num == len(lines)-1 and line.strip() == '':
            pass
        else:
            print(num + 1)
            print(line)
