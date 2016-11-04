import jsonpickle as jp
from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process
import PyTib
import copy
import re
import os

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False)
seg = PyTib.Segment()
components = PyTib.getSylComponents()
collection_eds = list


def is_punct(string):
    # put in common
    if '༄' in string or '༅' in string or '༆' in string or '༇' in string or '༈' in string or \
        '།' in string or '༎' in string or '༏' in string or '༐' in string or '༑' in string or \
        '༔' in string or '_' in string:
        return True
    else:
        return False


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


def strip_similar(list_of_lists):
    lists_copy = copy.deepcopy(list_of_lists)

    # keep track of all the syllables that received an extra tsek
    no_tseks = []
    for a, list in enumerate(lists_copy):
        to_save = []
        for b, syl in enumerate(list):
            if '་' not in syl:
                lists_copy[a][b] += '་'
                to_save.append(syl+'་')
        no_tseks.append(to_save)
    no_tseks = [a[-1] if a != [] else a for a in no_tseks]

    # strip on the left
    while len({a[0] for a in lists_copy if a != []}) == 1 and [] not in lists_copy:
        for b in range(len(lists_copy)):
            if lists_copy[b]:
                del lists_copy[b][0]
    # strip on the right
    while len({a[-1] for a in lists_copy if a != []}) == 1 and [] not in lists_copy:
        for c in range(len(lists_copy)):
            if lists_copy[c]:
                del lists_copy[c][-1]

    # take away the added tseks
    for a, list in enumerate(no_tseks):
        if len(list) > 0:
            for b, syl in enumerate(list):
                if len(lists_copy[a]) != 0 and syl in lists_copy[a]:
                    lists_copy[a][b] = lists_copy[a][b].rstrip('་')

    return lists_copy


def strip_similar_syls(list_of_lists):
    def contains_merged_part(lists):
        has_merged = False
        for list in lists:
            if ' ' in list[0]:
                has_merged = True
        return has_merged

    lists_copy = strip_similar(list_of_lists)

    if {len(a) for a in lists_copy} == {1}:
        if contains_merged_part(lists_copy):
            for a in range(len(list_of_lists)):
                lists_copy[a] = lists_copy[a][0].replace(' ', ' _').split(' ')

            lists_copy = strip_similar(lists_copy)
    return lists_copy


def find_profiles(data):
    profiles = {}
    for note in data:
        groups = defaultdict(list)
        for n in note[1].keys():
            groups[note[1][n]].append(n)
        profile = ['='.join(sorted(groups[a])) for a in groups]
        profile = ' '.join(sorted(profile))
        if profile not in profiles.keys():
            profiles[profile] = [0, []]
        profiles[profile][1].append(note[0])

    total = 0
    for pro in profiles:
        num = len(profiles[pro][1])
        profiles[pro][0] = num
        total += num

    for pro in profiles:
        profiles[pro].append('{:02.2f}%'.format(profiles[pro][0] * 100 / total))

    final = {}
    for p in profiles:
        for note in profiles[p][1]:
            final[note] = [p, profiles[p][2]]

    return final, ['{}: {} ({} notes)'.format(a, profiles[a][2], profiles[a][0]) for a in profiles]


