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
            print(note_num)
            if note_num == 40:
                print('ok')
            # find the syllable that precede and follow the current note
            # left_side, right_side = find_contexts(unified, counter, conc_length=20)
            # left_string = ''.join(left_side)
            # right_string = ''.join(right_side)

            # find the conc syllables from the manually checked notes in notes{}
            index = str(note_num)
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

        #write_file('output/antconc_format/{}_antconc_format.txt'.format(text_name), '\n'.join(out))
        final = '\n'.join(out)
        return final


if __name__ == '__main__':
    #in_dir = '../2-b-manually_corrected_automatic_categorisation/'
    in_dir = '../2-automatic_categorisation/output/'
    output = []
    for file_name in os.listdir(in_dir):
        if file_name == '1-དབུ་མ།_དབུ་མ་རྩ་བའི་ཚིག་ལེའུར་བྱས་པ་ཤེས་རབ།_cats.json':
            work_name = file_name.replace('_cats.json', '')
            print(file_name)
            json_structure = jp.decode(open_file(in_dir+file_name))
            reordered_structure = reorder_by_note(json_structure)

            cat_lists = ['automatic__min_mod__min_mod_groups', 'automatic__min_mod__particle_groups', 'automatic__particle_issues__added_particle', 'automatic__particle_issues__agreement_issue', 'automatic__particle_issues__po-bo-pa-ba', 'automatic__particle_issues__different_particles', 'automatic__particle_issues__other', 'automatic__spelling_mistake__missing_vowel', 'automatic__spelling_mistake__nga_da', 'automatic__spelling_mistake__non_word__ill_formed', 'automatic__spelling_mistake__non_word__well_formed', 'automatic__sskrt', 'automatic__verb_difference__diff_tense', 'automatic__verb_difference__diff_verb', 'automatic__verb_difference__not_sure', 'dunno__long_diff', 'dunno__no_diff', 'dunno__short_diff', 'empty_notes']

            output.append(extract_categories(reordered_structure, work_name, cat_list=cat_lists))
    write_file('./output/all_notes.txt', '\n'.join(output))

