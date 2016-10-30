import jsonpickle as jp
from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process
import PyTib
import copy
import re
import os

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False)
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
        if left_context != [] and '#' in left_context[0]:
            del left_context[0]
        if right_context != [] and '#' in right_context[-1]:
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
    global collection_eds
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


def strip_similar_syls(list_of_lists):
    while len({a[0] for a in list_of_lists if a != []}) == 1:
        for b in range(len(list_of_lists)):
            if list_of_lists[b]:
                del list_of_lists[b][0]
    while len({a[-1] for a in list_of_lists if a != []}) == 1:
        for c in range(len(list_of_lists)):
            if list_of_lists[c]:
                del list_of_lists[c][-1]


def categorise(note, categorised, verbs):
    def contains_x(note, x):
        yes = False
        for ed in note[1].keys():
            if x in note[1][ed][1]:
                yes = True
        return yes

    def format_entry(note, cat):
        return {note[0]: [cat, {n: list(note[1][n]) for n in note[1]}]}

    def pre_process(note):
        # extract only note_texts
        note_texts = {}
        for ed in note[1]:
            note_texts[ed] = note[1][ed][1]
        # cut in syls
        for ed in note_texts:
            note_texts[ed] = re.sub(r'([^་]) ', r'\1_', note_texts[ed])  # keep the merged particles
            note_texts[ed] = re.sub(r'(་)([^ ])', r'\1 \2', note_texts[ed]) # insert spaces where there is none
            note_texts[ed] = note_texts[ed].split(' ')  # split in syllables
            note_texts[ed] = [a.replace('_', ' ') for a in note_texts[ed]]  # restore spaces in syllables with merged particles
        return note_texts

    def process_mistakes(note_texts):
        def split_syls(note_texts):
            # split syls in two
            syl_parts = defaultdict(list)
            for ed in note_texts:
                for syl in note_texts[ed]:
                    if '#' in syl:
                        syl = syl.replace('#', '')
                        parts = comp.get_parts(syl)
                        if parts == None:  # the syl is ill-formed
                            syl_parts[ed].append('#'+syl)
                        else:  # the syllable is well-formed and can be split
                            syl_parts[ed].append(parts)
                    else:  # the syl does not contain "#"
                        syl_parts[ed].append(syl)
            return syl_parts

        def find_missing_vowels(syl_parts):
            missing_vowel = {}
            for ed in syl_parts:
                for num, syl in enumerate(syl_parts[ed]):
                    if type(syl) == list or type(syl) == tuple:
                        # if there is no vowel
                        if 'ི' not in syl[1] and 'ེ' not in syl[1] and 'ུ' not in syl[1] and 'ོ' not in syl[1]:
                            for vowel in ['ི', 'ེ', 'ུ', 'ོ']:
                                left, right = ''.join(syl_parts[ed][:num]), ''.join(syl_parts[ed][num+1:])
                                new_syl = syl[0]+vowel+syl[1]
                                new_text = left+new_syl+right
                                new_segmented = seg.segment(new_text)
                                if '#' not in new_segmented:
                                    missing_vowel[ed] = [vowel, list(syl)]
            return missing_vowel

        def find_nga_da(note_texts):
            nga_da = {}
            for ed in note_texts:
                for num, syl in enumerate(note_texts[ed]):
                    if '#' in syl:
                        new_syl = syl.replace('ང', 'ད').replace('#', '')
                        left, right = ''.join(note_texts[ed][:num]), ''.join(note_texts[ed][num + 1:])
                        new_segmented = seg.segment(left+new_syl+right)
                        if '#' not in new_segmented:
                            nga_da[ed] = new_syl
            return nga_da


        # prepare
        syl_parts = split_syls(note_texts)

        # if there is a mistake
        if contains_x(note, '#'):
            # 1.1 missing vowel
            vowels = find_missing_vowels(syl_parts)
            if vowels:
                categorised['automatic_categorisation']['spelling_mistake']['missing_vowel'].append(format_entry(note, vowels))
            # 1.2 nga instead of da
            nga_da = find_nga_da(note_texts)
            if nga_da:
                categorised['automatic_categorisation']['spelling_mistake']['nga_da'].append(format_entry(note, nga_da))

    def process_minor_modifications(note_texts):
        particles = { "dreldra": ["གི", "ཀྱི", "གྱི", "ཡི"], "jedra": ["གིས", "ཀྱིས", "གྱིས", "ཡིས"], "ladon": ["སུ", "ཏུ", "དུ", "རུ"], "lhakce": ["སྟེ", "ཏེ", "དེ"], "gyendu": ["ཀྱང", "ཡང", "འང"], "jedu": ["གམ", "ངམ", "དམ", "ནམ", "བམ", "མམ", "འམ", "རམ", "ལམ", "སམ", "ཏམ"], "dagdra_pa": ["པ", "བ"], "dagdra_po": ["པོ", "བོ"], "lardu": ["གོ", "ངོ", "དོ", "ནོ", "བོ", "མོ", "འོ", "རོ", "ལོ", "སོ", "ཏོ"], "cing": ["ཅིང", "ཤིང", "ཞིང"], "ces": ["ཅེས", "ཞེས"], "ceo": ["ཅེའོ", "ཤེའོ", "ཞེའོ"], "cena": ["ཅེ་ན", "ཤེ་ན", "ཞེ་ན"], "cig": ["ཅིག", "ཤིག", "ཞིག"], "gin": ["ཀྱིན", "གིན", "གྱིན"], "jungkhung": ["ནས", "ལས"]}
        all_particles = [p for c in particles for p in particles[c]]

        def particle_groups(group):
            particle_pairs = [('ladon',), ('dreldra', 'jedra'), ('jedra',), ('gyendu',), ('dreldra',), ('dagdra_pa', 'ladon'), ('dagdra_po', 'ladon'), ('jungkhung', 'ladon'), ('jedra', 'jungkhung'), ('dagdra',), ('lardu',), ('gyendu', 'jedu'), ('dreldra', 'lardu')]
            out = False
            cases = []
            for i in group:
                for case in particles:
                    if i in particles[case]:
                        cases.append(case)
            # check if the marked cases are in particle_pairs
            pair = tuple(sorted(cases))
            if pair in particle_pairs:
                out = pair
            return out

        def min_mod_groups(group):
            groups = [['དེ', 'འདི'], ['འདི', 'ནི'], ['ན', 'ནས'], ['ན', 'ནི'], ['ཡང', 'ནི'], ['ལ', 'ནི'], ['གི', 'ནི'], ['གིས', 'ནི'], ['གྱིས', 'ནི'], ['ཉིད', 'ནི'], ['ཏེ', 'ནི'], ['གམ', 'དང'], ['གང', 'དག'], ['དང', 'དག'], ['རྣམས', 'དག'], ['ཡང', 'དག'], ['དག', 'དང'], ['དང', 'ནས'], ['དང', 'ལ'], ['གང', 'འགའ'], ['བ འང', 'གང'], ['ཉིད', 'གི'], ['ཉིད', 'ཞིང'], ['གིས', 'ཉིད'], ['ཡི', 'ཞིང'], ['ཡི', 'ཡིན', 'ཡིས'], ['དེ', 'པ'], ['དང', 'པ འི'], ['པ ས', 'ཤིང'], ['པ ས', 'ནས'], ['པ', 'ཅན'], ['ལས', 'བ ས'], ['ལས', 'ལ'], ['ན', 'ཏེ'], ['ཇི', 'དེ'], ['དེ', 'དང'], ['དེ', 'ལ'], ['ཅིང', 'ཅིག'], ['ཅེས', 'ཅེ'], ['ཞེ', 'ཞེས']]
            group_size = [a for a in group if '་' in a]  # keep only the multi-syllabled words

            out = []
            if not group_size:
                for m in groups:
                    if sorted(m) == sorted(group):
                        out.append(group)
            return out

        def particle_issues(group):
            cases = []
            if len(group) > 1:
                for part in group:
                    for case in particles:
                        if part in particles[case] and case not in cases:
                            cases.append(case)
            if len(cases) == 1 and len(group) > len(cases):
                return 'same', cases
            elif len(cases) == 1 and len(group) == 1:
                return 'added_particle', cases
            elif len(cases) > 1:
                return 'different_particles', cases
            else:
                return 'other', cases

        def only_particles(l):
            if not l:
                return False
            else:
                part = True
                for el in l:
                    if el not in all_particles:
                        part = False
                return part

        # 2.0 make a list of all the note texts
        group = [note_texts[a] for a in note_texts]
        strip_similar_syls(group)
        group = list(set([''.join(a) for a in group]))

        # 2.1 min mod groups
        min_mod_group = min_mod_groups(group)
        if min_mod_group:
            categorised['automatic_categorisation']['min_mod']['min_mod_groups'].append(format_entry(note, min_mod_group))

        if only_particles(group):
            # 2.2 particle groups
            part_group = particle_groups(group)
            if part_group:
                categorised['automatic_categorisation']['min_mod']['particle_groups'].append(format_entry(note, list(part_group)))

            same_diff = particle_issues(group)
            # 2.3 particle agreement difference
            if same_diff[0] == 'same':
                categorised['automatic_categorisation']['particle_issues']['agreement_issue'].append(format_entry(note, same_diff[1][0]))
            # 2.4 different cases
            elif not part_group:
                if same_diff[0] == 'added_particle':
                    categorised['automatic_categorisation']['particle_issues']['added_particle'].append(format_entry(note, same_diff[1][0]))
                elif same_diff[0] == 'different_particles':
                    categorised['automatic_categorisation']['particle_issues']['different_particles'].append(
                        format_entry(note, same_diff[1][0]))
                elif same_diff[0] == 'other':
                    categorised['automatic_categorisation']['particle_issues']['other'].append(
                        format_entry(note, same_diff[1][0]))

    def verb_difference(note_texts, verbs):
        profiles = [
            # with tense
            ['ཐ་དད་མི་དད།', 'དུས།', 'བྱ་ཚིག'],
            ['དུས།', 'བྱ་ཚིག'],
            ['དུས།', 'བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'],
            # without tense
            ['དུས།'],
            # could be any
            ['ཐ་དད་མི་དད།'],
            ['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།']
        ]

        def verb_type(group, profiles):
            no_tense = [profiles[3]]
            with_tense = [profiles[0], profiles[1], profiles[2]]
            a = []
            b = []
            for verb in group:
                for meaning in verbs[verb]:
                    profile = sorted([a for a in meaning])
                    if profile in no_tense:
                        a.append(verb)
                    elif profile in with_tense:
                        b.append(verb)

            is_with_tense = True
            is_no_tense = True
            for verb in group:
                if verb not in b:
                    is_with_tense = False
                if verb not in a:
                    is_no_tense = False

            if is_no_tense:
                return 'no_tense'
            elif is_with_tense:
                return 'with_tense'
            else:
                return 'dunno'

        def common_verb(group):
            def intersect(*lists):
                return list(set.intersection(*map(set, lists)))

            roots = {}
            meanings = {}
            for verb in group:
                for meaning in verbs[verb]:
                    if verb not in roots.keys():
                        roots[verb] = []
                    extracted_roots = list({meaning['བྱ་ཚིག'] if 'བྱ་ཚིག' in meaning.keys() else '' for a in meaning})
                    roots[verb].extend(extracted_roots)
                    meanings[verb] = verbs[verb]

            lists = [roots[a] for a in roots]
            common = intersect(*lists)

            common_meanings = {}
            for c in common:
                for verb in meanings:
                    for meaning in meanings[verb]:
                        if meaning['བྱ་ཚིག'] == c:  # Todo add a check of the same profile
                            if c not in common_meanings.keys():
                                common_meanings[c] = []
                            common_meanings[c].append(meaning)

            return common_meanings

        def format_meanings(meanings):
            profiles = [
                # with tense
                (['ཐ་དད་མི་དད།', 'དུས།', 'བྱ་ཚིག'], ('{} གི་ {} {}', 'བྱ་ཚིག', 'དུས།', 'ཐ་དད་མི་དད།')),
                (['དུས།', 'བྱ་ཚིག'], ('{} གི་ {}', 'བྱ་ཚིག', 'དུས།')),
                (['དུས།', 'བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'],
                 ('{} གི་དུས་ {} གི་ འབྲི་ཚུལ་གཞན།', 'བྱ་ཚིག', 'དུས།')),
                # without tense
                (['དུས།'], ('བྱ་ཚིག་{}', 'དུས།')),
                # could be any
                (['ཐ་དད་མི་དད།'], ('{}', 'ཐ་དད་མི་དད།')),
                (['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'], ('{} གི་ འབྲི་ཚུལ་གཞན།', 'བྱ་ཚིག'))
            ]
            out = []
            for verb in meanings:
                for meaning in meanings[verb]:
                    profile = sorted([a for a in meaning])
                    for p in profiles:
                        if profile == p[0]:
                            out.append(p[1][0].format(*[meaning[a] for a in p[1][1:]]))
            return out

        group = [note_texts[a] for a in note_texts]
        strip_similar_syls(group)
        if {len(a) for a in group} == {1}:  # there are only one syllable per edition
            group = list({a[0] for a in group})  # make it a list of words
            only_verbs = True
            for g in group:
                if g not in verbs:
                    only_verbs = False

            if only_verbs:
                verb_type = verb_type(group, profiles)
                if verb_type == 'with_tense':
                    common = common_verb(group)
                    if common:
                        formatted = format_meanings(common)

                    print('ok')

    # 0. find parts
    note_texts = pre_process(note)

    # 1. process mistakes
    process_mistakes(note_texts)

    # 2. if the difference is a particle
    process_minor_modifications(note_texts)

    # 3. verb differences
    verb_difference(note_texts, verbs)


