from PyTib.common import open_file, write_file, pre_process, split_in_two
import csv_parse
import yaml
import copy
import sys
path = '/home/swan/Documents/PycharmProjects/sandbox/kangyur_notes_reinsertion/output/manual_conc/'
if sys.path[0] != path:
    sys.path.insert(0, path)


def find_cat_notes(in_file, cat):
    raw = open_file(in_file)
    legend = raw.split('\n')[0].split(',')
    out = []
    total = 0
    for note in raw.split('\n-'):
        fields = note.split('\n')[0].split(',')

        cats = []
        for num, field in enumerate(fields):
            if field == 'x':
                cats.append(legend[num])

        if cat in cats:
            out.append(note)
            total += 1
    return 'Total notes in "{}": {}'.format(cat, total), out


def find_all_notes(in_file):
    raw = open_file(in_file)
    out = []
    total = 0
    for note in raw.split('\n-'):
        out.append(note)
        total += 1
    return 'Total notes: {}'.format(total), out


def find_note_text(notes):
    '''

    :param notes:
    :return: (<note text>, <tuples with left and right contexts>)
    '''
    extracted = {}
    for n in notes:
        parts = n.split('\n')
        note_num = parts[0].split(',')[0].replace('-', '')
        note_num = int(note_num)-1
        note = {}
        for line in parts[1:]:
            ed, text = line.split(',')[0].split(': ')
            note[ed] = text
        texts = csv_parse.extract_note_text(note)
        de = 'སྡེ་'
        to_split = ''.join(note[de]).replace(' ', '')
        split_on = texts[de].replace(' ', '')
        middle = int(len(pre_process(to_split, mode='syls')) / 2)
        context = split_in_two(to_split, split_on, middle)
        extracted[note_num] = (texts, context)
    return extracted


def reinsert_left_context(str_conc, string, debug=False):
    span = len(string) - (len(str_conc) * 2)
    if debug:
        a = string[span:]
    mid = len(str_conc) // 2

    left = 0
    while string.find(str_conc[mid - left:mid + 1], span) != -1 and mid - left >= 0:
        if debug:
            b = str_conc[mid - left:mid]
        left += 1
    left_limit = len(string) - mid - left + 1
    right = 0
    while string.rfind(str_conc[mid: mid + right + 1], span) != -1 and mid + right < len(str_conc):
        right += 1
        if debug:
            c = str_conc[mid: mid + right + 1]
    right_limit = len(string) - mid + right
    syncable = string[left_limit:right_limit]

    conc_index = str_conc.rfind(syncable)
    if conc_index == -1:
        print('"{}" not found for in "{}"'.format(syncable, str_conc))
    new_string = string[:left_limit] + str_conc[conc_index:]
    if debug:
        d = new_string[span:]
    return new_string


def reinsert_right_context(str_conc, string, debug=False):
    span = len(str_conc) * 2
    mid = len(str_conc) // 2

    left = 0
    while string.find(str_conc[mid - left:mid + 1], 0, span) != -1 and mid - left >= 0:
        if debug:
            a = str_conc[mid - left:mid + 1]
        left += 1
    left_limit = mid - left + 2
    right = 0
    while string.rfind(str_conc[mid - 1: mid + right], 0, span) != -1 and mid + right < len(str_conc):
        right += 1
        if debug:
            b = str_conc[mid - 1: mid + right]
    right_limit = mid + right
    syncable = string[left_limit:right_limit]

    conc_index = str_conc.find(syncable)
    if conc_index == -1:
        print('"{}" not found for in "{}"'.format(syncable, str_conc))
    conc_index += len(syncable)
    new_string = str_conc[:conc_index] + string[right_limit:]
    return new_string


