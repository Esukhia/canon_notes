from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process
import PyTib
import copy
import re

seg = PyTib.Segment()
collection_eds = ['སྡེ་', 'ཅོ་', 'པེ་', 'སྣར་']


def open_csv(path):
    raw = open_file(path).split('\n')
    legend = raw[0].split(',')
    del raw[0]
    raw = '\n'.join(raw)
    return legend, raw


def write_profiles(notes, dir):
    '''

    :param notes: must be of this structure to work {type1: [{ed1: conc, edN: con}, {ed1: conc, edN: con}], typeN: [{ed1: conc, edN: con}, {ed1: conc, edN: con}]}
    :return: writes files to the given directory
    '''
    # format the data
    total = {}
    for profile in notes:
        error_types = []
        total_notes = []
        for note in notes[profile]:
            out = []
            for ed in collection_eds:
                out.append('{}༽ {}\n'.format(ed, note[ed]))
            out.append('{}༽ {}\n'.format('type', note['type']))
            error_types.append(note['type'])
            total_notes.append(out)
        # sorting by error type
        total_notes = sorted(total_notes, key=lambda x: x[-1])

        # merging the parts of each note
        for i in range(len(total_notes)):
            total_notes[i] = ''.join(total_notes[i])

        # counting how many entries by type
        types_num = defaultdict(int)
        for t in set(error_types):
            for error in error_types:
                if error == t:
                    types_num[t] += 1
        stats = ''
        stats += 'Total notes: {}\n'.format(str(len(total_notes)))
        for type in sorted(types_num, key=lambda x: types_num[x], reverse=True):
            stats += '{}: {}\n'.format(type, types_num[type])

        total[profile] = stats + '\n'.join(total_notes)
    # write them in files
    for t in total:
        write_file('./{}/{}.txt'.format(dir, t), total[t])


def write_types(notes, dir):
    '''

    :param notes: must be of this structure to work {type1: [{ed1: conc, edN: con}, {ed1: conc, edN: con}], typeN: [{ed1: conc, edN: con}, {ed1: conc, edN: con}]}
    :return: writes files to the given directory
    '''
    # format the data
    total = {}
    for type in notes:
        total_notes = []
        for note in notes[type]:
            out = []
            for ed in collection_eds:
                out.append('{}༽ {}\n'.format(ed, note[ed]))
            total_notes.append('\n'.join(out))
        total[type] = '\n'.join(total_notes)

    # write them in files
    def write(total):
        for t in total:
            write_file('./{}/{}.txt'.format(dir, t), total[t])

    write(total)


def prepare_data(raw, legend):
    notes = defaultdict(list)
    for note in raw.split('---')[1:]:
        parts = note.split('\n')
        type = ''
        for num, p in enumerate(parts[0].split(',')):
            if p == 'x':
                type = legend[num]
        eds = {}
        for e in range(1, 5):
            ed = parts[e].split(':')[0]
            text = parts[e].split(',')[0].split(': ')[1]
            eds[ed] = text
        notes[type].append(eds)
    return notes


def note_types(notes):
    percents = []
    total = 0
    types = []
    for n in notes:
        occs = len(notes[n])
        types.append((n, occs))
        total += occs
    for t in sorted(types, key=lambda x: x[1], reverse=True):
        percent = t[1] * 100 / total
        percents.append('{:02.2f}% ({})\t{}'.format(percent, t[1], t[0]))
    return 'Total types: {}\n{}'.format(total, '\n'.join(percents))


def find_profiles(data):
    profiles = defaultdict(list)
    for type in data:
        for note in data[type]:
            groups = defaultdict(list)
            for n in note.keys():
                groups[note[n]].append(n)
            profile = ['='.join(sorted(groups[a])) for a in groups]
            profile = ' '.join(sorted(profile))
            typed_note = note
            typed_note['type'] = type
            profiles[profile].append(typed_note)
    return profiles


