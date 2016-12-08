import os
import re
from PyTib.common import open_file, write_file


def process(origin_path, target_path, origin_name_end, target_name_end):
    existing = [g.replace(target_name_end, '') for g in os.listdir(target_path)]
    for f in os.listdir(origin_path):
        if f.endswith('.txt'):
            work_name = f.replace(origin_name_end, '')
            if work_name not in existing:
                raw_content = open_file('{}/{}'.format(origin_path, f))

                # actual processing
                text, notes = raw_content.split('\n\n')
                text = text.replace('-'*100, '').replace('\n', '')
                output = '\n\n'.join([text, notes])

                write_file('{}/{}{}'.format(target_path, work_name, target_name_end), output)

origin_path = 'output/3-2-compared'
target_path = 'output/3-3-final'
origin_name_end = '_compared.txt'  # part to delete to obtain the work name
target_name_end = '_final.txt'
process(origin_path, target_path, origin_name_end, target_name_end)