def contextualised_text(notes, file_name):
    # finding the differing syllables from the manually checked concordance
    differing_syls = find_note_text(notes)
    # loading the structure
    unified_structure = yaml.load(open_file('/home/swan/Documents/PycharmProjects/sandbox/kangyur_notes_reinsertion/output/unified_structure/i-6-1_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།_unified_structure.yaml'.format(file_name.split('_')[0])))

    # # adjusting the contexts
    # for num, el in enumerate(unified_structure):
    #     if type(el) == dict:
    #         left = []
    #         l_counter = num-1
    #         while type(unified_structure[l_counter]) != dict and l_counter >= 0:
    #             left.insert(0, unified_structure[l_counter])
    #             l_counter -= 1
    #         right = []
    #         r_counter = num + 1
    #         while type(unified_structure[r_counter]) != dict and r_counter <= len(unified_structure):
    #             right.append(unified_structure[r_counter])
    #             r_counter += 1



    # formatting both the inline notes and the notes to review
    c = 0
    out = []
    tmp = ''
    for u in unified_structure:
        if type(u) == dict:
            if c in differing_syls.keys():
                #tmp +=  '《{}》'.format(''.join(u['སྡེ་']))
                tmp = tmp.replace('_', ' ')
                out.append('྿{}'.format(tmp))
                tmp = ''
                # example review note format :
                # 123
                # ཅོ་༽  གཟུང་︰
                # པེ་༽  བཟུང་︰
                # སྡེ་༽  གཟུང་︰
                # སྣར་༽  བཟུང་︰
                note = ['{}༽\t{}︰'.format(a, ''.join(differing_syls[c][0][a]).replace('། ', '།_').replace(' ', '').replace('_', ' ')) for a in sorted(differing_syls[c][0])]
                note = '\n'.join(note)
                note = '{}\n{}'.format(str(c+1), note)
                out.append(note)
            else:
                # inline note format :
                # 【ཅོ་〈འགྲེ་〉 པེ་〈འདྲེ་〉 སྡེ་〈འགྲེ་〉 སྣར་〈འདྲེ་〉】
                tmp += '【{}】'.format(' '.join(['{}〈{}〉'.format(a, ''.join(u[a])) for a in sorted(u)]))
            c += 1
        else:
            tmp += u
    tmp = tmp.replace('_', ' ')
    out.append('྿{}'.format(tmp))


    # for i in range(len(out)):
    #     if not out[i].startswith('྿'):
    #         num = int(out[i].split('\n')[0])-1
    #         if num == 176:
    #             print('ok')
    #         left, right = [a.replace('_', ' ') for a in differing_syls[num][1]]
    #         left_text = out[i-1]
    #         right_text = out[i+1]
    #         l_new = reinsert_left_context(left, left_text)
    #         r_new = '྿'+reinsert_right_context(right.replace('྿', ''), right_text, debug=True)
    #         print('Left: "[…]{}"\n"[…]{}" ==> "[…]{}"'.format(left, left_text[len(left_text)-len(left)*2:], l_new[len(l_new)-len(left)*2:]))
    #         print('Right: "{}[…]"\n"{}[…]" ==> "{}[…]"'.format(right, right_text[:len(right)*2], r_new[:len(right)*2]))
    #         print()
    #         out[i-1] = l_new
    #         out[i+1] = r_new

    return '\n'.join(out)


def export_cat(file_name, cat):
    name = file_name.split('.')[0]
    total, notes = find_cat_notes(file_name, cat)
    write_file('{}_{}.csv'.format(name, cat), '{}\n{}'.format(total, '\n'.join(notes)))

    export = contextualised_text(notes, file_name)
    write_file('{}_{}_tocheck.txt'.format(name, cat), export)


def export_all_notes(file_name):
    name = file_name.split('.')[0]
    total, notes = find_all_notes(file_name)
    write_file('{}_{}.csv'.format(name, 'all'), '{}\n{}'.format(total, '\n'.join(notes)))

    export = contextualised_text(notes, file_name)
    write_file('{}_{}_tocheck.txt'.format(name, 'all'), export)

file_name = 'i-6-1 བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།_conc_corrected.csv'

#export_all_notes(file_name)


categories = ['tense']
for cat in categories:
    export_cat(file_name, cat)
