import jsonpickle as jp
from collections import defaultdict
from PyTib.common import open_file, write_file, pre_process, de_pre_process
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


def contextualised_text(notes, file_name, uni_struct_dir='../1-a-reinsert_notes/output/unified_structure'):
    # finding the differing syllables from the manually checked concordance
    differing_syls = find_note_text(notes)
    # loading the structure
    unified_structure = yaml.load(open_file('{}/{}'.format(uni_struct_dir, file_name.replace('_conc_corrected.csv', '_unified_structure.yaml'))))

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
    # turn the complex structure into a simple dict
    categorised = {}
    categorised['automatic__min_mod__min_mod_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['min_mod_groups'])
    categorised['automatic__min_mod__particle_groups'] = flat_list_dicts(nested_dict['automatic_categorisation']['min_mod']['particle_groups'])
    categorised['automatic__particle_issues__added_particle'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['added_particle'])
    categorised['automatic__particle_issues__agreement_issue'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['agreement_issue'])
    categorised['automatic__particle_issues__dagdra_po'] = flat_list_dicts(nested_dict['automatic_categorisation']['particle_issues']['dagdra_po'])
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
    in_dir = '../2-b-manually_corrected_automatic_categorisation/'
    for file_name in os.listdir(in_dir):
        json_structure = jp.decode(open_file(in_dir+file_name))
        reordered_structure = reorder_by_note(json_structure)