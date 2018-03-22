import jsonpickle as jp
from PyTib.common import open_file, write_file, tib_sort, pre_process, get_longest_common_subseq, find_sub_list_indexes
import PyTib
import copy
import os
import re
import yaml
from time import time

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False, parse_int=True)
seg = PyTib.Segment()
components = PyTib.getSylComponents()
collection_eds = list
debug = False

def is_punct(string):
    # put in common
    puncts = ['༄', '༅', '༆', '༇', '༈', '།', '༎', '༏', '༐', '༑', '༔', '_']
    for p in puncts:
        string = string.replace(p, '')
    if string == '':
        return True
    else:
        return False


def contextualised_text(notes, differing_syls, unified_structure, text_name):
    def spreadsheet_format(notes, note_num):
        struct = ['' for x in range(19)]
        left = [''.join(u['སྡེ་']) if type(u) == dict else u for u in unified_structure[num - 10:num]]
        right = [''.join(u['སྡེ་']) if type(u) == dict else u for u in unified_structure[num + 1:num + 11]]
        # prepare note
        note_texts = differing_syls[note_num][0]
        note_profile = notes[note_num]['profile']
        note_freq = notes[note_num]['ngram_freq']
        note_other_cats = [a for a in notes[note_num] if a not in ['ngram_freq', 'profile', 'ngram_freq', 'note']]  # all the other categories

        profile_string = ' '.join(note_profile)
        profile_string = profile_string.replace('པེ་', 'p').replace('སྡེ་', 'd').replace('སྣར་', 'n').replace('ཅོ་', 'c')
        freq_string = ''
        for k, v in sorted(note_freq.items()):
            tm = []
            for a in v:
                tm.append('{}({})'.format(a[0], a[1]))
            freq_string += '{}: {}; '.format(k, ', '.join(tm))
        freq_string = freq_string.replace('པེ་:', 'p').replace('སྡེ་:', 'd').replace('སྣར་:', 'n').replace('ཅོ་:', 'c')

        struct[0] = ''.join(left).replace('_', ' ')
        if 'པེ་' in note_texts.keys():
            struct[1] = note_texts['པེ་']
        if 'ཅོ་' in note_texts.keys():
            struct[2] = note_texts['ཅོ་']
        if 'སྡེ་' in note_texts.keys():
            struct[3] = note_texts['སྡེ་']
        if 'སྣར་' in note_texts.keys():
            struct[4] = note_texts['སྣར་']
        struct[5] = ''.join(right).replace('_', ' ')

        eds_notes = {'པེ་': 1, 'ཅོ་': 2, 'སྡེ་': 3, 'སྣར་': 4}
        for o in note_other_cats:
            if o.startswith('automatic__min_mod'):
                if not o.endswith('particle_groups'):
                    struct[7] += 'g '
                else:
                    struct[7] += 'p '
            if o.startswith('automatic__particle_issues'):
                if o.endswith('added_particle'):
                    struct[8] += '+ '
                if o.endswith('agreement_issue'):
                    struct[8] += '✘ '
                if o.endswith('po-bo-pa-ba'):
                    struct[8] += 'པ་བ་ '
                if o.endswith('different_particles'):
                    struct[8] += '≠ '
                if o.endswith('other'):
                    struct[8] += '? '
            if o.startswith('automatic__spelling_mistake'):
                if o.endswith('missing_vowel'):
                    struct[9] += 'v '
                    for k, v in notes[note_num][o].items():
                        if k in eds_notes.keys():
                            struct[eds_notes[k]] += '({}{}{})'.format(v[1][0], v[0], v[1][1])
                if o.endswith('nga_da'):
                    struct[9] += 'ངད '
                    for k, v in notes[note_num][o].items():
                        if k in eds_notes.keys():
                            struct[eds_notes[k]] += '({})'.format(v)
                if o.startswith('automatic__spelling_mistake__non_word'):
                    if o.endswith('ill_formed'):
                        struct[9] += 'nw✘ '
                    if o.endswith('well_formed'):
                        struct[9] += 'nw✓ '
            if o.startswith('automatic__sskrt'):
                struct[10] = '✓'
            if o.startswith('automatic__verb_difference'):
                if o.endswith('diff_tense'):
                    struct[11] += '⟶ '
                if o.endswith('diff_verb'):
                    struct[11] += '≠ '
                if o.endswith('not_sure'):
                    struct[11] += '? '
            if o.startswith('dunno'):
                if o.endswith('long_diff'):
                    struct[12] += 'l '
                if o.endswith('no_diff'):
                    struct[12] += '≡ '
                if o.endswith('short_diff'):
                    struct[12] += 's '
                struct[12] = struct[12].strip()
            if o.startswith('empty_notes'):
                struct[13] = '[ ]'
        struct[7] = struct[7].strip()
        struct[8] = struct[8].strip()
        struct[9] = struct[9].strip()
        struct[11] = struct[11].strip()

        struct[15] = profile_string
        struct[16] = freq_string
        struct[17] = text_name
        struct[18] = note_num

        final = '\t'.join(struct)
        return final

    # def find_contexts(unified_structure, note_index):
    #     left = []
    #     l_counter = note_index - 1
    #     while type(unified_structure[l_counter]) != dict and l_counter >= 0:
    #         left.insert(0, unified_structure[l_counter])
    #         l_counter -= 1
    #     right = []
    #     r_counter = note_index + 1
    #     while type(unified_structure[r_counter]) != dict and r_counter <= len(unified_structure):
    #         right.append(unified_structure[r_counter])
    #         r_counter += 1
    #     return left, right
    #
    # # adjusting the contexts
    # note_num = 0
    # for num, el in enumerate(unified_structure):
    #     if type(el) == dict:
    #         note_num += 1
    #
    #         # find the syllable that precede and follow the current note
    #         left_side, right_side = find_contexts(unified_structure, num)
    #         left_string = ''.join(left_side)
    #         right_string = ''.join(right_side)
    #
    #         # find the conc syllables from the manually checked notes in notes{}
    #         index = str(note_num)
    #         random_ed = list(notes[index]['note'].keys())[0]
    #         left_conc = notes[index]['note'][random_ed][0].replace('#', '').replace(' ', '')
    #         right_conc = notes[index]['note'][random_ed][2].replace('#', '').replace(' ', '')
    #
    #
    #         new_left_side = reinsert_left_context(left_conc, left_string)
    #         new_right_side = reinsert_right_context(right_conc, right_string)
    #



    # formatting both the inline notes and the notes to review
    c = 0
    out = []
    for num, u in enumerate(unified_structure):
        if type(u) == dict:
            if str(c+1) in differing_syls.keys():
                note = spreadsheet_format(notes, str(c+1))

                ### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                out.append(note)
    #         else:
    #             # inline note format :
    #             # 【ཅོ་〈འགྲེ་〉 པེ་〈འདྲེ་〉 སྡེ་〈འགྲེ་〉 སྣར་〈འདྲེ་〉】
    #             tmp.append('【{}】'.format(' '.join(['{}〈{}〉'.format(a, ''.join(u[a])) for a in sorted(u)])))
            c += 1
    #     else:
    #         tmp.append(u)
    # tmp = tmp.replace('_', ' ')
    # #out.append('྿{}'.format(tmp))
    # out.append(tmp)


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

    #return '\n'.join(out)
    return out


def sorted_strnum(thing):
    '''
    if thing is a dict, it works like dict.items() : it returns a list of key, value tuples.
    :param thing:
    :return:
    '''
    if type(thing) == dict:
        return [(el, thing[el]) for el in sorted(thing, key=lambda x: int(x))]
    else:
        thing = [a for a in thing]
        if thing and type(thing[0]) == tuple:
            return sorted(thing, key=lambda x: int(x[0]))
        else:
            return sorted(thing, key=lambda x: int(x))


def flat_list_dicts(l):
    if l != []:
        return {k: v for a in l for k, v in a.items()}
    else:
        return {}


