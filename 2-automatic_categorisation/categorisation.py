import jsonpickle as jp
from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process
import PyTib
import copy
import re
import os

jp.set_encoder_options('simplejson', sort_keys=True, indent=4)
seg = PyTib.Segment()
comp = PyTib.getSylComponents()
collection_eds = list



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
        while side and len(note_conc) == len([a for a in note_conc if note_conc[a] != []]):
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


def segment_space_on_particles(string, syl_seg=0):
    global seg

    def contains_punct(string):
        # put in common
        if '༄' in string or '༅' in string or '༆' in string or '༇' in string or '༈' in string or \
                        '།' in string or '༎' in string or '༏' in string or '༐' in string or '༑' in string or \
                        '༔' in string:
            return True
        else:
            return False
    mistakes = 0
    if syl_seg == 0:
        mistakes = 1
    segmented = [a + '་' if not a.endswith('་') else a for a in seg.segment(string, syl_segmented=syl_seg, unknown=mistakes).split('་ ')]
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


def find_note_parts(note, on_syls=True):
    def join(l, space_on_particles=True, in_words=True):
        joined = '-'.join(l)
        if not space_on_particles:
            joined = joined.replace(' ', '')
        if in_words:
            joined = joined.replace('-', ' ')
        else:
            joined = joined.replace('-', '').replace('_', ' ')
        return joined

    for t in note:
        if on_syls:
            note[t] = segment_space_on_particles(note[t], syl_seg=1)
        else:
            note[t] = segment_space_on_particles(note[t], syl_seg=0)

    indexes = note_indexes(note)
    split_note = {}
    for t in note:
        left = indexes[t]['left']
        right = indexes[t]['right']

        note_text = note[t][left:right]
        left_context = note[t][:left]
        right_context = note[t][right:]

        # delete the extremities if these words are mistakes
        if '#' in left_context[0]:
            del left_context[0]
        if '#' in right_context[-1]:
            del right_context[-1]

        left_context = join(left_context)
        note_text = join(note_text)
        right_context = join(right_context)

        split_note[t] = (left_context, note_text, right_context)
    return split_note


def find_all_parts(notes):
    all_parts = []
    for note in notes:
        note_parts = find_note_parts(note[1], on_syls=False)
        all_parts.append((note[0], note_parts))
    return all_parts


def prepare_data(raw):
    notes = []
    splitted = re.split(r'-([0-9]+)-', raw)[1:]
    for id in range(len(splitted)):
        if id % 2 != 0:
            note = splitted[id]
            parts = note.split('\n')
            eds = {}
            for e in range(1, len(collection_eds)+1):
                ed = parts[e].split(':')[0].strip()
                text = parts[e].split(',')[0].split(': ')[1].strip()
                eds[ed] = text
            note_id = int(splitted[id-1])
            notes.append((note_id, eds))
    return notes


def categorisation(note):
    def contains_x(note, x):
        yes = False
        for ed in note[1].keys():
            if x in note[1][ed][1]:
                yes = True
        return yes

    eds = {}
    for ed in note:

    note_id = note[0]
    left = note[1][0]
    note_text = note[1][1]
    right = note[1][2]
    # 1. if there is a mistake
    if contains_x(note, '#'):

        # 0. cut each syllable in two parts
        note_syls = [note_text.replace('་', '་ ').replace('  ', ' ').split(' ')]
        syl_parts = comp.get_parts()


if __name__ == '__main__':
    path = '../1-b-manually_corrected_conc/notes_restored'
    for f in os.listdir(path):
        print(f)
        raw = open_file('{}/{}'.format(path, f))
        # setting collection_eds for the current file
        collection_eds = list({a for a in re.findall(r' ([^ ]+): ', raw)})

        data = prepare_data(raw)

        # prepare
        prepared = find_all_parts(data)

        # categorisation
        categorised = []
        for note in prepared:
            categorised.append(categorisation(note))

        #find_categories(data, categories, all=True)