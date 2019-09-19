import os
import re
from PyTib.common import open_file, write_file


def process(in_path, file_origin, name_end, out_path):
    for f in os.listdir(in_path):
        work_name = f.replace(name_end, '')
        # raw_content = open_file(file_origin.format(work_name.replace('_', ' ')))
        try:
            raw_content = open_file(file_origin.format(work_name))
        except FileNotFoundError:
            continue

        content = re.sub(r'\n?[0-9]+\.\s+', '', raw_content)
        content = re.sub(r' ', '\n', content)
        write_file(out_path[0].format(work_name), content)

        content = content.replace('a', '')
        write_file(out_path[1].format(work_name), content)

# in_path = 'output/0-1-formatted'
# name_end = '_formatted.txt'  # part to delete to obtain the work name
in_path = '../3-a-revision_format/output/antconc_format'
name_end = '_antconc_format.txt'
file_origin = '../1-a-reinsert_notes/input/{}.txt'
out_path = ['output/2-0-with_a/{}_with_a.txt', 'output/0-2-raw_text/{}_raw.txt']

process(in_path, file_origin, name_end, out_path)
