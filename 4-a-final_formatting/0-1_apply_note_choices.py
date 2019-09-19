import jsonpickle as jp
from PyTib.common import open_file, write_file, tib_sort, pre_process, get_longest_common_subseq, find_sub_list_indexes
from PyTib import Agreement
import copy
import os
import re
import yaml
from collections import defaultdict
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


def format_footnote(note, chosen, ref):
    def agree_zhas(chosen_ed):
        last_syl = pre_process(chosen_ed, mode='syls')[-1]
        return Agreement().part_agreement(last_syl, 'ཞེས')

    def strip_punct(string):
        punct = ['༄', '༅', '༆', '༇', '༈', '།', '༎', '༏', '༐', '༑', '༔', '་', ' ']
        while string != '' and string[-1] in punct:
            string = string[:-1]
        return string

    def clean_ed_text(ed):
        return ''.join(ed).replace(' ', '').replace('#', '').replace('_', ' ')

    def strip_similar_to_chosen(note, chosen_ed):
        stripped = {}
        for k, v in note.items():
            if v != note[chosen_ed]:
                stripped[k] = v
        return stripped

    if chosen == 'K':
        try:
            stripped_note = strip_similar_to_chosen(note, 'སྡེ་')
        except KeyError:
            stripped_note = strip_similar_to_chosen(note, 'པེ་')
        ordered = defaultdict(list)
        for k, v in stripped_note.items():
            ordered[strip_punct(clean_ed_text(v))].append(k)
        # ཞེས་པར་མ་གཞན་ནང་མེད། for all notes where Derge adds something.
        if not [a for a in ordered.keys() if a != '']:
            return '{}: {}། ཞེས་པར་མ་གཞན་ནང་མེད།'.format(ref, strip_punct(''.join(note['སྡེ་'])))
        else:
            final = []
            full_names = {'སྡེ་': 'སྡེ་དགེ', 'ཅོ་': 'ཅོ་ནེ', 'པེ་': 'པེ་ཅིན', 'སྣར་': 'སྣར་ཐང་'}
            for text in tib_sort(ordered.keys()):
                if text != '':
                    final.append(text)
                    final.extend([full_names[ed] for ed in tib_sort(ordered[text]) if ed != 'ཞོལ་'])
            return '{}: {}།'.format(ref, '། '.join(final))

    elif chosen == 'b':
        derge = strip_punct(clean_ed_text(note['སྡེ་']))
        both = strip_punct(clean_ed_text(note['སྣར་']))
        zhas = agree_zhas(both)
        return '{}: མ་དཔེར་{}། བྱུང་ཡང་པེ་ཅིན་དང་སྣར་ཐང་བཞིན། {}། {}་བཅོས།'.format(ref, derge, both, zhas)
    elif chosen == 'n':
        if note_num == 370:
            print('ok')
        derge = strip_punct(clean_ed_text(note['སྡེ་']))
        narthang = strip_punct(clean_ed_text(note['སྣར་']))
        zhas = agree_zhas(narthang)
        return '{}: མ་དཔེར་{}། བྱུང་ཡང་སྣར་ཐང་བཞིན། {}། {}་བཅོས།'.format(ref, derge, narthang, zhas)
    elif chosen == 'p':
        derge = strip_punct(clean_ed_text(note['སྡེ་']))
        pecing = strip_punct(clean_ed_text(note['པེ་']))
        zhas = agree_zhas(pecing)
        return '{}: མ་དཔེར་{}། བྱུང་ཡང་པེ་ཅིན་བཞིན། {}། {}་བཅོས།'.format(ref, derge, pecing, zhas)