def categorise(note, categorised, verbs):
    def contains_x(note, x):
        yes = False
        for ed in note[1].keys():
            if x in note[1][ed][1]:
                yes = True
        return yes

    def format_entry(note, cat):
        if cat != 'n/a':
            return {note[0]: [cat, {n: list(note[1][n]) for n in note[1]}]}
        else:
            return {note[0]: [{n: list(note[1][n]) for n in note[1]}]}

    def remove_punct(note_texts):
        new = {}
        for ed in note_texts:
            no_punct = []
            syls = note_texts[ed].split(' ')
            for syl in syls:
                if not is_punct(syl):
                    no_punct.append(syl)
            new[ed] = ' '.join(no_punct)
        return new

    def pre_process(note):
        # extract only note_texts
        note_texts = {ed: note[1][ed][1] for ed in note[1]}
        note_texts = remove_punct(note_texts)

        # cut in syls
        for ed in note_texts:
            note_texts[ed] = re.sub(r'([^་]) ', r'\1_', note_texts[ed])  # keep the merged particles
            note_texts[ed] = re.sub(r'(་)([^ ])', r'\1 \2', note_texts[ed])  # insert spaces where there is none
            note_texts[ed] = note_texts[ed].split(' ')  # split in syllables
            note_texts[ed] = [a.replace('_', ' ') for a in                               note_texts[ed]]  # restore spaces in syllables with merged particles

        return note_texts

    def process_mistakes(note_texts):
        def split_syls(note_texts):
            # split syls in two
            syl_parts = defaultdict(list)
            for ed in note_texts:
                for syl in note_texts[ed]:
                    if '#' in syl:
                        syl = syl.replace('#', '')
                        parts = components.get_parts(syl)
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
        particles = { "dreldra": ["གི", "ཀྱི", "གྱི", "ཡི"], "jedra": ["གིས", "ཀྱིས", "གྱིས", "ཡིས", "_ས"], "ladon": ["སུ", "ཏུ", "དུ", "རུ", "_ར"], "lhakce": ["སྟེ", "ཏེ", "དེ"], "gyendu": ["ཀྱང", "ཡང", "འང"], "jedu": ["གམ", "ངམ", "དམ", "ནམ", "བམ", "མམ", "འམ", "རམ", "ལམ", "སམ", "ཏམ"], "dagdra_pa": ["པ", "བ"], "dagdra_po": ["པོ", "བོ"], "lardu": ["གོ", "ངོ", "དོ", "ནོ", "བོ", "མོ", "འོ", "རོ", "ལོ", "སོ", "ཏོ"], "cing": ["ཅིང", "ཤིང", "ཞིང"], "ces": ["ཅེས", "ཞེས"], "ceo": ["ཅེའོ", "ཤེའོ", "ཞེའོ"], "cena": ["ཅེ་ན", "ཤེ་ན", "ཞེ་ན"], "cig": ["ཅིག", "ཤིག", "ཞིག"], "gin": ["ཀྱིན", "གིན", "གྱིན"], "jungkhung": ["ནས", "ལས"]}
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
                    if el not in all_particles+['']:  # empty string added to find the additions
                        part = False
                return part

        # 2.0 make a list of all the note texts
        group = [note_texts[a] for a in note_texts]
        group = strip_similar_syls(group)
        group = [b for b in set([''.join(a).strip('་') for a in group])]

        # 2.1 min mod groups
        min_mod_group = min_mod_groups(group)
        if min_mod_group:
            categorised['automatic_categorisation']['min_mod']['min_mod_groups'].append(format_entry(note, min_mod_group))

        if only_particles(group):
            # 2.2 particle groups
            part_group = particle_groups(group)
            if part_group:
                categorised['automatic_categorisation']['min_mod']['particle_groups'].append(format_entry(note, list(part_group)))

            # 2.4 different cases
            elif not part_group:
                same_diff = particle_issues(group)
                # 2.3 particle agreement difference
                if same_diff[0] == 'same':
                    if 'dagdra_po' in same_diff[1]:
                        categorised['automatic_categorisation']['particle_issues']['dagdra_po'].append(format_entry(note, same_diff[1][0]))
                    else:
                        categorised['automatic_categorisation']['particle_issues']['agreement_issue'].append(format_entry(note, same_diff[1][0]))

                if same_diff[0] == 'added_particle':
                    categorised['automatic_categorisation']['particle_issues']['added_particle'].append(format_entry(note, same_diff[1][0]))
                elif same_diff[0] == 'different_particles':
                    categorised['automatic_categorisation']['particle_issues']['different_particles'].append(format_entry(note, same_diff[1][0]))
                elif same_diff[0] == 'other':
                    categorised['automatic_categorisation']['particle_issues']['other'].append(format_entry(note, same_diff[1][0]))

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

        def verb_type(group, profiles, verbs):
            no_tense = [profiles[3]]
            with_tense = [profiles[0], profiles[1], profiles[2]]
            a = []
            b = []
            for verb in group:
                verb_form = verb[0]
                for meaning in verbs[verb_form]:
                    profile = sorted([a for a in meaning])
                    if profile in no_tense:
                        a.append(verb_form)
                    elif profile in with_tense:
                        b.append(verb_form)

            is_with_tense = True
            is_no_tense = True
            for verb in group:
                verb_form = verb[0]
                if verb_form not in b:
                    is_with_tense = False
                if verb_form not in a:
                    is_no_tense = False

            if is_no_tense:
                return 'no_tense'
            elif is_with_tense:
                return 'with_tense'
            else:
                return 'dunno'

        def same_verb_or_not(group, profiles):
            '''
            returns either a dict with the verbal form and the common meanings, or all the meanings if the verbal forms don’t have any verb in common.
            :param group:
            :return:
            '''
            def intersect(*lists):
                return list(set.intersection(*map(set, lists)))

            roots = {}
            meanings = {}
            for verb in group:
                verb_form = verb[0]
                for meaning in verbs[verb_form]:
                    if verb_form not in roots.keys():
                        roots[verb_form] = []
                    if sorted([a for a in meaning]) in [profiles[0], profiles[1], profiles[2]]:
                        extracted_roots = list({meaning['བྱ་ཚིག'] if 'བྱ་ཚིག' in meaning.keys() else '' for a in meaning})
                    else:
                        extracted_roots = verb
                    roots[verb_form].extend(extracted_roots)
                    meanings[verb_form] = verbs[verb_form]

            lists = [roots[a] for a in roots]
            common = intersect(*lists)

            same_verb_meanings = {}
            for c in common:
                for verb in meanings:
                    for meaning in meanings[verb]:
                        if verb not in same_verb_meanings.keys():
                            same_verb_meanings[verb] = []
                        meaning_profile = sorted([a for a in meaning])
                        if meaning_profile in [profiles[0], profiles[1], profiles[2]]:
                            if meaning['བྱ་ཚིག'] == c:
                                same_verb_meanings[verb].append(meaning)
                        elif meaning_profile == profiles[3]:
                            same_verb_meanings[verb].append(meaning)

            if same_verb_meanings:
                return same_verb_meanings
            else:
                return meanings

        def format_meanings(meanings):
            profiles = [
                # with tense
                (['ཐ་དད་མི་དད།', 'དུས།', 'བྱ་ཚིག'], ('〈{}〉གི་ {} {}', 'བྱ་ཚིག', 'དུས།', 'ཐ་དད་མི་དད།')),
                (['དུས།', 'བྱ་ཚིག'], ('〈{}〉གི་ {}', 'བྱ་ཚིག', 'དུས།')),
                (['དུས།', 'བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'],
                 ('〈{}〉གི་ {} འབྲི་ཚུལ་གཞན།', 'བྱ་ཚིག', 'དུས།')),
                # without tense
                (['དུས།'], ('{}', 'དུས།')),
                # could be any
                (['ཐ་དད་མི་དད།'], ('{}', 'ཐ་དད་མི་དད།')),
                (['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'], ('〈{}〉 འབྲི་ཚུལ་གཞན།', 'བྱ་ཚིག'))
            ]
            out = []
            for verb in meanings:
                same_verb_meanings = []
                for meaning in meanings[verb]:
                    profile = sorted([a for a in meaning])
                    for p in profiles:
                        if profile == p[0]:
                            same_verb_meanings.append(p[1][0].format(*[meaning[a] for a in p[1][1:]]))
                out.append('《'+verb+'》ཞེས་པ།【'+'】【'.join(sorted(same_verb_meanings))+'】')
            return out

        def is_only_verbs(group, verbs):
            '''
            Checks if there are only verbs in the note and if they are all 1 syl long
            :param group:
            :param verbs:
            :return:
            '''
            for num, g in enumerate(group):
                group[num] = [a.rstrip('་') for a in g]

            only_verbs = None
            if {len(a) for a in group} == {1}:  # there are only one syllable per edition
                only_verbs = True
                group = list({a[0] for a in group})  # make it a list of words
                for g in group:
                    if g not in verbs:
                        only_verbs = False
            return only_verbs

        # 3.0 prepare
        group = [note_texts[a] for a in note_texts]
        group = strip_similar_syls(group)

        if is_only_verbs(group, verbs):
            # process verbs and extract the list of tenses and verbs
            note_verbs = same_verb_or_not(group, profiles)
            formatted = format_meanings(note_verbs)
            note_type = verb_type(group, profiles, verbs)

            # 3.1 categorize the note
            # find criteria to categorise
            tenses_set = {m['དུས།'] for n in note_verbs for m in note_verbs[n] if 'དུས།' in m.keys()}
            verbs_set = {m['བྱ་ཚིག'] if 'བྱ་ཚིག' in m.keys() else n for n in note_verbs for m in note_verbs[n]}

            # categorize
            if note_type == 'with_tense':
                if len(tenses_set) > 1 and len(verbs_set) == 1:
                    categorised['automatic_categorisation']['verb_difference']['diff_tense'].append(format_entry(note, formatted))
                elif len(verbs_set) > 1:
                    categorised['automatic_categorisation']['verb_difference']['diff_verb'].append(format_entry(note, formatted))
            elif note_type == 'no_tense':
                if len(verbs_set) > 1:
                    categorised['automatic_categorisation']['verb_difference']['diff_verb'].append(format_entry(note, formatted))
                else:
                    categorised['automatic_categorisation']['verb_difference']['not_sure'].append(format_entry(note, formatted))
            elif note_type == 'dunno':
                categorised['automatic_categorisation']['verb_difference']['not_sure'].append(format_entry(note, formatted))

    def already_exists(nested_dict, note_num):
        contains_note = False
        locations = [('min_mod_groups', nested_dict['automatic_categorisation']['min_mod']['min_mod_groups']),
         ('particle_groups', nested_dict['automatic_categorisation']['min_mod']['particle_groups']),
         ('added_particle', nested_dict['automatic_categorisation']['particle_issues']['added_particle']),
         ('agreement_issue', nested_dict['automatic_categorisation']['particle_issues']['agreement_issue']),
         ('different_particles', nested_dict['automatic_categorisation']['particle_issues']['different_particles']),
         ('missing_vowel', nested_dict['automatic_categorisation']['spelling_mistake']['missing_vowel']),
         ('nga_da', nested_dict['automatic_categorisation']['spelling_mistake']['nga_da']),
         ('ill_formed', nested_dict['automatic_categorisation']['spelling_mistake']['non_word']['ill_formed']),
         ('well_formed', nested_dict['automatic_categorisation']['spelling_mistake']['non_word']['well_formed']),
         ('sskrt', nested_dict['automatic_categorisation']['sskrt']),
         ('diff_tense', nested_dict['automatic_categorisation']['verb_difference']['diff_tense']),
         ('diff_verb', nested_dict['automatic_categorisation']['verb_difference']['diff_verb']),
         ('not_sure', nested_dict['automatic_categorisation']['verb_difference']['not_sure'])]
        for l in locations:
            notes_id = [b for a in l[1] for b in a]
            if note_num in notes_id:
                contains_note = True
        return contains_note

    def is_tibetan_text(note_texts):
        is_tibetan = True
        for n in note_texts:
            for syl in note_texts[n]:
                sy = syl.replace('#', '').replace('་', '').replace(' ', '')
                if sy != '':
                    if not components.get_parts(sy):
                        is_tibetan = False
        return is_tibetan

    def contains_sskrt(note_texts):
        # Source for regexes : Paul Hackett Visual Basic script
        # Now do Sanskrit: Skt.vowels, [g|d|b|dz]+_h, hr, shr, Skt
        regex1 = r"([ཀ-ཬཱ-྅ྐ-ྼ]{0,}[ཱཱཱིུ-ཹཻཽ-ྃ][ཀ-ཬཱ-྅ྐ-ྼ]{0,}|[ཀ-ཬཱ-྅ྐ-ྼ]{0,}[གཌདབཛྒྜྡྦྫ][ྷ][ཀ-ཬཱ-྅ྐ-ྼ]{0,}|[ཀ-ཬཱ-྅ྐ-ྼ]{0,}[ཤཧ][ྲ][ཀ-ཬཱ-྅ྐ-ྼ]{0,}|[ཀ-ཬཱ-྅ྐ-ྼ]{0,}[གྷཊ-ཎདྷབྷཛྷཥཀྵ-ཬཱཱཱིུ-ཹཻཽ-ྃྒྷྚ-ྞྡྷྦྷྫྷྵྐྵ-ྼ][ཀ-ཬཱ-྅ྐ-ྼ]{0,})"
        # more Sanskrit: invalid superscript-subscript pairs
        regex2 = r"([ཀ-ཬཱ-྅ྐ-ྼ]{0,}[ཀཁགང-ཉཏ-དན-བམ-ཛཝ-ཡཤཧཨ][ྐ-ྫྷྮ-ྰྴ-ྼ][ཀ-ཬཱ-྅ྐ-ྼ]{0,})"
        # tsa-phru mark used in Chinese transliteration
        regex3 = r"([ཀ-ཬཱ-྅ྐ-ྼ]{0,}[༹][ཀ-ཬཱ-྅ྐ-ྼ]{0,})"
        is_sskrt = False
        for n in note_texts:
            for syl in note_texts[n]:
                if '#' in syl:
                    sy = syl.replace('#', '').replace('་', '')
                    if not re.search(regex1, sy) or not re.search(regex2, sy) or not re.search(regex3, sy):
                        is_sskrt = True
        return is_sskrt

    def differing_syls_count(note_texts):
        def combs(xs, i=0):
            # from http://stackoverflow.com/a/32555515
            if i == len(xs):
                yield ()
                return
            for c in combs(xs, i + 1):
                yield c
                yield c + (xs[i],)
        input = [len(note_texts[a]) for a in note_texts]
        combinations = [a for a in combs(input) if len(a) == 2]
        count = {abs(a[0]-a[1]) for a in combinations}
        final = 0
        for c in count:
            if c > final:
                final = c
        return final

    # 0. find parts
    note_texts = pre_process(note)
    content = {syl for ed in note_texts for syl in note_texts[ed] if syl != ''}

    if len(content) != 0:
        if is_tibetan_text(note_texts):
            # 1. process mistakes
            process_mistakes(note_texts)

            # 2. if the difference is a particle
            process_minor_modifications(note_texts)

            # 3. verb differences
            verb_difference(note_texts, verbs)

            # 4. well-formed non-words
            if not already_exists(categorised, note[0]):
                contains_mistake = {True for syl in content if '#' in syl}
                if len(contains_mistake) > 0:
                    categorised['automatic_categorisation']['spelling_mistake']['non_word']['well_formed'].append(format_entry(note, 'n/a'))
                else:
                    count_syls = differing_syls_count(note_texts)
                    if count_syls == 0:
                        categorised['dunno']['no_diff'].append(format_entry(note, 'n/a'))
                    elif count_syls <= 2:
                        categorised['dunno']['short_diff'].append(format_entry(note, 'n/a'))
                    else:
                        categorised['dunno']['long_diff'].append(format_entry(note, 'n/a'))
        else:
            # 5. sskrt words
            if contains_sskrt(note_texts):
                categorised['automatic_categorisation']['sskrt'].append(format_entry(note, 'n/a'))
            else:
                categorised['automatic_categorisation']['spelling_mistake']['non_word']['ill_formed'].append(format_entry(note, 'n/a'))
    else:
        categorised['empty_notes'].append(format_entry(note, 'n/a'))


