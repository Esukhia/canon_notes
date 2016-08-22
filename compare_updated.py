from PyTib.common import open_file, write_file, pre_process
import re
import os

def find_lines_to_compare(string):
    c = 0
    content = []
    for line in string.split('\n'):
        if c <= 1:
            content.append(line.replace('%', ''))
            c += 1
        else:
            c = 0
    return content

old = find_lines_to_compare(open_file('compare/i-1-112_རྒྱལ་པོ་གཏམ་བྱ་བ་རིན་པོ་ཆེའི་ཕྲེང་བ།_ཞུས་དག་ཚར་བ།.csv'))
new = find_lines_to_compare(open_file('compare/i-1-112_རྒྱལ་པོ་གཏམ་བྱ་བ་རིན་པོ་ཆེའི་ཕྲེང་བ།_ཞུས་དག་ཆེད།.csv'))
for line1, line2 in zip(old, new):
    parts1 = line1.split(',')
    parts2 = line2.split(',')
    for part1, part2 in zip(parts1, parts2):
        if part1 != part2:
            print(part1)
            print(part2)
            print()