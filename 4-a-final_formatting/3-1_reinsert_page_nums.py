from PyTib.common import open_file, write_file
import os
from collections import deque


def increment_counter(counter, side):
    increment = False
    change = False
    if side == 'བ':
        increment = True
    if side == 'ན':
        change = True

    if increment:
        return counter + 1, 'ན'
    if change:
        return counter, 'བ'


def page_num(counter, side):
    equivalences = [('1', '༡'), ('2', '༢'), ('3', '༣'), ('4', '༤'), ('5', '༥'), ('6', '༦'), ('7', '༧'), ('8', '༨'), ('9', '༩'), ('0', '༠')]
    num = str(counter)
    for n in equivalences:
        num = num.replace(n[0], n[1])
    return '\[{}{}\]'.format(num, side)


def create_page(lines, size, counter, side):
    page = []
    for i in range(size):
        page.append(lines.popleft())
    return page_num(counter, side) + '\n'.join(page)


def reinsert(in_path, out_path1, out_path2, patterns):
    for f in os.listdir(in_path):
        work_name = f.replace('_a_reinserted.txt', '')
        print('processing', work_name)
        content = open_file('{}/{}'.format(in_path, f))
        text, notes = content.split('\n\n')
        lines = deque(text.replace('\n', ' ').split('a'))

        pages = []
        text_pattern = patterns[work_name][2:]
        counter = patterns[work_name][0][1]
        side = patterns[work_name][0][2]

        # beginning pages
        for num in text_pattern[0]:
            pages.append(create_page(lines, num, counter, side))
            counter, side = increment_counter(counter, side)

        # body of the text
        while len(lines) > 0:
            if len(lines) >= text_pattern[1]:
                pages.append(create_page(lines, text_pattern[1], counter, side))
                counter, side = increment_counter(counter, side)
            elif text_pattern[2] == len(lines):
                pages.append(create_page(lines, len(lines), counter, side))
                counter, side = increment_counter(counter, side)
            else:
                print('There is a line number issue: only {} lines were left for the last page.'.format(len(lines)))
                pages.append(create_page(lines, len(lines), counter, side))
                counter, side = increment_counter(counter, side)

        output = '\n{}\n'.format('-'*100).join(pages) + '\n\n' + notes

        write_file('{}/{}_page_reinserted.txt'.format(out_path1, work_name), output)

        # write to the file to 3-2-compared if it is not yet there
        existing = [g.replace('_compared.txt', '') for g in os.listdir(out_path2) if g.endswith('.txt')]
        if work_name not in existing:
            write_file('{}/{}_compared.txt'.format(out_path2, work_name), output)
            text_path = '{}/extra_copies/{}'.format(out_path2, work_name)
            if not os.path.exists(text_path):
                os.makedirs(text_path)

# # works, but not needed for now…
# def create_missing_dir(origin_path, target_path, origin_name_end):
#     to_compare_texts = [g.replace(origin_name_end, '') for g in os.listdir(origin_path) if g.endswith('.txt')]
#     for text in to_compare_texts:
#         text_path = '{}/{}'.format(target_path, text)
#         if not os.path.exists(text_path):
#             os.makedirs(text_path)
#
# origin_path = 'output/3-2-compared'
# target_path = '{}/extra_copies'.format(origin_path)
# origin_name_end = '_compared.txt'
# create_missing_dir(origin_path, target_path, origin_name_end)


in_path = './output/2-1-a_reinserted'
out_path1 = './output/3-1-page_reinserted'
out_path2 = './output/3-2-compared'
patterns = {
    '1-དབུ་མ།_དབུ་མ་རྩ་བའི་ཚིག་ལེའུར་བྱས་པ་ཤེས་རབ།': [
        ('start', 1, 'ན'),
        ('end', 19, 'ན'),
        [1, 5, 5],
        7,
        6
    ],
    '1-སྤྲིང་ཡིག།_བཤེས་པའི་སྤྲིང་ཡིག': [
        ('start', 40, 'བ'),
        ('end', 46, 'བ'),
        [4],
        7,
        3
    ],
    '1-དབུ་མ།_རིགས་པ་དྲུག་ཅུ་པའི་ཚིག་ལེའུར་བྱས་པ།': [
        ('start', 20, 'བ'),
        ('end', 22, 'བ'),
        [7],
        7,
        6
    ],
    '1-དབུ་མ།_ཞིབ་མོ་རྣམ་པར་འཐག་པ་ཞེས་བྱ་བའི་མདོ།': [
        ('start', 22, 'བ'),
        ('end', 24, 'ན'),
        [2],
        7,
        6
    ],
    '1-དབུ་མ།_ཞིབ་མོ་རྣམ་པར་འཐག་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།': [
        ('start', 99, 'བ'),
        ('end', 110, 'ན'),
        [7],
        7,
        4
    ],
    '1-དབུ་མ།_ཐེག་པ་ཆེན་པོ་ཉི་ཤུ་པ།': [
        ('start', 137, 'བ'),
        ('end', 138, 'ན'),
        [7],
        7,
        7
    ]
    # '': [
    #     ('start', 0, ''),     # page start + front/back
    #     ('end', 0, ''),       # idem
    #     [0],                  # list of lines per page for the beginning of the text
    #     0,                    # general number of lines per page
    #     0                     # number of lines pertaining to the current text on the last page
    # ]
}
reinsert(in_path, out_path1, out_path2, patterns)