def open_ngrams():
    ngrams = {}
    for i in range(1, 13):
        lines = open_file('./resources/kangyur_ngrams/{}-grams_raw.txt'.format(i)).strip().split('\n')
        for line in lines:
            parts = line.split(' ')
            text = ''.join(parts[:-1]).strip().strip('་')
            ngrams[text] = int(parts[-1])
    return ngrams


def ngram_frequency(prepared, all_ngrams):
    def prepare_syls(string):
        return string.replace('#', '').split(' ')

    def generate_all(left, middle, right):
        rev_left = left[::-1]
        l_parts = []
        for l in range(1, len(rev_left) + 1):
            l_parts.append(''.join(rev_left[:l][::-1]))
            l_parts.append(''.join(rev_left[:l][::-1]))

        r_parts = []
        for r in range(1, len(right) + 1):
            r_parts.append(''.join(right[:r]))
            r_parts.append(''.join(right[:r]))

        left_parts_a = copy.deepcopy(l_parts)
        left_parts_a.insert(0, '')
        del left_parts_a[-1]

        right_parts_a = copy.deepcopy(r_parts)
        right_parts_a.insert(0, '')
        del right_parts_a[-1]

        return  (l_parts, middle, right_parts_a), (left_parts_a, middle, r_parts)

    def generate_versions(left, middle, right):
        out = [middle.strip().strip('་')]
        if len(left) >= len(right):
            for i in range(len(left)):
                if i <= len(right) - 1:
                    w = '{}{}{}'.format(left[i], middle, right[i]).strip().strip('་')
                    out.append(w)
                else:
                    x = '{}{}{}'.format(left[i], middle, right[-1]).strip().strip('་')
                    out.append(x)
        else:
            for i in range(len(right)):
                if i <= len(left) - 1:
                    y = '{}{}{}'.format(left[i], middle, right[i]).strip().strip('་')
                    out.append(y)
                else:
                    z = '{}{}{}'.format(left[-1], middle, right[i]).strip().strip('་')
                    out.append(z)
        return out

    def union_a_b(left, note_text, right):
        first_set, second_set = generate_all(left, note_text, right)
        versions_a = generate_versions(first_set[0], first_set[1], first_set[2])
        versions_b = generate_versions(second_set[0], second_set[1], second_set[2])
        union = sorted(list({a for a in versions_a + versions_b}), key=lambda x: len(x))
        return union

    note_ngrams = {}
    for note in prepared:
        note_ngrams[note[0]] = {}
        note_num = note[0]
        for ed in note[1]:
            left = prepare_syls(note[1][ed][0])
            note_text = note[1][ed][1].replace('#', '').replace(' ', '')
            right = prepare_syls(note[1][ed][2])

            union_versions = union_a_b(left, note_text, right)

            frequencies = []
            for chunk in union_versions:
                if chunk in all_ngrams.keys():
                    frequencies.append([chunk, str(all_ngrams[chunk])])
            note_ngrams[note[0]][ed] = frequencies

    ## prints the ngrams for the current file
    # for note in sorted(note_ngrams):
    #     print(note)
    #     for edition in note_ngrams[note]:
    #         print('\t\t' + edition)
    #         for test in note_ngrams[note][edition]:
    #             print('\t\t\t\t' + ''.join(test))

    return note_ngrams