reviewed_path = '../3-b-reviewed_texts'
structure_path = '../3-a-revision_format/output/updated_structure'
limit = False
for f in sorted(os.listdir(reviewed_path)):
    print(f)
    if f:  # == '1-1_ཆོས་ཀྱི་དབྱིངས་སུ་བསྟོད་པ།_DUCKed.csv':
        work_name = f.replace('_DUCKed.csv', '')
        if work_name == 'N3118':
            limit = True

        if not limit:
            continue
        note_choice = parse_decisions(open_file('{}/{}'.format(reviewed_path, f)))

        # parse the file to keep only the decision and the note number
        try:
            updated_structure = yaml.load(open_file('{}/{}_updated_structure.txt'.format(structure_path, work_name)))
        except FileNotFoundError:
            continue
        try:
            unified_structure = yaml.load(open_file('../1-a-reinsert_notes/output/unified_structure/{}_unified_structure.yaml'.format(work_name)))
        except FileNotFoundError:
            continue
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
                    ref = '[^{}K]'.format(note_num)
                    note = '{}{}'.format(note, ref)
                    output.append(note)
                    notes.append(format_footnote(s, 'K', ref))
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
                        ref = '[^{}C]'.format(note_num)
                        note = '{}{}'.format(note, ref)
                        output.append(note)
                        notes.append(format_footnote(s, chosen, ref))
                        note_map.append('C[p]')
                        stats['C'] += 1
                        if grouped_unified[num] == s:
                            similar_notes += 1
                    elif chosen == 'n':
                        note = ''.join(s['སྣར་'])
                        ref = '[^{}C]'.format(note_num)
                        note = '{}{}'.format(note, ref)
                        output.append(note)
                        notes.append(format_footnote(s, chosen, ref))
                        note_map.append('C[n]')
                        stats['C'] += 1
                        if grouped_unified[num] == s:
                            similar_notes += 1
                    elif chosen == 'b':
                        note = ''.join(s['སྣར་'])
                        ref = '[^{}C]'.format(note_num)
                        note = '{}{}'.format(note, ref)
                        output.append(note)
                        notes.append(format_footnote(s, chosen, ref))
                        note_map.append('C[n]')
                        stats['C'] += 1
                        if grouped_unified[num] == s:
                            similar_notes += 1
                elif decision == 'K':
                    try:
                        note = ''.join(s['སྡེ་'])
                    except KeyError:
                        note = ''.join(s['པེ་'])
                    ref = '[^{}K]'.format(note_num)
                    note = '{}{}'.format(note, ref)
                    if [a for a in s.values() if a != []]:
                        output.append(note)
                        notes.append(format_footnote(s, decision, ref))
                        note_map.append('K')
                        stats[decision] += 1
                        if grouped_unified[num] == s:
                            similar_notes += 1
                    else:
                        note_map.append('0')
                        stats[decision] += 1
                        if grouped_unified[num] == s:
                            similar_notes += 1
                        continue

        prepared = ''.join(output).replace(' ', '').replace('#', '').replace('_', ' ').replace(' ', '\n')
        write_file('output/0-1-formatted/{}_formatted.txt'.format(work_name), prepared+'\n\n'+'\n'.join(notes))
        write_file('output/0-3-corrected/{}_corrected.txt'.format(work_name), prepared + '\n\n' + '\n'.join(notes))

        # Stats
        total = 0
        for kind, value in stats.items():
            total += value
        percentages = {}
        for kind, value in stats.items():
            percentages[kind] = (value, value * 100 / total)
        discarted_notes = percentages['D'][0] + percentages['U'][0]
        kept_notes = percentages['C'][0] + percentages['K'][0] + percentages['?'][0]

        statistics = []
        for kind, value in stats.items():
            statistics.append('{}: {} notes ({:02.2f}%)'.format(kind, value, value * 100 / total))
        statistics.append('Total notes: '+str(total))
        statistics.append('Discarded notes({}+{}): {} notes ({:02.2f}%)'.format('D', 'U', discarted_notes, discarted_notes*100/total))
        statistics.append('Kept notes({}+{}+{}): {} notes ({:02.2f}%)'.format('C', 'K', '?', kept_notes, kept_notes*100/total))
        statistics.append('Similar kept notes: {} notes, {:02.2f}%'.format(similar_notes, similar_notes*100/total))
        write_file('output/stats/{}_stats.txt'.format(work_name), '\n'.join(statistics)+'\n'+' '.join(note_map))
