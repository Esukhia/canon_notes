import jsonpickle as jp
from PyTib.common import open_file, write_file, tib_sort, pre_process, get_longest_common_subseq, find_sub_list_indexes
import PyTib
import copy
import os
import re
import yaml
from time import time

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False, parse_int=True)


def parse_decisions(DUCKed):
    split_lines = [line.split(',') for line in DUCKed.strip().split('\n')[1:]]
    return {int(f[-1]): (f[6], f) for f in split_lines}


def group_syllables(structure):
    grouped = []
    tmp = []
    for u in structure:
        if type(u) != dict:
            tmp.append(u)
        else:
            grouped.append(tmp)
            grouped.append(u)
            tmp = []
    if tmp:
        grouped.append(tmp)
    return grouped


reviewed_path = '../3-b-reviewed_texts'
structure_path = '../3-a-revision_format/output/updated_structure'
for f in os.listdir(reviewed_path):
    work_name = f.replace('_DUCKed.csv', '')
    note_choice = parse_decisions(open_file('{}/{}'.format(reviewed_path, f)))

    # parse the file to keep only the decision and the note number
    updated_structure = yaml.load(open_file('{}/{}_updated_structure.txt'.format(structure_path, work_name)))
    unified_structure = yaml.load(open_file('../1-a-reinsert_notes/output/unified_structure/{}_unified_structure.yaml'.format(work_name)))
    grouped_unified = group_syllables(unified_structure)
    grouped_updated = group_syllables(updated_structure)

    similar_notes = 0
    output = []
    notes = []
    note_map = []
    note_num = 0
    stats = {n: 0 for n in ['D', 'U', 'C', 'K', '?']}
    for num, s in enumerate(grouped_updated):
        if not type(s) == dict:
            output.extend(s)
            note_map.extend(['.' for syl in s])
        else:
            note_num += 1
            DUCK = note_choice[note_num]
            decision = DUCK[0]
            if decision == '?':
                # take Derge and keep the note
                note = ''.join(s['སྡེ་'])
                note = '({})?'.format(note)
                output.append(note)
                note_map.append('?')
                stats[decision] += 1
                if grouped_unified[num] == s:
                    similar_notes += 1
            elif decision == 'U':
                note = ''.join(s['སྡེ་'])
                #note = '({})U'.format(note)
                output.append(note)
                note_map.append('U')
                stats[decision] += 1
            elif decision == 'D':
                note = ''.join(s['སྡེ་'])
                #note = '({})D'.format(note)
                output.append(note)
                note_map.append('D')
                stats[decision] += 1
            elif decision.startswith('C'):
                chosen = decision[1]
                if chosen == 'p':
                    note = ''.join(s['པེ་'])
                    note = '({})C[p]'.format(note)
                    output.append(note)
                    note_map.append('C[p]')
                    stats['C'] += 1
                    if grouped_unified[num] == s:
                        similar_notes += 1
                elif chosen == 'n':
                    note = ''.join(s['སྣར་'])
                    note = '({})C[n]'.format(note)
                    output.append(note)
                    note_map.append('C[n]')
                    stats['C'] += 1
                    if grouped_unified[num] == s:
                        similar_notes += 1
            elif decision == 'K':
                note = ''.join(s['སྡེ་'])
                note = '({})K'.format(note)
                output.append(note)
                note_map.append('K')
                stats[decision] += 1
                if grouped_unified[num] == s:
                    similar_notes += 1

    prepared = ''.join(output).replace(' ', '').replace('#', '').replace('_', ' ')
    write_file('output/formatted/{}_formatted.txt'.format(work_name), prepared)

    # Stats
    total = 0
    for type, value in stats.items():
        total += value
    percentages = {}
    for type, value in stats.items():
        percentages[type] = (value, value*100/total)
    discarted_notes = percentages['D'][0] + percentages['U'][0]
    kept_notes = percentages['C'][0] + percentages['K'][0] + percentages['?'][0]

    statistics = []
    for type, value in stats.items():
        statistics.append('{}: {} notes ({:02.2f}%)'.format(type, value, value*100/total))
    statistics.append('Total notes: '+str(total))
    statistics.append('Discarded notes({}+{}): {} notes ({:02.2f}%)'.format('D', 'U', discarted_notes, discarted_notes*100/total))
    statistics.append('Kept notes({}+{}+{}): {} notes ({:02.2f}%)'.format('C', 'K', '?', kept_notes, kept_notes*100/total))
    statistics.append('Similar kept notes: {} notes, {:02.2f}%'.format(similar_notes, similar_notes*100/total))
    write_file('output/stats/{}_stats.txt'.format(work_name), '\n'.join(statistics)+'\n'+' '.join(note_map))