def reorder_by_note(nested_dict):
    # turn the complex updated_structure into a 1-level-dict
    categorised = {}
    categorised['automatic__min_mod__min_mod_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['min_mod_groups'])
    categorised['automatic__min_mod__particle_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['particle_groups'])
    categorised['automatic__particle_issues__added_particle'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['added_particle'])
    categorised['automatic__particle_issues__agreement_issue'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['agreement_issue'])
    categorised['automatic__particle_issues__po-bo-pa-ba'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['po-bo-pa-ba'])
    categorised['automatic__particle_issues__different_particles'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['different_particles'])
    categorised['automatic__particle_issues__other'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['other'])
    categorised['automatic__spelling_mistake__missing_vowel'] = flat_list_dicts(nested_dict['automatic_categorisation']['spelling_mistake']['missing_vowel'])
    categorised['automatic__spelling_mistake__nga_da'] = flat_list_dicts(nested_dict['automatic_categorisation']['spelling_mistake']['nga_da'])
    categorised['automatic__spelling_mistake__non_word__ill_formed'] = flat_list_dicts(nested_dict['automatic_categorisation']['spelling_mistake']['non_word']['ill_formed'])
    categorised['automatic__spelling_mistake__non_word__well_formed'] = flat_list_dicts(nested_dict['automatic_categorisation']['spelling_mistake']['non_word']['well_formed'])
    categorised['automatic__sskrt'] = flat_list_dicts(nested_dict['automatic_categorisation']['sskrt'])
    categorised['automatic__verb_difference__diff_tense'] = flat_list_dicts(nested_dict['automatic_categorisation']['verb_difference']['diff_tense'])
    categorised['automatic__verb_difference__diff_verb'] = flat_list_dicts(nested_dict['automatic_categorisation']['verb_difference']['diff_verb'])
    categorised['automatic__verb_difference__not_sure'] = flat_list_dicts(nested_dict['automatic_categorisation']['verb_difference']['not_sure'])
    categorised['dunno__long_diff'] = flat_list_dicts(nested_dict['dunno']['long_diff'])
    categorised['dunno__no_diff'] = flat_list_dicts(nested_dict['dunno']['no_diff'])
    categorised['dunno__short_diff'] = flat_list_dicts(nested_dict['dunno']['short_diff'])
    categorised['empty_notes'] = flat_list_dicts(nested_dict['empty_notes'])
    categorised['manual__long_difference__differing_formulation'] = flat_list_dicts(nested_dict['manual_categorisation']['long_difference']['differing_formulation'])
    categorised['manual__long_difference__major_modification'] = flat_list_dicts(nested_dict['manual_categorisation']['long_difference']['major_modification'])
    categorised['manual__evaluation__derge_correct'] = flat_list_dicts(nested_dict['manual_categorisation']['manual_evaluation']['derge_correct'])
    categorised['manual__evaluation__meaning_difference__great_diff'] = flat_list_dicts(nested_dict['manual_categorisation']['manual_evaluation']['meaning_difference']['great_diff'])
    categorised['manual__evaluation__meaning_difference__medium_diff'] = flat_list_dicts(nested_dict['manual_categorisation']['manual_evaluation']['meaning_difference']['medium_diff'])
    categorised['manual__evaluation__meaning_difference__small_diff'] = flat_list_dicts(nested_dict['manual_categorisation']['manual_evaluation']['meaning_difference']['small_diff'])
    categorised['ngram_freq'] = nested_dict['ngram_freq']
    categorised['non_standard_notes'] = flat_list_dicts(nested_dict['non_standard_notes'])
    categorised['profile'] = nested_dict['profile']

    reordered_notes = {}
    # reinsert the notes in the new updated_structure
    for note_num in sorted_strnum([a for a in nested_dict['profile'].keys()]):
        for cat in categorised:
            if note_num in categorised[cat] and cat != 'profile' and cat != 'ngram_freq':
                if len(categorised[cat][note_num]) == 2:
                    n = categorised[cat][note_num][1]
                else:
                    n = categorised[cat][note_num][0]
                reordered_notes[note_num] = {'note': n}


    # create dict updated_structure with
    for cat in categorised:
        for el in categorised[cat]:
            if cat == 'profile' or cat == 'ngram_freq':
                reordered_notes[el][cat] = categorised[cat][el]
            else:
                if len(categorised[cat][el]) == 2:
                    reordered_notes[el][cat] = categorised[cat][el][0]
                else:
                    reordered_notes[el][cat] = True
    reordered_notes['Stats'] = nested_dict['Stats']

    return reordered_notes


def reinsert_left_context(str_conc, string, debug=False):
    # reduce the search to the last 2* str_conc characters
    span = len(string) - (len(str_conc) * 2)
    if debug:
        a = string[span:]
    mid = len(str_conc) // 2

    # search from the middle (mid) of the span to the left as long as the characters are a substring of span
    left = 0
    while string.find(str_conc[mid - left:mid + 1], span) != -1 and mid - left >= 0:
        if debug:
            b = str_conc[mid - left:mid]
        left += 1
    #left_limit = len(string)-1 - (mid + (left - 1) - 1) #len(string) - 1 - mid - left + 2
    # do the same to the right
    right = 0
    while string.rfind(str_conc[mid: mid + right + 1], span) != -1 and mid + right < len(str_conc):
        right += 1
        if debug:
            c = str_conc[mid: mid + right + 1]
    #right_limit = left_limit + mid + right #len(string)- 1 - mid + right + 1
    syncable = str_conc[mid - left + 1:mid + right]

    left_limit = string.rfind(syncable)
    conc_index = str_conc.rfind(syncable)
    if conc_index == -1:
        print('left: "{}" not found in "{}"'.format(syncable, str_conc))
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
    left_limit = mid - left + 1
    right = 0
    while string.rfind(str_conc[mid - 1: mid + right], 0, span) != -1 and mid + right < len(str_conc):
        right += 1
        if debug:
            b = str_conc[mid - 1: mid + right]
    right_limit = mid + right
    syncable = str_conc[left_limit:right_limit]

    conc_index = str_conc.find(syncable)
    if conc_index == -1:
        print('right: "{}" not found in "{}"'.format(syncable, str_conc))
    conc_index += len(syncable)
    new_string = str_conc[:conc_index] + string[right_limit:]
    return new_string


def update_unified_structure(unified_structure, notes):
    global debug
    unified = copy.deepcopy(unified_structure)
    def find_contexts(unified, note_index, conc_length):
        def choose_edition_text(side):
            c = len(side)
            while c > 0:
                c -= 1
                if type(side[c]) == dict:
                    eds = list(side[c].keys())
                    if 'སྡེ་' in eds:
                        side[c:c+1] = side[c]['སྡེ་']
                    else:
                        random_edition = eds[0]
                        side[c] = side[c][random_edition]
            return side

        if note_index - conc_length <= 0:
            left = choose_edition_text(unified[:note_index])
        else:
            left = choose_edition_text(unified[note_index - conc_length:note_index])
        if note_index + conc_length + 1 > len(unified)-1:
            right = choose_edition_text(unified[note_index + 1:])
        else:
            right = choose_edition_text(unified[note_index+1:note_index+conc_length+1])
        return left, right

    def until_next_note(unified, counter):
        next_syls = []
        i = 1
        while len(unified)-1 >= counter + i and type(unified[counter + i]) != dict:
            next_syls.append(unified[counter + i])
            i += 1
        return next_syls

    def until_previous_note(updated_structure):
        previous_syls = []
        i = len(updated_structure)-1
        while i >= 0 and type(updated_structure[i]) != dict:
            previous_syls.insert(0, updated_structure[i])
            i -= 1
        return previous_syls

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

    # A. insert the notes from the manually checked concordance
    updated_structure = []
    note_num = 0
    #for num, el in enumerate(unified_structure):
    counter = 0
    while counter <= len(unified)-1:
        el = unified[counter]
        if type(el) == dict:
            note_num += 1
            # print(note_num)
            # if note_num == 40:
            #     print('ok')
            # find the syllable that precede and follow the current note
            # left_side, right_side = find_contexts(unified, counter, conc_length=20)
            # left_string = ''.join(left_side)
            # right_string = ''.join(right_side)

            # find the conc syllables from the manually checked notes in notes{}
            # index = str(note_num)
            # random_ed = list(notes[index]['note'].keys())[0]
            # left_conc = notes[index]['note'][random_ed][0].replace('#', '').replace(' ', '')
            # right_conc = notes[index]['note'][random_ed][2].replace('#', '').replace(' ', '')

            # # adjusting the context if necessary
            # if not left_string.endswith(left_conc):
            #     #new_left_side = reinsert_left_context(left_conc, left_string)  #, debug=True)
            #     #new_left_syls = pre_process(new_left_side, mode='syls')
            #     previous_syls = until_previous_note(updated_structure)
            #     left_conc_syls = pre_process(left_conc, mode='syls')
            #     common = get_longest_common_subseq([previous_syls, left_conc_syls])
            #     if common:
            #         to_insert = left_conc_syls[find_sub_list_indexes(get_longest_common_subseq([common, left_conc_syls]), left_conc_syls)[0]:]
            #         indexes = find_sub_list_indexes(common, updated_structure[len(updated_structure)-len(previous_syls):])
            #         # if indexes == None:
            #         #     indexes = (0, 0)
            #         l_index = len(updated_structure) - len(previous_syls) + indexes[0]
            #         updated_structure[l_index:] = to_insert
            #     else:
            #         for i in range(len(previous_syls)):
            #             del updated_structure[-1]
            #
            # if not right_string.startswith(right_conc):
            #     #new_right_side = reinsert_right_context(right_conc, right_string)  #, debug=True)
            #     #new_right_syls = pre_process(new_right_side, mode='syls')
            #     # take all the syllables until the next note
            #     next_syls = until_next_note(unified, counter)
            #     if next_syls != []:
            #         # find the common syllables
            #         right_conc_syls = pre_process(right_conc, mode='syls')
            #         common = get_longest_common_subseq([next_syls, right_conc_syls])
            #         if common:
            #             # check if there is some syllables to strip in right_conc_syls TODO adjust the check: the output is worse than before
            #             previous = until_previous_note(updated_structure)
            #             sub_list = get_longest_common_subseq([previous, right_conc_syls])
            #             if sub_list and ''.join(previous).endswith(''.join(sub_list)):
            #                 to_insert = right_conc_syls[find_sub_list_indexes(sub_list, right_conc_syls)[1]:]
            #             else:
            #                 to_insert = right_conc_syls
            #             l_index, r_index = find_sub_list_indexes(common, unified[counter:])
            #             differing_els = ''.join(set(unified[counter + 1:counter + r_index + 1]).difference(to_insert))
            #             if not is_punct(differing_els):
            #                 unified[counter + 1:counter + r_index + 1] = to_insert

            # add the new note
            index = str(note_num)
            if debug:
                print(index)
                if index == '2160':
                    print('ok')
                print(notes[index]['note'])
            if index in notes.keys() and note_num != len(notes):
                updated_structure.append({k: pre_process(v[1].replace(' ', '').replace('#', ''), mode='syls') for k, v in notes[index]['note'].items()})
        else:
            updated_structure.append(el)
        counter += 1

    # B. adjust the contexts
    total_notes = 0

    grouped_unified = group_syllables(unified_structure)
    grouped_updated = group_syllables(updated_structure)
    for i in range(len(grouped_updated)):
        if type(grouped_updated[i]) == dict:
            # calculating the percentage of similar notes
            total_notes += 1
            editions = [e for e in grouped_updated[i]]
            all_left = []
            all_right = []
            for ed in editions:
                upd = grouped_updated[i][ed]
                uni = grouped_unified[i][ed]
                common = get_longest_common_subseq([upd, uni])
                if common:
                    l_index, r_index = find_sub_list_indexes(common, upd)
                    left = upd[:l_index]
                    right = upd[r_index + 1:]
                    all_left.append(left)
                    all_right.append(right)
            all_left = [list(k) for k in set(map(tuple, all_left)) if k]
            all_right = [list(k) for k in set(map(tuple, all_right)) if k]

            # ONE : All left contexts are same
            if len(all_left) == 1:
                # left context ends with left
                left_context = grouped_updated[i - 1]
                # left context ends with left
                if ''.join(left_context).endswith(''.join(all_left[0])):
                    for j in range(len(all_left[0])):
                        del grouped_updated[i - 1][-1]

            # TWO : All right contexts are same
            if len(all_right) == 1:
                # right context starts with right
                right_context = grouped_updated[i + 1]
                if ''.join(right_context).startswith(''.join(all_right[0])):
                    for j in range(len(all_right[0])):
                        del grouped_updated[i + 1][0]

    degrouped_updated = []
    for el in grouped_updated:
        if type(el) == list:
            degrouped_updated.extend(el)
        else:
            degrouped_updated.append(el)

    return degrouped_updated


def extract_categories(notes, text_name, cat_list=False):
    def find_cat_notes(notes, cat):
        differing_syls = {}  # {'note_num': ( {texts}, (left, right))}
        sorted_notes = sorted_strnum([(a, b) for a, b in notes.items() if a != 'Stats'])
        for k, v in sorted_notes:
            if cat in v.keys():
                editions = copy.deepcopy(v['note'])
                context = (editions['སྡེ་'][0], editions['སྡེ་'][2])
                for e in editions:
                    editions[e] = editions[e][1]
                differing_syls[k] = (editions, context)
        return differing_syls

    all_categories = ['automatic__min_mod__min_mod_groups', 'automatic__min_mod__particle_groups', 'automatic__particle_issues__added_particle', 'automatic__particle_issues__agreement_issue', 'automatic__particle_issues__po-bo-pa-ba', 'automatic__particle_issues__different_particles', 'automatic__particle_issues__other', 'automatic__spelling_mistake__missing_vowel', 'automatic__spelling_mistake__nga_da', 'automatic__spelling_mistake__non_word__ill_formed', 'automatic__spelling_mistake__non_word__well_formed', 'automatic__sskrt', 'automatic__verb_difference__diff_tense', 'automatic__verb_difference__diff_verb', 'automatic__verb_difference__not_sure', 'dunno__long_diff', 'dunno__no_diff', 'dunno__short_diff', 'empty_notes']
    # loading the updated_structure
    unified_structure = yaml.load(open_file('../1-a-reinsert_notes/output/unified_structure/{}'.format(text_name+'_unified_structure.yaml')))
    updated_structure = update_unified_structure(unified_structure, notes)
    write_file('output/updated_structure/{}_updated_structure.txt'.format(text_name), yaml.dump(updated_structure, allow_unicode=True, default_flow_style=False, width=float("inf")))
    if not cat_list:
        for cat in all_categories:
            syls = find_cat_notes(notes, cat)
            if syls:
                out = contextualised_text(notes, syls, updated_structure, text_name)
                write_file('output/antconc_format/{}_{}_antconc_format.txt'.format(text_name, cat), out)
    else:
        out = []
        for cat in cat_list:
            syls = find_cat_notes(notes, cat)
            if syls:
                new_notes = contextualised_text(notes, syls, updated_structure, text_name)
                for new in new_notes:
                    if new not in out:
                        out.append(new)

        write_file('output/antconc_format/{}_antconc_format.txt'.format(text_name), '\n'.join(out))
        final = '\n'.join(out)
        return final


if __name__ == '__main__':
    #in_dir = '../2-b-manually_corrected_automatic_categorisation/'
    in_dir = '../2-automatic_categorisation/output/'
    output = []

    finished = [
        '8-14_རྡོ་རྗེ་ཕག་མོའི་སྒྲབ་ཐབས།_cats.json',
        '17-22_གཤིན་རྗེ་གཤེད་རྣམ་པར་སྣང་མཛད་ཀྱི་མངོན་པར་རྟོགས་པ།_cats.json',
        '10-33_ཆོས་མངོན་པའི་མཛོད་ཀྱི་བཤད་པ།_(B)_cats.json',
        '17-39_མི་འཁྲུགས་པའི་སྒྲུབ་ཐབས།_cats.json',
        '17-24_འོད་དཔག་ཏུ་མེད་པའི་སྙིང་པོ་འདོད་ཆགས་གཤིན་རྗེ་གཤེད་སྒྲུབ་པའི་ཐབས།_cats.json',
        '11-14_དམིགས་པ་བརྟག་པ།_cats.json',
        '11-1_སྤེལ་མར་བསྟོད་པ།_cats.json',
        '17-93_ཁ་ཏོན་དང་གླེགས་བམ་ཀླག་པའི་སྔོན་དུ་བྱ་བའི་ཆོ་ག_cats.json',
        '6-2_བསླབ་པ་ཀུན་ལས་བཏུས་པའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-43_དཔའ་ཕྱག་ན་རྡོ་རྗེ་ལ་བསྟོད་པ།_cats.json',
        '11-17_ཚད་མ་རིགས་པར་འཇུག་པའི་སྒོ།_cats.json',
        '10-16_དོན་གསང་བ་རྣམ་པར་ཕྱེ་བ་བསྡུས་ཏེ་བཤད་པ།_cats.json',
        '8-17_འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྡོ་རྗེ་གཅོད་པའི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '2-18_ཆ་ཤས་ཀྱི་ཡན་ལག་ཅེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '17-16_དཔལ་མགོན་པོའི་གཏོར་མ།_cats.json',
        '560_དཀྱིལ་འཁོར་གྱི་ཐིག་གི་ཆོ་ག།_cats.json',
        '17-31_པདྨ་གཤིན་རྗེ་གཤེད་ཤེས་རབ་བདེ་བ་ཅན་གྱི་སྒྲུབ་ཐབས།_cats.json',
        '9-3_འཕགས་པ་བྱམས་པའི་སྒྲུབ་ཐབས།_cats.json',
        '17-129-133_བར་ཆ་ཚང་།_cats.json',
        '10-26_ཐེག་པ་ཆེན་པོའི་ཆོས་བརྒྱ་གསལ་བའི་སྒོའི་བསྟན་བཅོས།_cats.json',
        '290_ཡེ་ཤེས་མགོན་པོ་གྲི་གུག་གི་ཅན་གྱི་བདག་བསྐྱེད་བཟླས་པ་བསྟོད་པ།_cats.json',
        '2-35_ཁྲོ་བོ་རེག་ཚིག་གི་སྦྱིན་སྲེག་གི་ཆོ་ག_cats.json',
        '17-98_བྱང་ཆུབ་ཀྱི་སེམས་བདེ་བའི་མན་ངག_cats.json',
        '273_དམ་ཚིག་སྦས་པ།_cats.json',
        '17-41_འཇམ་པའི་དབྱངས་དཔའ་བོ་གཅིག་ཏུ་གྲུབ་པའི་སྒྲུབས་ཐབས།_cats.json',
        '2-3_རྒྱུད་ཀྱི་རྒྱལ་པོ་དཔལ་གདན་བཞི་པ་ཞེས་བྱ་བའི་དཀྱིལ་ཆོག_cats.json',
        '17-101_དཱི་བཾ་ཀཱ་ར་ཤྲཱི་ཛྙཱ་ནའི་ཆོས་ཀྱི་གླུ།_cats.json',
        '17-138-17-140_བར་ཆ་ཚང་།_cats.json',
        '17-81_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་མདོ་ཙམ་གདམས་ངག་ཏུ་བྱས་པ།_cats.json',
        '17-96_རིགས་ཀྱི་སྨོན་ལམ།_cats.json',
        '10-28_བསྟན་བཅོས་ཚིགས་སུ་བཅད་པ་བསྡུས་པ།_cats.json',
        '4-6_དབུ་མའི་དོན་བསྡུས་པ།_cats.json',
        '17-104-17-116_བར་ཆ་ཚང་།_cats.json',
        '8-35_སློབ་དཔོན་ཀཱ་མ་ལ་ཤཱི་མའི་སྨོན་ལམ་མུ་གཉིས་མ།_cats.json',
        '522_མོ་རྩིས་འཇམ་པའི་དབྱངས།_cats.json',
        '17-70_དྲན་པ་གཅིག་པའི་མན་ངག_cats.json',
        '10-17_སུམ་ཅུ་པའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-58_འཕགས་པ་ཚོགས་ཀྱི་བདག་པོ་ཆགས་པ་རྡོ་རྗེའི་དམ་ཚིག་གི་བསྟོད་པ།_cats.json',
        '17-6_དཔའ་བོ་གཅིག་པའི་སྒྲུབ་ཐབས།_cats.json',
        '9-23_རྣམ་འབྱོར་སྤྱོད་པའི་ས་ལས་གཞི་བསྡུ་བ།_cats.json',
        '2-31_ཁྲོ་བོ་རེག་ཚིག་གི་སྒྲུབ་པའི་ཐབས།_cats.json',
        '11-5_འཕགས་པ་འཇམ་པའི་དབྱངས་ཀྱི་བསྟོད་པ།_cats.json',
        '277_ལྷ་མཆོད་པའི་རིམ་པ།_cats.json',
        '9-6_སངས་རྒྱས་རྗེས་སུ་དྲན་པའི་འགྲེལ་པ།_cats.json',
        '8-25_བསྒོམ་རིམ་བར་མ།_cats.json',
        '17-61_ཀླུ་གཏོར་གྱི་ཆོ་ག_cats.json',
        '17-72_དབུ་མའི་མན་ངག་རིན་པོ་ཆེའི་ཟ་མ་ཏོག་ཁ་ཕྱེ་བ།_cats.json',
        '17-5_དཔལ་བཅོམ་ལྡན་འདས་ཀྱི་མངོན་པར་རྟོགས་པ།_cats.json',
        '10-22_ཕུང་པོ་ལྔའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '17-161_དྲི་མ་མེད་པ་རིན་པོ་ཆེའི་སྤྲིང་ཡིག_cats.json',
        '8-15_འཇམ་པ་ཁྲོ་བོར་སྒྲུབ་པ།_cats.json',
        '8-12_ཤེས་རབ་ཀྱི་ཕ_རོལ་ཏུ་ཕྱིན་པའི་སྒྲུབ་ཐབས།_cats.json',
        '2-12_དཔལ་གསང་བ་འདུས་པའི་རྫོགས་རིམ་མཐར་ཕྱིན་པ།_cats.json',
        '17-49_གཙུག་ཏོར་དྲི་མ་མེད་པའི་གཟུངས་ཀྱི་ཆོ་ག_cats.json',
        '15-1_བྱང་ཆུབ་སེམས་དཔའི་སའི་འགྲེལ་པ།_cats.json',
        '17-69_བདེན་པ་གཉིས་ལ་འཇུག་པ།_cats.json',
        '17-102_སྦྱིན་སྲེག་གི་ཆོ་ག_cats.json',
        '8-28_རྣལ་འབྱོར་བསྒོམ་པ་ལ་འཇུག་པ།_cats.json',
        '17-134-17-137_བར་ཆ་ཚང་།_cats.json',
        '557_གཞུང་ལུགས་ཀྱི་བྱེ་བྲག་བཀོད་པའི་འཁོར་ལོ།_cats.json',
        '17-170_རྩ་བའི་ལྟུང་བའི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '9-7_ཆོས་རྗེས་སུ་དྲན་པའི་འགྲེལ་པ།_cats.json',
        '278_ཚེ་བསྒྲུབ་པའི་ཐབས།_cats.json',
        '7-4_བདེན་པ་གཉིས་རྣམ་པར་འབྱེད་པའི་དཀའ་འགྲེལ།_cats.json',
        '261_རྡོ་རྗེ་རྣལ་འབྱོར་མའི་སྒྲུབ་ཐབས།_cats.json',
        '14-9_སྡུད་པ་ཚིགས་སུ་བཅད་པའི་དཀའ་འགྲེལ།_cats.json',
        '281_རོ་བསྲེག་པའི་ཆོ་ག_cats.json',
        '2-33_སྐལ་འཇོག་དབང་གི་ཆོ་ག_cats.json',
        '17-100_དབྱུག་པ་གཤིན་རྗེ་གཤེད་རྣམ་པར་འཇོམས་པའི་སྒྲུབ་ཐབས།_cats.json',
        '8-24_བསྒོམ་རིམ་དང་པོ།_cats.json',
        '17-21_གཤིན་རྗེ་གཤེད་ནག་པོའི་སྒྲུབ་ཐབས།_cats.json',
        '17-48_གཙུག་ཏོར་དྲི་མ་མེད་པའི་གཟུངས་ཀྱི་ཆོ་ག_cats.json',
        '8-18_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་སྙིང་པོ་ཞེས་བྱ་བའི་འགྲེལ་པ།_cats.json',
        '7-14_འཕགས་པ་ཀུན་ནས་སྒོར་འཇུག་པའི་འོད་ཟེར་གཙུག་ཏོར།_cats.json',
        '5-16_སྟོང་ཉིད་བདུན་ཅུ་པའི་འགྲེལ་པ།_cats.json',
        '17-160_སྡོམ་པ་ཉི་ཤུ་པའི་འགྲེལ་པ།_cats.json',
        '17-56_སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '275_ཆུ་གཏོར་གྱི་ཆོ་ག_cats.json',
        '2-2_ཡེ་ཤེས་དབང་ཕྱུག་མའི་སྒྲུབ་ཐབས།_cats.json',
        '17-78_སྙིང་པོ་བསྡུས་པ་ཞེས་བྱ་བ།_cats.json',
        '2-13_རྣམ་པར་མི་རྟོག་པའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '17-89_ལས་རྣམ་པར་འབྱེད་པ་ཞེས་བྱ་བ།_cats.json',
        '17-95_བླ་མའི་བྱ་བའི་རིམ་པ།_cats.json',
        '17-162_དགེ་ཚུལ་གྱི་དང་པོའི་ལོ་དྲི་བ།_cats.json',
        '284_འཕགས་མ་སྒྲོལ་མ་ལ་བསྟོད་པ།_cats.json',
        '2-1_རྣལ་འབྱོར་གྱི་རྒྱུད་དཔལ་གདན་བཞི་པའི་སྒྲུབ་ཐབས།_cats.json',
        '7-12_དེ་བཞིན་གཤེགས་པ་བདུན་གྱི་སྔོན་གྱི་སྨོན་ལམ་གྱི་ཁྱད་པར་རྒྱས་པ།_cats.json',
        '5-15_ཕུང་པོ་ལྔའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '2-16_བཅོམ་ལྡན་འདས་འཇམ་པའི་དབྱངས་ཀྱི་དཔྱད།_cats.json',
        '8-7_བྱང་ཆུབ་སྤྱོད་པའི་སྒྲོན་མ་ཞེས་བྱ་བ།_cats.json',
        '17-66_ནོར་བདག་གཙོ་འཁོར་ལྔའི་བསྟོད་པ་དབྱིག་གི་ཆར་འབེབས།_cats.json',
        '10-18_ཉི་ཤུ་པའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-145_དེ་བཞིན་གཤེགས་པ་ཐམས་ཅད་ཀྱི་དམ་ཚིག་བསྲུང་བའི་སྒྲུབ་ཐབས།_cats.json',
        '9-1_ཆོས་ཀྱི་སྐུ་ལ་གནས་པའི་ཡོན་ཏན་ལ་བསྟོད་པ།_cats.json',
        '217_གཤིན་རྗེ་གཤེད་པོ་སྒྲུབ་པའི་ཐབས།_cats.json',
        '157_མི་འཁྲུགས་པའི་སྒྲུབ་ཐབས་བཞུགས།_cats.json',
        '10-34_འཕགས་པ་བཟང་པོ་སྤྱོད་པའི་སྨོན་ལམ་གྱི་འགྲེལ་པ།_cats.json',
        '3-1_དབུ་མ་རྩ་བའི་འགྲེལ་པ་བུདྡྷ་པཱ་ལི་ཏ།_cats.json',
        '10-8_འཕགས་པ་ཆོས་བཞི་པའི་རྣམ་པར་བཤད་པ།_cats.json',
        '17-17_དཔལ་གསང་བ་འདུས་པའི་དཀྱིལ་འཁོར་གྱི་ཆོ་ག_cats.json',
        '17-125-17-126བར་ཆ་ཚང།_cats.json',
        '10-25_ལས་གྲུབ་པའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '17-9_སྤྱོད་པའི་གླུ།_cats.json',
        '17-25_གཤིན་རྗེ་གཤེད་རྡོ་རྗེ་ནག་པོའི་སྒྲུབ་ཐབས།_cats.json',
        '17-67_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་དོན་བསྡུས་སྒྲོན་མ།_cats.json',
        '8-13_རྗེ་བཙུན་འཕགས་མ་སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '9-2_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་སྒྲུབ་ཐབས།_cats.json',
        '13-2_མངོན་རྟོགས་རྒྱན་གྱི་རྣམ་འགྲེལ།_cats.json',
        '17-85_ཐེག་པ་ཆེན་པོའི་ལམ་གྱི་སྒྲུབ་ཐབས་ཤིན་ཏུ་བསྡུས་པ།_cats.json',
        '9-17_དགོངས་པ་ངེས་པར་འགྲེལ་པའི་མདོའི་རྣམ་པར་བཤད་པ།_(A)_cats.json',
        '12-2_དཔལ་རྡོ་རྗེ་མཁའ་འགྲོའི་བསྟོད་པ་རྒྱུན་ཆགས།_cats.json',
        '17-11_རྡོ་རྗེ་རྣལ་འབྱོར་མ་ལ་བསྟོད་པ།_cats.json',
        '5-9_དབུ་མ་ལ་འཇུག་པ།_cats.json',
        '7-10_རྩོད་པའི་རིགས་པའི་འགྲེལ་པ་དོན་རྣམ་པར་འབྱེད་པ།_cats.json',
        '555_རྣམ་དབྱེའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-77_བྱང་ཆུབ་ལམ་གྱི་སྒྲོན་མའི་དཀའ་འགྲེལ་ཞེས་བྱ་བ།_cats.json',
        '17-18_གསང་འདུས་འཇིག་རྟེན་དབང་ཕྱུག་གི་སྒྲུབ་ཐབས།_cats.json',
        '542_དགོངས་པ་ཟབ་མོ་ངེས་པར་འགྲེལ་པའི་མདོ་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '17-30_ལས་ཀྱི་རྡོ་རྗེ་གཽ་རཱིའི་སྒྲུབ་ཐབས།_cats.json',
        '17-2_གཏོར་མའི་ཆོ་ག_cats.json',
        '2-7_སྤྱོད་པ་བསྡུས་པའི་སྒྲོན་མ།_cats.json',
        '5-6_གསང་བ་འདུས་པའི་མངོན་པར་རྟོགས་པའི་རྒྱན་གྱི་འགྲེལ་པ།_cats.json',
        '10-11_འཕགས་པ་བློ་གྲོས་མི་ཟད་པས་བསྟན་པ་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '7-15_རྡོ་རྗེས་རྣམ་པར་འཇོམས་པ་ཞེས་བྱ་བའི་གཟུངས་ཀྱི་བཤད་པ།_cats.json',
        '17-51_འཕགས་མ་ལྷ་མོ་སྒྲོལ་མ་བསྒོམ་པའི་ཆོ་ག་རྒྱས་པ།_cats.json',
        '17-153_འཕགས་མ་སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '10-29_ཡོན་ཏན་བདུན་ཡོངས་སུ་བརྗོད་པའི་གཏམ།_cats.json',
        '5-1_རྡོ་རྗེ་ཕག་མོ་སྒྲོལ་མ་ལ་བསྟོད་པ།_cats.json',
        '559_སྨོན་ལམ་གྱི་གཟུངས་བཀླག་པའི་ཆོ་ག་མདོ་སྡེ་ལས་བཏུས་པ།_cats.json',
        '179_ཁྲོ་བོ་བརྒྱད་ཀྱི་དཀྱིལ་འཁོར་དུ་དབང་བསྐུར་བ།_cats.json',
        '17-121-123_བར་ཆ་ཚང་།_cats.json',
        '17-14_དཔལ་རྡོ་རྗེ་རྣལ་འབྱོར་མའི་སྒྲུབ་ཐབས།_cats.json',
        '11-21_ཚད་མའི་བསྟན་བཅོས་རིགས་པ་ལ་འཇུག་པ།_cats.json',
        '11-4_ཨེ་ཀ་ནཱ་ཐའི་དོན་འགྲེལ།_cats.json',
        '17-79_སྙིང་པོ་ངེས་པར་བསྡུ་བ་ཞེས་བྱ་བ།_cats.json',
        '544_དམ་པའི་ཆོས་པདྨ་དཀར་པོའི་འགྲེལ་པ།_cats.json',
        '269_འཕགས་པ་ཡི་གེ་དྲུག་པའི་སྒྲུབ་ཐབས།_cats.json',
        '9-9_ཐེག་པ་ཆེན་པོ་རྒྱུད་བླ་མའི་བསྟན་བཅོས་རྣམ་པར་བཤད་པ།_cats.json',
        '17-34_འཁོར་བ་ལས་ཡིད་ངེས་པར་འབྱུང་བར་བྱེད་པའི་གླུ།_cats.json',
        '14-5_ལྟ་བ་ཐ་དད་པ་རྣམ་པར་ཕྱེ་བ་མདོར་བསྡུས་པ།_cats.json',
        '15-4_འདུལ་བ་མདོ།_cats.json',
        '4-11_སྡེ་པ་ཐ་དད་པར་བྱེད་པ་དང་རྣམ་པར་བཤད་པ།_cats.json',
        '8-23_བྱང་ཆུབ་ཀྱི་སེམས་བསྒོམ་པ།_cats.json',
        '17-26_རྡོ་རྗེ་སེམས་མ་བདེ་བའི་སྒྲུབ་ཐབས།_cats.json',
        '538_དབུ་མ་རིན་པོ་ཆེའི་སྒྲོན་མ།_cats.json',
        '8-34_དེ་ཁོ་ན་ཉིད་བསྡུས་པའི་དཀའ་འགྲེལ།_(B)_cats.json',
        '17-23_གཤིན་རྗེ་གཤེད་རིན་ཆེན་འབྱུང་ལྡན་གྱི་སྒྲུབ་ཐབས།_cats.json',
        '8-11_དེ་ཁོ་ན་ཉིད་ཕྱག་རྒྱ་ཆེན་པོ་ཡི་གེ་མེད་པའི་མན་ངག_cats.json',
        '2-19_ཆ་ཤས་ཀྱི་ཡན་ལག་ཅེས་བྱ་བའི་རབ་ཏུ་བྱེད་པའི་འགྲེལ་པ།_cats.json',
        '279_འཆི་བ་སླུ་བ།_cats.json',
        '14-4_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་མན་ངག་གི་བསྟན་བཅོས་མངོན་རྟོགས་རྒྱན་འགྲེལ།_cats.json',
        '9-4_འཕགས་པ་དགོངས་པ་ངེས་པར་འགྲེལ་པའི་རྣམ་པར་བཤད་པ།_cats.json',
        '563_རྒྱུད་ཀྱི་རྒྱལ་པོ་ཆེན་པོ་དཔལ་དགྱེས་པའི་རྡོ་རྗེའི་དཀའ་འགྲེལ་སྤྱན་འབྱེད།_cats.json',
        '17-50_སྒྲོལ་མའི་སྒྲུབ་ཐབས་བཞུགས།_cats.json',
        '567_རྔོན་པ་བ་ཆེན་པོས་ཀ་མ་ལ་ཤཱི་ལ་ལ་གནད་ཀྱི་གདམས་པ་བསྟན་པ།_cats.json',
        '14-1_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྟོང་ཕྲག་ཉི་ཤུ་ལྔ་པ།_(C)_cats.json',
        '12-8_འབྲེལ་བ་བརྟག་པའི་འགྲེལ་པ།_cats.json',
        '540_དབུ་མ་སྙིང་པོའི་འགྲེལ་པ་རྟོག་གེ་འབར་བ།_cats.json',
        '17-19_སྤྱན་རས་གཟིགས་འཇིག་རྟེན་དབང་ཕྱུག་སྒྲུབ་པའི་ཐབས།_cats.json',
        '539_དབུ་མའི་སྙིང་པོའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '9-13_རྣལ་འབྱོར་སྤྱོད་པའི་ས་ལས་གཞི་བསྡུ་བ།_cats.json',
        '2-20_བསྟན་བཅོས་བཞི་བརྒྱ་པ་ཞེས་བྱ་བའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '2-10_མངོན་པར་བྱང་ཆུབ་པའི་རིམ་པའི་མན་ངག_cats.json',
        '8-22_ཆོས་ཐམས་ཅད་རང་བཞིན་མེད་པ་ཉིད་དུ་གྲུབ་པ།_cats.json',
        '17-64_གནོད་སྦྱིན་གྱི་སྡེ་དཔོན་ཆེན་པོ་ལག་ན་རྡོ་རྗེ་གོས་སྔོན་ཅན་གྱི་བསྒྲུབ་ཐབས།_cats.json',
        '12-9_རྒྱུད་གཞན་གྲུབ་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '5-12_དབུ་མ་ཤེས་རབ་ལ་འཇུག་པ།_cats.json',
        '11-9_རྣལ་འབྱོར་ལ་འཇུག་པ།_cats.json',
        '144_གྲུབ་ཐོབ་ལྔ་བཅུའི་རྟོགས་པ་བརྗོད་པ་ཐིག་ལེའི་འོད་ཕྲེང།_cats.json',
        '8-2_ཐེག་པ་གསུང་གི་སྒྲོན་མ།_cats.json',
        '282_བདུན་ཚིགས་ཀྱི་ཆོ་ག_cats.json',
        '17-46_དཔལ་རྟ་མགྲིན་གྱི་སྒྲུབ་ཐབས།_cats.json',
        '15-7_འདུལ་བའི་མདོའི་འགྲེལ།_cats.json',
        '17-42_སྤྱན་རས་གཟིགས་དབང་ཕྱུག་ཁརྦ་པཱ་ཎིའི་སྒྲུབ་ཐབས།_cats.json',
        '2-34_ཁྲོ་བོ་རེག་ཚིག་གི་དམ་ཚིག་གསང་བའི་སྒྲུབ་ཐབས།_cats.json',
        '17-94_ཚ་ཚ་གདབ་པའི་ཆོ་ག་བཞུགས།_cats.json',
        '12-7_འབྲེལ་བ་བརྟག་པའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '12-3_ཚད་མ་རྣམ་འགྲེལ་གྱི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-57_དམ་ཚིག་ཐམས་ཅད་བསྡུས་པ།_cats.json',
        '92_རྣལ་འབྱོར་ཆེན་པོའི་རྒྱུད་དཔལ་གསང་བ་འདུས་པའི་གཏོར་མའི་ཆོ་ག_cats.json',
        '565__རིམ་ལྔའི་དཀའ་འགྲེལ།_cats.json',
        '10-15_ཐེག་པ་ཆེན་པོ་བསྡུས་པའི་འགྲེལ་པ།_cats.json',
        '7-6_དབུ་མའི་རྒྱན་གྱི་འགྲེལ་པ།_cats.json',
        '17-154_ཆོམ་རྐུན་བཅིང་བ།_cats.json',
        '293_ཤིན་ཏུ་མྱུར་བའི་ལྷ་ཆེན་པོ་བགེགས་ཀྱི་རྒྱལ་པོའི་སྒྲུབ་ཐབས།_cats.json',
        '17-8_རྡོ་རྗེ་གདན་གྱི་གླུའི་འགྲེལ་པ།_cats.json',
        '2-14_གོ་བ་བྱེད་པ་སྙིང་པོ་བརྒྱ་པ།_cats.json',
        '10-6_ཚིགས་སུ་བཅད་པ་གཅིག་པའི་བཤད་པ།_cats.json',
        '8-3_ཡང་དག་ལྟ་བའི་སྒྲོན་མ།_cats.json',
        '9-24_རྣལ་འབྱོར་སྤྱོད་པའི་ས་ལས་རྣམ་གྲངས་བསྡུ་བ།_cats.json',
        '5-5_བདུད་རྩི་འཁྱིལ་པའི་སྒྲུབ་ཐབས།_cats.json',
        '6-5_འཕགས་པ་འདའ་ཀ་ཡེ་ཤེས་ཞེས་བྱ་བ་ཐེག་པ་ཆེན་པོའི་མདོའི་འགྲེལ་པ།_cats.json',
        '4-10_སྒྲོན་མ་གསལ་བར་བྱེད་པའི་དགོངས་པ་རབ་གསལ་གྱི་ཊཱི་ཀཱ།_(A)_cats.json',
        '564_ནག་པོ་ཆེན་པོ་སྒྲུབ་པའི་ཐབས།_cats.json',
        '17-90_སྤྱོད་པ་བསྡུས་པའི་སྒྲོན་མ།_cats.json',
        '17-37_འཇིག་རྟེན་ལས་འདས་པའི་ཡན་ལག་བདུན་པའི་ཆོ་ག།_cats.json',
        '17-127_འཇིག་རྟེན་གྱི་ལྷ་མཉེས་པར་བྱེད་པ་དོན་གྲུབ།_cats.json',
        '8-6_མཐར་ཐུག་འབྲས་བུའི་སྒྲོན་མ།_cats.json',
        '17-38_སྐུ་དང་གསུང་དང་ཐུགས་རབ་ཏུ་གནས་པ།_cats.json',
        '2-22_རབ་ཏུ་བྱེད་པ་ལག་པའི་ཚད་ཀྱི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '2-5_རྡོ་རྗེ་དྲིལ་ཐབས་ཀྱིས་མཆོད་པའི་ཐབས་ཀྱི་རིམ་པ།_cats.json',
        '8-32_དད་བསྐྱེད་སྒྲོན་མ།_cats.json',
        '17-97_སྒྲོལ་མ་དཀོན་མཆོག་གསུམ་ལ་བསྟོད་པ།_cats.json',
        '17-55_སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '280_འཆི་ཀ་མའི་བསྟན་བཅོས།_cats.json',
        '8-27_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་བདུན་བརྒྱ་པ་རྒྱ་ཆེར་བཤད་པ།_cats.json',
        '11-3_ཡོན་ཏན་མཐའ་ཡས་པར་བསྟོད་པའི་དོན་གྱི་ཚིག་ལེའུར།_cats.json',
        '9-25_རྣལ་འབྱོར་སྤྱོད་པའི་ས་ལས་རྣམ་པར་བཤད་པ་བསྡུ་བ།_cats.json',
        '17-47_ཁྲོ་བོའི་རྒྱལ་པོ་འཕགས་པ་མི་གཡོ་བ་ལ་བསྟོད་པ།_cats.json',
        '17-84_ཐེག་པ་ཆེན་པོའི་ལམ་གྱི་སྒྲུབ་ཐབས་ཡི་གེ་བསྡུས་པ།_cats.json',
        '11-12_ཚད་མ་ཀུན་ལས་བཏུས་པ།_cats.json',
        '8-30_དགེ་སྦྱོང་གི་ཀཱ་རི་ཀཱ་ལྔ་བཅུ་པ་མདོ་ཙམ་དུ་བཤད་པ།_cats.json',
        '14-3_བཅོམ་ལྡན་འདས་ཡོན་ཏན་རིན་པོ་ཆེ་སྡུད་པའི་ཚིགས་བཅད་དཀའ་འགྲེལ།_cats.json',
        '10-7_འཕགས་པ་སྒོ་དྲུག་པའི་གཟུངས་ཀྱི་རྣམ་པར་བཤད་པ།_cats.json',
        '17-3_མངོན་པར་རྟོགས་པ་རྣམ་པར་འབྱེད་པ།_cats.json',
        '17-175_རྟེན་འབྲེལ་སྙིང་པོའི་སྔགས་ཐེམ་ཞིབ་མོར་བཀོད་པ།_cats.json',
        '10-27_ཆོས་མངོན་པའི་མཛོད་ཀྱི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '17-68_ཤེས་རབ་སྙིང་པོའི་རྣམ་པར་བཤད་པ།_cats.json',
        '10-1_དཀོན་མཆོག་གསུམ་གྱི་བསྟོད་པ།_cats.json',
        '11-15_དམིགས་པ་བརྟག་པའི་འགྲེལ་པ།_cats.json',
        '17-76_བྱང་ཆུབ་ལམ་གྱི་སྒྲོན་མ།_cats.json',
        '17-91_སེམས་བསྐྱེད་པ་དང་སྡོམ་པའི་ཆོ་གའི་རིམ་པ།_cats.json',
        '17-12_རིན་པོ་ཆེ་རྒྱན་གྱི་སྒྲུབ་པ།_cats.json',
        '140_ལྷན་ཅིག་སྐྱེས་པའི་གླུ།_cats.json',
        '15-2_བྱང་ཆུབ་སེམས་དཔའི་ཚུལ་ཁྲིམས་ཀྱི་ལེའུ་བཤད་པ།_cats.json',
        '5-17_གསུམ་ལ་སྐྱབས་སུ་འགྲོ་བ་བདུན་ཅུ་པ།_cats.json',
        '17-117-17-120_བར་ཆ་ཚང་།_cats.json',
        '17-10_སྤྱོད་པའི་གླུའི་འགྲེལ་པ།_cats.json',
        '2-25_ཡེ་ཤེས་སྙིང་པོ་ཀུན་ལས་བཏུས་པ།_cats.json',
        '17-157_མདོ་ཀུན་ལས་བཏུས་པ་ཆེན་པོ།_cats.json',
        '2-24_དབུ་མ་འཁྲུལ་པ་འཇོམས་པ།_cats.json',
        '17-144_ཁྲོ་བོའི་རྒྱལ་པོ་འཕགས་པ་མི་གཡོ་བ་ལ་བསྟོད་པ།_cats.json',
        '5-14_བྱང་ཆུབ་སེམས་དཔའི་རྣལ་འབྱོར་སྤྱོད་པ་བཞི་བརྒྱ་པའི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '2-11_རོ་བསྲེག་པའི་ཆོག_cats.json',
        '2-17_བདག་མེད་མ་ལྷ་མོ་བཅོ་ལྔ་ལ་བསྟོད་པ།_cats.json',
        '17-53_སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '17-60_ཆུ་གཏོར་གྱི་ཆོ་ག་བཞུགས།_cats.json',
        '5-7_ཐུགས་རྗེ་ཆེན་པོ་ལ་སྨྲེ་སྔགས་ཀྱིས་བསྟོད་པ་བྱིན་རླབས་ཅན།_cats.json',
        '11-2_ཡོན་ཏན་མཐའ་ཡས་པར་བསྟོད་པའི་འགྲེལ་པ།_cats.json',
        '17-80_བྱང་ཆུབ་སེམས་དཔའི་ནོར་བུའི་ཕྲེང་བ།_cats.json',
        '2-6_སྒྲོན་མ་གསལ་བ་ཞེས་བྱ་བའི་འགྲེལ་བཤད།_cats.json',
        '17-75_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་མདོ་ཙམ་གདམས་ངག་ཏུ་བྱས་པ།_cats.json',
        '17-99_སྲུང་བའི་འཁོར་ལོ་སྒྲུབ་པའི་ཐབས།_cats.json',
        '8-20_དབུ་མ་སྣང་བ་ཞེས་བྱ་བ།_cats.json',
        '11-27_ཚད་མ་ཀུན་ལས་བཏུས་པའི་འགྲེལ་པ།_cats.json',
        '8-5_མཉམ་ཉིད་གཞིའི་སྒྲོན་མ།_cats.json',
        '2-9_བདག་བྱིན་གྱིས་བརླབ་པའི་རིམ་པ་རྣམ་པར་དབྱེ་བ།_cats.json',
        '458_བསམ་གཏན་གྱི་སྒྲོན་མ་ཞེས་བྱ་བའི་མན་ངག_cats.json',
        '7-2_དེ་བཞིན་གཤེགས་པ་བརྒྱད་ལ་བསྟོད་པ།_cats.json',
        '12-4_ཚད་མ་རྣམ་པར་ངེས་པ།_cats.json',
        '6-1_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།_cats.json',
        '17-20_དཔལ་གསང་བ་འདུས་པའི་བསྟོད་པ།_cats.json',
        '2-21_འཁྲུལ་པ་བཟློག་པའི་རིགས་པ་གཏན་ཚིགས་གྲུབ་པ།_cats.json',
        '11-7_བཟང་པོ་སྤྱོད་པའི་སྨོན་ལམ་གྱི་རྒྱལ་པོའི་བཤད་པ།_cats.json',
        '17-65_ཁྲོ་བོའི་རྒྱལ་པོ་མི་གཡོ་བའི་བསྒྲུབ་ཐབས།_cats.json',
        '17-83_སྐྱབས་སུ་འགྲོ་བ་བསྟན་པ།_cats.json',
        '10-4_ཤེས་རབ་ཀྱི་ཕ་རོལ་དུ་ཕྱིན་པ་རྡོ་རྗེ་གཅོད་པའི་དོན་བདུན་གྱི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '17-159_ལས་ཀྱི་སྒྲིབ་པ་རྣམ་པར་སྦྱོང་བའི་ཆོ་ག་བཤད་པ།_cats.json',
        '17-163_དགེ་སློང་གི་དང་པོའི་ལོ་དྲི་བ།_cats.json',
        '11-16_དུས་གསུམ་བརྟག་པ་ཞེས་བྱ་བ།_cats.json',
        '9-10_རྣལ་འབྱོར་སྤྱོད་པའི་ས་ལས་བྱང་ཆུབ་སེམས་དཔའི་ས།_cats.json',
        '9-16_ཆོས་མངོན་པ་ཀུན་ལས་བཏུས་པ།_cats.json',
        '8-10_མཎྜལ་གྱི་ཆོ་ག་ཞེས་བྱ་བ།_cats.json',
        '7-3_དེ་ཁོ་ན་ཉིད་གྲུབ་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '11-10_ཚད་མ་ཀུན་ལས་བཏུས་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '10-23_རྣམ་པར་བཤད་པ་རིགས་པའི་མདོ་སྡེའི་དུམ་བུ་བརྒྱ།_cats.json',
        '17-7_རྡོ་རྗེ་གདན་གྱི་རྡོ་རྗེའི་གླུ།_cats.json',
        '2-8_སེམས་ཀྱི་སྒྲིབ་པ་རྣམ་པར་སྦྱོང་བ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '9-5_དགེ་འདུན་རྗེས་སུ་དྲན་པའི་བཤད་པ།_cats.json',
        '10-32_འདོད་པའི་ཡོན་ཏན་ལྔའི་ཉེས་དམིགས་བཤད་པ།_cats.json',
        '294_དཔལ་ཚོགས་ཀྱི་བདག་པོ་ཞི་བའི་སྒྲུབ་ཐབས།_cats.json',
        '5-8_དབུ་མ་རྩ་བའི་འགྲེལ་པ་ཚིག་གསལ་བ།_cats.json',
        '556_སྐྱེས་པའི་རབས་ཀྱི་རྒྱ་ཆེར་བཤད་པ།_cats.json',
        '8-8_རྣལ་འབྱོར་ལམ་གྱི་སྒྲོལ་མ།_cats.json',
        '541_དགོངས་པ་ཟབ་མོ་ངེས་པར་འགྲེལ་པའི་མདོ་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '10-40_འཕགས་པ་ས་བཅུ་པའི་རྣམ་པར་བཤད་པ།_cats.json',
        '283_ཚ་ཚྭའི་ཆོ་ག།_cats.json',
        '8-9_གསང་བ་ཐུགས་ཀྱི་སྒྲོན་མ།_cats.json',
        '10-19_ཉི་ཤུ་པའི་འགྲེལ་བ།_cats.json',
        '5-2_སྒྲོལ་མ་གསལ་བར་བྱེད་པ་ཞེས་བྱ་བའི་རྒྱ་ཆེེར་བཤད་པ།_cats.json',
        '11-20_ཆོས་མངོན་པའི་འགྲེལ་པ་གནད་ཀྱི་སྒྲོན་མ།_cats.json',
        '10-30_ཚུལ་ཁྲིམས་ཀྱི་གཏམ།_cats.json',
        '12-6_གཏན་ཚིགས་ཀྱི་ཐིགས་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '2-23_ལག་པའི་ཚད་ཀྱི་འགྲེལ་པ།_cats.json',
        '17-29_རྡོ་རྗེ་བདེ་རྒྱས་དབྱངས་ཅན་མའི་སྒྲུབ་ཐབས།_cats.json',
        '7-8_ཀྱེའི་རྡོ་རྗེ་ལས་བྱུང་བའི་ཀུ་རུ་ཀུལླེའི་མན་ངག་ཆེན་པོ་ལྔ།_cats.json',
        '16-2_གཞི་ཐམས་ཅད་ཡོད་པར་སྨྲ་བའི་དགེ་ཚུལ་གྱི་ཚིག་ལེའུར་བྱས་པའི་འགྲེལ་པ་འོད་ལྡན།_cats.json',
        '17-146_སཱཙྪ་ལྔ་གདབ་པའི་ཆོ་ག_cats.json',
        '15-5_ལས་བརྒྱ་རྩ་གཅིག་པ།_cats.json',
        '17-52_འཇིགས་པ་བརྒྱད་ལས་སྐྱོབ་པ་བཞུགས།_cats.json',
        '12-11_རྩོད་པའི་རིགས་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '17-33_རལ་གྲི་གཤིན་རྗེ་གཤེད་གཏུམ་པོའི་སྒྲུབ་ཐབས།_cats.json',
        '7-13_གཙུག་ཏོར་དྲི་མ་མེད་པའི་གཟུངས་བཀླག་པ།_cats.json',
        '17-15_རྡོ་རྗེ་རྣལ་འབྱོར་མ་བསྟོད་པ།_cats.json',
        '10-5_སངས་རྒྱས་རྗེས་སུ་དྲན་པའི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '17-128_ཚོགས་བདག་གི་སྒྲུབ་པ་དབུལ་བའི་གཏེར་སྦྱིན།_cats.json',
        '17-59_བདུད་རྩི་འབྱུང་བ་ཞེས་བྱ་བའི་གཏོར་མའི་ཆོ་ག_cats.json',
        '17-88_མི་དགེ་བ་བཅུའི་ལས་ཀྱི་ལམ་བསྟན་པ།_cats.json',
        '17-71_དབུ་མའི་མན་ངག་ཅེས་བྱ་བ།_cats.json',
        '10-38_ཚིགས་སུ་བཅད་པའི་དོན་བསྡུས་པ།_cats.json',
        '17-36_ཏིང་ངེ་འཛིན་ཚོགས་ཀྱི་ལེའུ།_cats.json',
        '17-87_མདོའི་སྡེའི་དོན་ཀུན་ལས་བཏུས་པའི་མན་ངག_cats.json',
        '17-32_ཁྲོ་བོ་ཐོ་བ་གཤིན་རྗེ་གཤེད་ཀྱི་སྒྲུབ་ཐབས།_cats.json',
        '17-92_ལྟུང་བ་བཤགས་པའི་ཆོ་ག_cats.json',
        '17-124_བསྒྲུབ་བྱ་ཀླུ་རྣམས་ཀྱི་བྱད་དུ་གཞུག་པའི་ཆོ་ག་སྲོག་གཅོད་ཀྱི་སྤུ་གྲི།_cats.json',
        '17-82_བྱང་ཆུབ་སེམས་དཔའ་ལས་དང་པོ་པའི་ལམ་ལ་འཇུག་པ་བསྟན་པ།_cats.json',
        '8-31_ལྷོ་ཟ་མོ་ཚངས་དབྱངས་ལ་སྡུག་བསྔལ་བརྒྱད་ཀྱི་བྱེ་བྲག་བསྟན་པ།_cats.json',
        '7-5_དབུ་མ་རྒྱན་གྱི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '272_དབང་གི་མན་ངག_cats.json',
        '9-12_རྣལ་འབྱོར་སྤྱོད་པའི་ས་རྣམ་པར་གཏན་ལ་དབབ་པ་བསྡུ་པ།_cats.json',
        '8-26_བསྒོམ་རིམ་ཐ་མ།_cats.json',
        '276_སྦྱིན་སྲེག་གི་ཆོ་ག_cats.json',
        '561_ངན་སོང་སྦྱོང་བའི་རོའི་སྦྱིན་སྲེག་གི་དཀྱིལ་ཆོག_cats.json',
        '2-4_དཔལ་གདན་བཞི་པའི་ཟབ་དོན་སྟོན་པ་ཤིང་གཅིག་གི་དཀའ་འགྲེལ་བཞུགས།_cats.json',
        '10-12_མདོ་སྡེའི་རྒྱན་གྱི་བཤད་པ།_cats.json',
        '17-4_དཔལ་འཁོར་སྡོམ་པའི་སྒྲུབ་ཐབས།_cats.json',
        '14-2_བརྒྱད་སྟོང་པའི་བཤད་པ་མངོན་རྟོགས་རྒྱན་གྱི་སྣང་བ།_cats.json',
        '2-36_ལྷ་ཆེན་པོ་གསུམ་གྱི་སྒྲུབ་ཐབས།_cats.json',
        '2-32_རེག་འབིགས་མའི་སྒྲུབ་ཐབས།_cats.json',
        '10-10_འཕགས་པ་ག་ཡ་མགོའི་རི་ཞེས་བྱ་བའི་མདོའི་རྣམ་པར་བཤད་པ།_cats.json',
        '12-1_སངས་རྒྱས་ཡོངས་སུ་མྱ་ངན་ལས་འདས་པ་ལ་བསྟོད་པ།_cats.json',
        '10-31_ཚོགས་ཀྱི་གཏམ།_cats.json',
        '16-1_འཕགས་པ་གཞི་ཐམས་ཅད་ཡོད་པར་སྨྲ་བའི་དགེ་ཚུལ་གྱི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '6-4_སྙིང་པོ་ཡི་གེ་བརྒྱ་པ་པའི་ཆོ་ག_cats.json',
        '17-27_རྡོ་རྗེ་མཁའ་འགྲོ་མ་རྣལ་འབྱོར་མའི་སྒྲུབ་ཐབས།_cats.json',
        '8-34_དེ་ཁོ་ན་ཉིད་བསྡུས་པའི་དཀའ་འགྲེལ།_(A)_cats.json',
        '8-4_རིན་པོ་ཆེ་སྒྲོན་མ།_cats.json',
        '17-40_ལས་ཀྱི་སྒྲིབ་པ་ཐམས་ཅད་རྣམ་པར་འཇོམས་པའི་དཀྱིལ་ཆོག_cats.json',
        '10-24_རྣམ་པར་བཤད་པའི་རིགས་པ།_cats.json',
        '17-54_སྒྲོལ་མའི་སྒྲུབ་ཐབས།_cats.json',
        '9-15_ཐེག་པ་ཆེན་པོ་བསྡུས་པ།_cats.json',
        '11-6_འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་མ་བསྡུས་པའི་ཚིག་ལེའུར་བྱས་པ།_cats.json',
        '558_ཕུང་པོ་ལྔའི་བཤད་པ།_cats.json',
        '8-21_དེ་ཁོ་ན་ཉིད་སྣང་བ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
        '5-11_དབུ་མ་ལ་འཇུག་པའི་བཤད་པ།_cats.json',
        '8-29_རྣམ་པར་མི་རྟོག་པར་འཇུག་པའི་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '8-33_རིགས་པའི་ཐིགས་པའི་ཕྱོགས་སྔ་མ་མདོར་བསྡུས་པ།_cats.json',
        '12-10_ཚད་མ་རྣམ་འགྲེལ་གྱི་འགྲེལ་པ།_cats.json',
        '17-86_རང་གི་བྱ་བའི་རིམ་པ་བསྐུལ་བ་དང་བཅས་པ་ཡི་གེར་བྲིས་པ།_cats.json',
        '17-45_འཕགས་པ་རྟ་མགྲིན་གྱི་སྒྲུབ་ཐབས།_cats.json',
        '543_དགོངས་པ་ཟབ་མོ་ངེས་པར་འགྲེལ་པའི་མདོ་རྒྱ་ཆེར་འགྲེལ་པ།_cats.json',
        '17-35_ཆོས་ཀྱི་དབྱིངས་ལྟ་བའི་གླུ།_cats.json',
        '6-7_བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པའི་སྨོན་ལམ།_cats.json',
        '17-152_འཕགས་མ་སྒྲོལ་མ་ལ་བསྟོད་པ།_cats.json',
        '8-1_མན་ངག་སྐུའི་སྒྲོན་མ།_cats.json',
        '17-1_དཔལ་དགྱེས་པ་རྡོ་རྗེའི་སྒྲུབ་ཐབས་རིན་པོ་ཆེའི་སྒྲོན་མ།_cats.json',
        '8-19_དབུ་མའི་རྒྱན་གྱི་དཀའ་འགྲེལ།_cats.json',
        '10-2_འཕགས་པ་སྒོ་དྲུག་པའི་གཟུངས་ཀྱི་རྣམ་པར་བཤད་པ།_cats.json',
        '2-15_དུག་ལྔ་སྤས་པའི་ལམ་མཆོག་ཏུ་གསང་བ་བམས་གྱིས་མི་ཁྱབ་པ།_cats.json',
        '6-3_བསླབ་པ་ཀུན་ལས་བཏུས་པ།_cats.json',
        '15-3_ཕུང་པོ་ལྔའི་རྣམ་པར་འགྲེལ་པ།_cats.json',
        '9-21_རྣལ་འབྱོར་སྤྱོད་པའི་ས་ལས་ཉན་ཐོས་ཀྱི་ས།_cats.json',
        '9-20_རྣམ་འབྱོར་སྤྱོད་པའི་ས་ལས་དངོས་གཞིའི་ས་མང་པོ།_cats.json',
        '10-33_ཆོས་མངོན་པའི་མཛོད་ཀྱི་བཤད་པ།_(A)_cats.json',
        '5-13_རིགས་པ་དྲུག་ཅུ་པའི་འགྲེལ་པ།_cats.json',
        '10-3_ཤེར་ཕྱིན་འབུམ་པ་དང།_ཉི་ཁྲི་ལྔ་སྟོང་པ་དང།_ཁྲི་བརྒྱད་སྟོང་པའི་རྒྱ་ཆེར་བཤད་པ།_cats.json',
        '13-1_སྟོང་ཕྲག་ཉི་ཤུ་ལྔ་པའི་ཚུལ་གྱི་མངོན་པར་རྟོགས་པའི་རྒྱན་གྱི་འགྲེལ་པ།_cats.json',
        '5-10_དབུ་མ་ལ་འཇུག་པ།_cats.json',
        '10-21_རྟེན་འབྱུང་དང་པོའི་རྣམ་བཤད།_cats.json',
    ]
    exceptions = ['conc_sanity_check.py_cats.json',
                    '10-13_དབུས་དང་མཐའ་རྣམ་པར་འབྱེད་པའི་འགྲེལ་པ།_cats.json',
                  '562_བཅོམ་ལྡན་འདས་ལ་བསྟོད་པ་རྡོ་རྗེ་འཛིན་གྱི་དབྱངས།_cats.json',
                  '5-3_སྦྱོར་བ་ཡན་ལག་དྲུག་པ་ཞེས་བྱ་བའི་འགྲེལ་པ།_cats.json',
                  '12-5_རིགས་པའི་ཐིགས་པ་ཞེས་བྱ་བའི་རབ་ཏུ་བྱེད་པ།_cats.json',
                  '10-20_རང་བཞིན་གསུམ་ངེས་པར་བསྟན་པ།_cats.json',
                  '7-11_སྨོན་ལམ་གྱི་ཁྱད་པར་རྒྱས་པའི་མདོ་སྡེའི་མན་ངག_cats.json',
                  '295_ཚོགས་ཀྱི་བདག་པོའི་གསང་བའི་སྒྲུབ་ཐབས།_cats.json',
                  '311_རྟོགས་དཀའི་སྣང་བ།_cats.json',
                  '14-1_ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྟོང་ཕྲག་ཉི་ཤུ་ལྔ་པ།_(A)_cats.json',  # makes an infinite loop
                  '5-4_རྡོ་རྗེ་སེམས་དཔའི་སྒུབ་ཐབས།_cats.json',  # missing file or directory
                  '17-73_དབུ་མའི་མན་ངག་ཇོ་བོ་རྗེས་མཛད་པ།_cats.json',  # keyerror
                  '271_སྔགས་ཀྱི་དོན་འཇུག་པ།_cats.json',  # idem
                  '17-13_རྡོ་རྗེ་ཕག་མོའི་སྒྲུབ་ཐབས།_cats.json',  # indexerror
                  '4-1_སྒྲོལ་མ་གསལ་བར་བྱེད་པའི་དཀའ་བ་བཏུས་པའི་འགྲེལ་པ།_cats.json',  # indexerror
                  '11-18_གཏན་ཚིགས་ཀྱི་འཁོར་ལོ་གཏན་ལ་དབབ་པ།_cats.json',  # indexerror
                  '566_གྲུབ་མཐའ་བདུན་པ།_cats.json',
                  '10-14_ཆོས་དང་ཆོས་ཉིད་རྣམ་པར་འབྱེད་པའི་འགྲེལ་པ།_cats.json',  # indexerror
                  '17-74_མདོ་ཀུན་ལས་བཏུས་པའི་དོན་བསྡུས་པ།_cats.json',  # indexerror
                  '7-1_བཅོམ་ལྡན་འདས་ལ་བསྟོད་པ་དཔལ་རྡོ་རྗེ་འཛིན་གྱི་དབྱངས།_cats.json',  # idem
                  '7-7_དེ་ཁོ་ན་ཉིད་བསྡུས་པའི་ཚིག་ལེའུར་བྱས་པ།.txt_cats.json',  # idem
                  '42_རིགས་ལྡན་མའི་དེ་ཁོ་ན་ཉིད་ངེས་པ།_cats.json',  # indexerror
                  '15-6_འདུལ་བའི་མདོའི་འགྲེལ།_cats.json',  # infinite loop
                  '17-44_རྣམ་འཇོམས་ཀྱི་སྒྲུབ་ཐབས་བརྒྱ་རྩ་བརྒྱད་གྲགས་པ།_cats.json',  # typeerror
                  ]
    exceptions += finished
    for file_name in os.listdir(in_dir):
        if file_name not in exceptions:
            work_name = file_name.replace('_cats.json', '')
            print(file_name)
            json_structure = jp.decode(open_file(in_dir+file_name))
            reordered_structure = reorder_by_note(json_structure)

            cat_lists = ['automatic__min_mod__min_mod_groups', 'automatic__min_mod__particle_groups', 'automatic__particle_issues__added_particle', 'automatic__particle_issues__agreement_issue', 'automatic__particle_issues__po-bo-pa-ba', 'automatic__particle_issues__different_particles', 'automatic__particle_issues__other', 'automatic__spelling_mistake__missing_vowel', 'automatic__spelling_mistake__nga_da', 'automatic__spelling_mistake__non_word__ill_formed', 'automatic__spelling_mistake__non_word__well_formed', 'automatic__sskrt', 'automatic__verb_difference__diff_tense', 'automatic__verb_difference__diff_verb', 'automatic__verb_difference__not_sure', 'dunno__long_diff', 'dunno__no_diff', 'dunno__short_diff', 'empty_notes']
            debug = False
            output.append(extract_categories(reordered_structure, work_name, cat_list=cat_lists))
    write_file('./output/all_notes.txt', '\n'.join(output))

