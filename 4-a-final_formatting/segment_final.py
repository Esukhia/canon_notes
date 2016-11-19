from PyTib.common import open_file, write_file, tib_sort
import PyTib
import os

in_path = 'output/corrected_unmarked'
out_path = 'output/corrected_segmented'
for f in os.listdir(in_path):
    work_name = f.replace('_unmarked.txt', '')
    content = open_file('{}/{}'.format(in_path, f))
    segmented = PyTib.Segment().segment(content)
    mistakes = [str(num)+line for num, line in enumerate(segmented.split('\n')) if '#' in line]
    write_file("{}/{}_segmented.txt".format(out_path, work_name), '\n'.join(mistakes))