def process(in_path, template_path):
    global collection_eds
    raw_template = open_file(template_path)
    verbs = jp.decode(open_file('./resources/monlam_verbs.json'))
    for f in os.listdir(in_path):
        print(f)
        work_name = f.replace('_conc-corrected.yaml', '')

        raw = open_file('{}/{}'.format(in_path, f))
        # setting collection_eds for the current file
        collection_eds = list({a for a in re.findall(r' ([^ ]+): ', raw)})

        data = prepare_data(raw)

        # prepare
        prepared = find_all_parts(data)

        # categorise
        categorised_notes = jp.decode(raw_template)
        for note in prepared:
            if debug:
                if f == file and note[0] == note_num:
                    categorise(note, categorised_notes, verbs)
            else:
                categorise(note, categorised_notes, verbs)

        # finally write the json file
        encoded = jp.encode(categorised_notes)
        if encoded != raw_template:
            write_file('output/{}_cats.json'.format(work_name), encoded)


if __name__ == '__main__':
    debug = False
    file = '1-སྣ་ཚོགས།_ལུགས་ཀྱི་བསྟན་བཅོས་སྐྱེ་བོ་གསོ་བའི་ཐིགས་པ་ཞེས་བྱ་བ།_conc-corrected.yaml'
    note_num = 159

    in_path = '../1-b-manually_corrected_conc/notes_restored'
    template = './resources/template.json'
    process(in_path, template)
