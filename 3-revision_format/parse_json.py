import jsonpickle as jp
from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process, tib_sort
import PyTib
import copy
import os
import re
import yaml
import simplejson as json

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False, parse_int=True)
seg = PyTib.Segment()
components = PyTib.getSylComponents()
collection_eds = list


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


def contextualised_text(notes, differing_syls, unified_structure, text_name):

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
    for num, u in enumerate(unified_structure):
        if type(u) == dict:
            if str(c+1) in differing_syls.keys():
                # data structure in the spreadsheet
                # left, note, right, min_mod, particle_issues, spelling_mistake, sskrt, verb_difference, dunno, manual_cat, profile, ngram_freq
                struct = ['', '', '', '', '', '', '', '', '', '', '', '', '', '']
                left = [''.join(u['སྡེ་']) if type(u) == dict else u for u in unified_structure[num - 10:num]]
                right = [''.join(u['སྡེ་']) if type(u) == dict else u for u in unified_structure[num + 1:num + 11]]

                ### prepare note
                note_num = str(c+1)
                note_texts = differing_syls[note_num][0]
                note_profile = notes[note_num]['profile']
                note_freq = notes[note_num]['ngram_freq']
                note_other_cats = [a for a in notes[note_num] if a not in ['ngram_freq', 'profile', 'ngram_freq', 'note']]  # all the other categories

                text_string = ', '.join([k+': '+v for k, v in sorted(note_texts.items())])
                text_string = text_string.replace('པེ་:', 'p').replace('སྡེ་:', 'd').replace('སྣར་:', 'n').replace('ཅོ་:', 'c')
                profile_string = ' '.join(note_profile)
                profile_string = profile_string.replace('པེ་', 'p').replace('སྡེ་', 'd').replace('སྣར་', 'n').replace('ཅོ་', 'c')
                freq_string = ''
                for k, v in sorted(note_freq.items()):
                    tm = []
                    for a in v:
                        tm.append('{}({})'.format(a[0], a[1]))
                    freq_string += '{}: {}'.format(k, ', '.join(tm))
                freq_string = freq_string.replace('པེ་:', 'p').replace('སྡེ་:', 'd').replace('སྣར་:', 'n').replace('ཅོ་:', 'c')

                struct[0] = ''.join(left).replace('_', ' ')
                struct[1] = text_string
                struct[2] = ''.join(right).replace('_', ' ')
                for o in note_other_cats:
                    if o.startswith('automatic__min_mod'):
                        struct[3] = o
                    if o.startswith('automatic__particle_issues'):
                        struct[4] = o
                    if o.startswith('automatic__spelling_mistake'):
                        struct[5] = o
                    if o.startswith('automatic__sskrt'):
                        struct[6] = o
                    if o.startswith('automatic__verb_difference'):
                        struct[7] = o
                    if o.startswith('dunno'):
                        struct[8] = o
                struct[10] = profile_string
                struct[11] = freq_string
                struct[12] = note_num
                struct[13] = text_name
                note = '\t'.join(struct)

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
    return '\n'.join(out)


