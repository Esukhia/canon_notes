from PyTib.common import open_file, write_file, tib_sort, pre_process
from PyTib import Agreement
from PyTib import Segment
from collections import defaultdict
import os


# copied from 0-1_apply_note_choices.py
def format_footnote(bad, good):
    def agree_zhas(chosen_ed):
        last_syl = pre_process(chosen_ed, mode='syls')[-1]
        return Agreement().part_agreement(last_syl, 'ཞེས')

    zhas = agree_zhas(good)
    return '[^seg?]: མ་དཔེར་{}། བྱུང་ཡང་། {}། {}་བཅོས།'.format(bad, good, zhas)


def parse_data(string):
    final = []
    lines = string.split('\n')
    for line in lines:
        if not line.startswith(('#')):
            final.append(line.split('---'))
    return final

replacements = parse_data(open_file('segment_final_data.txt').strip())

in_path = 'output/1-1-unmarked'
out_path = 'output/1-2-segmented'
for f in os.listdir(in_path):
    work_name = f.replace('_unmarked.txt', '')
    content = open_file('{}/{}'.format(in_path, f))
    segmented = Segment().segment(content, danying=True)
    new_notes = ['\n']
    suggestions = defaultdict(list)
    for r in replacements:
        bad_segmented = Segment().segment(r[0])
        bads = [bad_segmented]
        if not bad_segmented.endswith('་'):
            bads.append(bad_segmented+'་')
        for b in bads:
            if b in segmented:
                segmented = segmented.replace(' {} '.format(b), ' @{} '.format(b))
                suggestions[' @{} '.format(b)] = []
                new_notes.append(format_footnote(r[0], r[1]))
    misspellings = [str(num)+line for num, line in enumerate(segmented.split('\n')) if '#' in line]

    for num, line in enumerate(segmented.split('\n')):
        for s in suggestions:
            if s in line:
                suggestions[s].append(str(num) + line)
    all_suggestions = [a for k in tib_sort(suggestions.keys()) for a in suggestions[k]+['\n'] if suggestions[k] != []]
    mistakes = misspellings + ['\n'] + all_suggestions
    write_file("{}/{}_segmented.txt".format(out_path, work_name), '\n'.join(mistakes+new_notes))

# copy the corrected file in post_seg if it does not exist
for f in os.listdir('output/0-3-corrected'):
    work_name = f.replace('_corrected.txt', '')
    existing = [g.replace('_post_seg.txt', '') for g in os.listdir('output/1-3-post_seg')]
    if work_name not in existing:
        write_file('output/1-3-post_seg/{}_post_seg.txt'.format(work_name), open_file('output/0-3-corrected/{}_corrected.txt'.format(work_name)))