def process(in_path, template_path, total_stats):
    global collection_eds
    raw_template = open_file(template_path)
    verbs = jp.decode(open_file('./resources/monlam_verbs.json'))
    all_ngrams = open_ngrams()
    for f in os.listdir(in_path):
        print(f)
        work_name = f.replace('_conc-corrected.yaml', '')

        raw = open_file('{}/{}'.format(in_path, f))
        # setting collection_eds for the current file
        collection_eds = list({a for a in re.findall(r' ([^ ]+): ', raw)})

        data = prepare_data(raw)
        profiles, profile_cats = find_profiles(data)

        # prepare
        prepared = find_all_parts(data)

        # categorise
        categorised_notes = jp.decode(raw_template)

        # find ngram frequencies
        frequencies = ngram_frequency(prepared, all_ngrams)

        if debug:
            if file == f and note_num != 0:
                for note in prepared:
                    if note[0] == note_num:
                        categorise(note, categorised_notes, verbs)
            elif file == f:
                for note in prepared:
                    categorise(note, categorised_notes, verbs)
        else:
            for note in prepared:
                #print(note)
                categorise(note, categorised_notes, verbs)

        # finally write the json file
        stats = {}
        total = 0
        for key1, item1 in sorted(categorised_notes.items()):
            if type(item1) == list:
                if len(item1) != 0:
                    stats[key1] = len(item1)
                    total += len(item1)
            else:
                stats[key1] = {}
                for key2, item2 in sorted(item1.items()):
                    if type(item2) == list:
                        if len(item2) != 0:
                            stats[key1][key2] = len(item2)
                            total += len(item2)
                    else:
                        stats[key1][key2] = {}
                        for key3, item3 in sorted(item2.items()):
                            if type(item3) == list:
                                if len(item3) != 0:
                                    stats[key1][key2][key3] = len(item3)
                                    total += len(item3)
                            else:
                                stats[key1][key2][key3] = {}
                                for key4, item4 in sorted(item3.items()):
                                    if type(item4) == list:
                                        if len(item4) != 0:
                                            stats[key1][key2][key3][key4] = len(item4)
                                            total += len(item4)
        stats['Notes’ total'] = total
        categorised = total
        if 'long_diff' in stats['dunno'].keys():
            categorised -= stats['dunno']['long_diff']
        if 'short_diff' in stats['dunno'].keys():
            categorised -= stats['dunno']['short_diff']
        if 'no_diff' in stats['dunno'].keys():
            categorised -= stats['dunno']['no_diff']
        percentage = categorised * 100 / total
        stats['Categorised'] = '{} notes ({:02.2f}%)'.format(categorised, percentage)
        stats['Profiles'] = profile_cats
        total_stats.append('{}\n{}'.format(work_name, jp.encode(stats)))

        encoded = jp.encode(categorised_notes)
        if encoded != raw_template:
            categorised_notes['Stats'] = stats
            categorised_notes['profile'] = profiles
            categorised_notes['ngram_freq'] = frequencies
            write_file('output/{}_cats.json'.format(work_name), jp.encode(categorised_notes))


if __name__ == '__main__':
    debug = False
    file = '1-དབུ་མ།_ཐེག་པ་ཆེན་པོ་ཉི་ཤུ་པ།_conc-corrected.yaml'
    note_num = 9

    in_path = '../1-b-manually_corrected_conc/notes_restored'
    template = './resources/template.json'
    total_stats = []
    process(in_path, template, total_stats)

    write_file('total_stats.txt', '\n\n'.join(total_stats))


