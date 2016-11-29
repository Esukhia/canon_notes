from PyTib.common import open_file, write_file
import os
from collections import deque

pattern = {
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
}


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


in_path = './output/2-3-a_reinserted'
out_path = './output/3-1-page_reinserted'
for f in os.listdir(in_path):
    work_name = f.replace('_a_reinserted.txt', '')
    print('processing', work_name)
    content = open_file('{}/{}'.format(in_path, f))
    text, notes = content.split('\n\n')
    lines = deque(text.replace('\n', ' ').split('a'))

    pages = []
    text_pattern = pattern[work_name][2:]
    counter = pattern[work_name][0][1]
    side = pattern[work_name][0][2]

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

    write_file('{}/{}_a_reinserted.txt'.format(out_path, work_name), '\n{}\n'.format('-'*100).join(pages) + '\n\n' + notes)