def extract_categories(notes, text_name, cat_list=False):
    def find_cat_notes(notes, cat):
        differing_syls = {}  # {'note_num': ( {texts}, (left, right))}
        for k, v in notes.items():
            if k != 'Stats' and cat in v.keys():
                editions = v['note']
                context = (editions['སྡེ་'][0], editions['སྡེ་'][2])
                for e in editions:
                    editions[e] = editions[e][1]
                differing_syls[k] = (editions, context)
        return differing_syls
    all_categories = ['automatic__min_mod__min_mod_groups', 'automatic__min_mod__particle_groups', 'automatic__particle_issues__added_particle', 'automatic__particle_issues__agreement_issue', 'automatic__particle_issues__dagdra_po', 'automatic__particle_issues__different_particles', 'automatic__particle_issues__other', 'automatic__spelling_mistake__missing_vowel', 'automatic__spelling_mistake__nga_da', 'automatic__spelling_mistake__non_word__ill_formed', 'automatic__spelling_mistake__non_word__well_formed', 'automatic__sskrt', 'automatic__verb_difference__diff_tense', 'automatic__verb_difference__diff_verb', 'automatic__verb_difference__not_sure', 'dunno__long_diff', 'dunno__no_diff', 'dunno__short_diff', 'empty_notes']
    # loading the structure
    unified_structure = yaml.load(open_file('../1-a-reinsert_notes/output/unified_structure/{}'.format(text_name+'_unified_structure.yaml')))
    if not cat_list:
        for cat in all_categories:
            syls = find_cat_notes(notes, cat)
            if syls:
                out = contextualised_text(notes, syls, unified_structure, text_name)
                write_file('output/antconc_format/{}_{}_antconc_format.txt'.format(text_name, cat), out)
    else:
        out = []
        for cat in cat_list:
            syls = find_cat_notes(notes, cat)
            if syls:
                out.append(contextualised_text(notes, syls, unified_structure, text_name))

        #write_file('output/antconc_format/{}_antconc_format.txt'.format(text_name), '\n'.join(out))
        return '\n'.join(out)


def sorted_strnum(thing):
    '''
    if thing is a dict, it works like dict.items() : it returns a list of key, value tuples.
    :param thing:
    :return:
    '''
    if type(thing) == dict:
        out = []
        for el in sorted(thing, key=lambda x: int(x)):
            out.append((el, thing[el]))
        return out
    else:
        return sorted(thing, key=lambda x: int(x))


def flat_list_dicts(l):
    if l != []:
        return {k: v for a in l for k, v in a.items()}
    else:
        return {}


def reorder_by_note(nested_dict):
    # turn the complex structure into a 1-level-dict
    categorised = {}
    categorised['automatic__min_mod__min_mod_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['min_mod_groups'])
    categorised['automatic__min_mod__particle_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['particle_groups'])
    categorised['automatic__particle_issues__added_particle'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['added_particle'])
    categorised['automatic__particle_issues__agreement_issue'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['agreement_issue'])
    categorised['automatic__particle_issues__dagdra_po'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['po-bo-pa-ba'])
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
    # reinsert the notes in the new structure
    for note_num in sorted_strnum([a for a in nested_dict['profile'].keys()]):
        for cat in categorised:
            if note_num in categorised[cat] and cat != 'profile' and cat != 'ngram_freq':
                if len(categorised[cat][note_num]) == 2:
                    n = categorised[cat][note_num][1]
                else:
                    n = categorised[cat][note_num][0]
                reordered_notes[note_num] = {'note': n}


    # create dict structure with
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


if __name__ == '__main__':
    #in_dir = '../2-b-manually_corrected_automatic_categorisation/'
    in_dir = '../2-automatic_categorisation/output/'
    output = []
    for file_name in os.listdir(in_dir):
        work_name = file_name.replace('_cats.json', '')
        print(file_name)
        json_structure = jp.decode(open_file(in_dir+file_name))
        reordered_structure = reorder_by_note(json_structure)

        cat_lists = ['automatic__min_mod__min_mod_groups', 'automatic__min_mod__particle_groups', 'automatic__particle_issues__added_particle', 'automatic__particle_issues__agreement_issue', 'automatic__particle_issues__dagdra_po', 'automatic__particle_issues__different_particles', 'automatic__particle_issues__other', 'automatic__spelling_mistake__missing_vowel', 'automatic__spelling_mistake__nga_da', 'automatic__spelling_mistake__non_word__ill_formed', 'automatic__spelling_mistake__non_word__well_formed', 'automatic__sskrt', 'automatic__verb_difference__diff_tense', 'automatic__verb_difference__diff_verb', 'automatic__verb_difference__not_sure', 'dunno__long_diff', 'dunno__no_diff', 'dunno__short_diff', 'empty_notes']

        output.append(extract_categories(reordered_structure, work_name, cat_list=cat_lists))
    write_file('./output/all_notes.txt', '\n'.join(output))

