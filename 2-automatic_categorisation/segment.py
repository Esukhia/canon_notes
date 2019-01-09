import sys, os
grandParentDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(grandParentDir)

from PyTib.common import open_file, write_file, tib_sort, is_sskrt, pre_process
import PyTib
import pybo
import re
from collections import defaultdict


tok = pybo.BoTokenizer('GMD')
# lex_path = '../PyTib/data/uncompound_lexicon.txt'
# lexicon = open_file(lex_path).strip().split('\n')
# lexicon = '\n'.join(tib_sort(list(set(lexicon))))
# write_file(lex_path, lexicon)


def rawify(string):
    return re.sub(r'[0-9]+\.\s?\s?', '', string.replace('a', '').replace('\n', ''))


def contains_sskrt(string):
    string = string.replace('#', '')
    has_sskrt = False
    syls = pre_process(string, mode='syls')
    for syl in syls:
        if has_sskrt == False and is_sskrt(syl):
            has_sskrt = True
    return has_sskrt


def mistake_conc(segmented, work_name, context=5):
    splitted = segmented.split(' ')
    mistakes = defaultdict(list)
    for num, word in enumerate(splitted):
        if '#' in word:
            if num - context < 0:
                left = splitted[:num]
            else:
                left = splitted[num - context:num]

            if num + context > len(splitted)-1:
                right = splitted[num+1:]
            else:
                right = splitted[num+1:num+1+context]
            mistakes[word].append((work_name, [''.join(left), ''.join(right)]))
    return mistakes


def pybo_segment(content):
    tkns = tok.tokenize(content)  # tokens
    out = []
    for t in tkns:
        if t.type == 'syl' or t.type == 'non-bo':
            if t.pos == 'oov' or t.pos == 'non-word' or t.type == 'non-bo':
                out.append('#' + t.content)
            else:
                out.append(t.content)
        else:
            out.append(t.content.replace(' ', '_'))
    return ' '.join(out)


in_path = 'out'
out_path = 'segmented'
# populate total with the mistakes of all files in in_path
total = defaultdict(list)
for f in sorted(os.listdir(in_path)):
    if f.endswith('txt'):
        work_name = f.replace('.txt', '')
        print(work_name)
        content = open_file('{}/{}'.format(in_path, f))
        content = rawify(content)
        # segmented = PyTib.Segment().segment(content)
        pybo_segmented = pybo_segment(content)
        mistakes = mistake_conc(pybo_segmented, work_name)
        for k, v in mistakes.items():
            if not contains_sskrt(k):
                total[k].extend(v)

# write individual files for each text, presenting the mistakes in total frequency order
len_ordered_mistakes = sorted(total, key=lambda x: len(total[x]), reverse=True)
for f in os.listdir(in_path):
    if f.endswith('txt'):
        current_text = f.replace('.txt', '')
        # filter mistakes of the current file
        output = []
        for mis in len_ordered_mistakes:
            tmp = []
            for occ in total[mis]:
                if current_text == occ[0]:
                   tmp.append(''.join(occ[1][0])+mis+''.join(occ[1][1]))
            if tmp:
                output.append('\n'.join([mis, '\n'.join(tmp)]))
        write_file('segmented/{}_segmented.txt'.format(current_text), '\n\n'.join(output))

# write
total_formatted = []
for mis in len_ordered_mistakes:
    tmp = []
    for occ in total[mis]:
        tmp.append(''.join(occ[1][0]) + mis + ''.join(occ[1][1]))
    if tmp:
        total_formatted.append('\n'.join(['   {} {}'.format(mis, len(total[mis])), '\n'.join(tmp)]))

total_len = ', '.join([m+str(len(total[m])) for m in len_ordered_mistakes]).replace('#', '')
write_file('total_mistakes.txt', total_len+'\n'+'\n\n'.join(total_formatted))
