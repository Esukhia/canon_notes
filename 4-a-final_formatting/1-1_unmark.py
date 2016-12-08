import os
import re
from PyTib.common import open_file, write_file


def process(in_path, file_origin, name_end, out_path):
    for f in os.listdir(in_path):
        work_name = f.replace(name_end, '')
        raw_content = open_file(file_origin.format(work_name))

        content = re.sub(r'\[[^\]]+\]', '', raw_content)
        content = re.sub(r'\:.*', '', content).strip()
        write_file(out_path[0].format(work_name), content)


in_path = 'output/0-3-corrected'
name_end = '_corrected.txt'  # part to delete to obtain the work name
file_origin = in_path+'/{}_corrected.txt'
out_path = ['output/1-1-unmarked/{}_unmarked.txt']

process(in_path, file_origin, name_end, out_path)
