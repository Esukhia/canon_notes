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


def contextualised_text(notes, file_name):
    # finding the differing syllables from the manually checked concordance
    differing_syls = find_note_text(notes)
    # loading the structure
    unified_structure = yaml.load(open_file('/home/swan/Documents/PycharmProjects/sandbox/kangyur_notes_reinsertion/output/unified_structure/i-6-1_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།_unified_structure.yaml'.format(file_name.split('_')[0])))

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

    # adjusting the contexts using
    def reinsert_right_context(right_conc, right_string):
        counter = 0
        while right_conc[counter:] not in right_string:
            counter += 1
        found = right_conc[counter:]
        left_sync_point = right_string.rfind(found, ) + len(found)
        return '྿{}{}'.format(right_conc, right_string[left_sync_point:])

    def reinsert_l_context(str_conc, string):
        len_conc = len(str_conc) - 1
        len_str = len(string) - 1

        r_counter = 0
        while str_conc[len_conc - r_counter:] != string[len_str - r_counter:]:
            r_counter += 1
        conc_r_limit = len_conc - r_counter
        conc_tmp = str_conc[:conc_r_limit + 1]
        len_conc_tmp = len(conc_tmp) - 1
        str_r_limit = len_str - r_counter
        str_tmp = string[:str_r_limit + 1]
        len_str_tmp = len(str_tmp) - 1

        l_counter = 0
        while conc_tmp[len_conc_tmp - l_counter:] == str_tmp[len_str_tmp - l_counter:]:
            l_counter += 1
        l_counter -= 1
        conc_l_limit = len_conc_tmp - l_counter
        str_l_limit = len_str_tmp - l_counter
        conc_sync = conc_tmp[conc_l_limit:]
        str_sync = str_tmp[str_l_limit:]

        final = string[:str_l_limit] + str_conc[conc_l_limit:]
        return final

    def reinsert_r_context(str_conc, string):
        len_conc = len(str_conc) - 1
        len_str = len(string) - 1
        initial_char = False
        clean_string = copy.deepcopy(string)[1:]
        if string.startswith('྿'):
            clean_string = clean_string[1:]
            initial_char = True

        l_counter = 1
        while str_conc[:l_counter] != clean_string[:l_counter]:
            l_counter += 1
        conc_l_limit = len_conc - l_counter
        conc_tmp = str_conc[:conc_l_limit + 1]
        len_conc_tmp = len(conc_tmp) - 1
        str_l_limit = len_str - l_counter
        str_tmp = clean_string[:str_l_limit + 1]
        len_str_tmp = len(str_tmp) - 1

        r_counter = 0
        while str_tmp[len_str_tmp - r_counter:] == conc_tmp[len_conc_tmp - r_counter:]:
            r_counter += 1
        r_counter -= 1
        conc_r_limit = len_conc_tmp - r_counter
        str_r_limit = len_str_tmp - r_counter
        conc_sync = conc_tmp[conc_r_limit:]
        str_sync = str_tmp[str_r_limit:]

        final = ''


    for i in range(len(out)):
        if not out[i].startswith('྿'):
            print(i)
            num = int(out[i].split('\n')[0])-1
            left, right = differing_syls[num][1]
            left_text = out[i-1]
            right_text = out[i+1]
            #out[i-1] = reinsert_l_context(left.replace('_', ' '), left_text)
            out[i+1] = reinsert_r_context(right.replace('_', ' '), right_text)

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