def note_indexes(note):
    def side_indexes(note, extremity):
        # copy to avoid modifying directly the note
        note_conc = copy.deepcopy(note)
        # dict for the indexes of each edition
        indexes = {t: 0 for t in collection_eds}
        # initiate the indexes values to the lenght of syllables for the right context
        if extremity == -1:
            for i in indexes:
                indexes[i] = len(note_conc[i])
        #
        side = True
        while side and side and len(note_conc[collection_eds[0]]) > 0:
            # fill syls[] with the syllables of the extremity for each edition
            syls = []
            for n in note_conc:
                syls.append(note_conc[n][extremity])
            # check wether the syllables are identical or not. yes: change index accordingly no: stop the while loop
            if len(set(syls)) == 1:
                for n in note_conc:
                    # change indexes
                    if extremity == 0:
                        indexes[n] += 1
                    if extremity == -1:
                        indexes[n] -= 1
                    # delete the identical syllables of all editions
                    del note_conc[n][extremity]
            else:
                side = False
        return indexes

    left, right = 0, -1
    l_index = side_indexes(note, left)
    r_index = side_indexes(note, right)
    combined_indexes = {ed: {'left': l_index[ed], 'right': r_index[ed]} for ed in l_index}
    return combined_indexes


def segment_space_on_particles(string):
    global seg

    def contains_punct(string):
        # put in common
        if '༄' in string or '༅' in string or '༆' in string or '༇' in string or '༈' in string or \
                        '།' in string or '༎' in string or '༏' in string or '༐' in string or '༑' in string or \
                        '༔' in string:
            return True
        else:
            return False

    segmented = [a + '་' if not a.endswith('་') else a for a in seg.segment(string, syl_segmented=1, unknown=0).split('་ ')]
    # taking back the tsek on last syllable if string didn’t have one
    if not string.endswith('་') and segmented[-1].endswith('་'):
        segmented[-1] = segmented[-1][:-1]
    out = []
    for s in segmented:
        if contains_punct(s):
            regex = ''.join({c for c in s if contains_punct(c)})
            splitted = [a for a in re.split(r'([{0}]*[^ ]*[{0}]*)'.format(regex), s) if a != '']
            well_split = []
            word = ''
            for sp in splitted:
                if contains_punct(sp):
                    well_split.append(word.strip())
                    well_split.append(sp)
                    word = ''
                else:
                    word += sp
            well_split.append(word.strip())
            out.extend(well_split)
        else:
            out.append(s)
    return out


def extract_note_text(note):
    for t in note:
        note[t] = segment_space_on_particles(note[t])

    indexes = note_indexes(note)
    notes = {}
    for t in note:
        left = indexes[t]['left']
        right = indexes[t]['right']
        note_text = note[t][left:right]
        note_text = de_pre_process(note_text)
        notes[t] = note_text
    return notes


def generate_stats(data):
    # how many mistakes of each type
    write_types(data, dir='error_types')
    write_file('total_stats.txt', note_types(data))

    # find all combinations of note differences and put together with the type
    profiles = find_profiles(data)
    write_profiles(profiles, dir='profiles')


def find_category(data, category, out_dir='note_categories'):
    # find all notes from a given category and write it to a csv file
    category_total = []
    for d in data[category]:
        note = copy.deepcopy(d)
        notes = extract_note_text(note)
        category_total.append(notes)

    csv = ''
    csv += '\t'.join([a for a in category_total[0]])+'\n'
    for note in category_total:
        for n in note:
            csv += note[n]+'\t'
        csv += '\n'
    write_file('./{}/{}.csv'.format(out_dir, category), csv)


def find_categories(data, categories):
    for category in categories:
        find_category(data, category)


def main():
    # prepare the structure
    legend, raw = open_csv('./chonjuk - Feuille 1.csv')
    data = prepare_data(raw, legend)

    # process
    generate_stats(copy.deepcopy(data))

    categories = ['min mod', 'tense']
    find_categories(data, categories)

#main()