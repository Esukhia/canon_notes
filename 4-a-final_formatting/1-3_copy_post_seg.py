import os
from PyTib.common import open_file, write_file


def copy_missing(origin_path, target_path, origin_name_end, target_name_end):
    for f in os.listdir(origin_path):
        work_name = f.replace(origin_name_end, '')
        existing = [g.replace(target_name_end, '') for g in os.listdir(target_path)]
        if work_name not in existing:
            write_file('{}/{}{}'.format(target_path, work_name, target_name_end), open_file('{}/{}{}'.format(origin_path, work_name, origin_name_end)))


origin_path = 'output/1-3-post_seg'
target_path = 'output/2-1-a_reinserted'
origin_name_end = '_post_seg.txt'
target_name_end = '_a_reinserted.txt'
copy_missing(origin_path, target_path, origin_name_end, target_name_end)
