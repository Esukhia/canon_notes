from PyTib.common import open_file, write_file, pre_process
import re
from xlwt import Workbook
import os

def is_punct(string):
    # put in common
    if '༄' in string or '༅' in string or '༆' in string or '༇' in string or '༈' in string or \
        '།' in string or '༎' in string or '༏' in string or '༐' in string or '༑' in string or \
        '༔' in string or '_' in string:
        return True
    else:
        return False


def reinsert_notes(raw_text, raw_notes, basis_edition='སྡེ་'):
    raw_text = raw_text.replace('a', '').split('\n')
    raw_notes = raw_notes.strip().split('\n')[1:]

    text = {}
    for t in raw_text:
        parts = re.split(r'([0-9]+)\. ', t)[1:]
        if parts:
            text[parts[0]] = pre_process(parts[1], mode='syls')

    edition_regex = r'《([^《》]+)》'

    # finding all the editions that exist for that text
    edition_names = set([e for r in raw_notes for e in re.findall(edition_regex, r)])
    editions = {basis_edition: []}
    for e in edition_names:
        editions[e] = []

    error = False
    for n in raw_notes:
        #print(n)
        if error:
            break
        parts = n.split(',')
        number = str(int(parts[2])-1)
        # DEBUG. Enables to start debugging at a given note
        note_num = len(raw_notes)-2
        if number == str(note_num-1):
            print('ok')
        page_number = parts[1]
        content = parts[4:]
        note = ''
        # keep track of which edition has already been replaced
        generated_versions = {basis_edition: False}
        for e in edition_names:
            generated_versions[e] = False
        # loop through tuples of (edition-s, note)
        max_pairs = len(content)-1
        if max_pairs > len(content):
            max_pairs = len(content)-1
        tuple_idx = [c for c in range(0, max_pairs) if c % 2 == 0]
        for a in tuple_idx:
            if error:
                break
            if content[a]:
            # filters the cases where the second tuple is empty
                note = content[a+1]
                if '(' in note:
                    print('there is a note on top of the comparison.')
                    print('\t'.join(parts))
                    note = note.split('(')[0].strip()
                if '《' in note:
                    print('The following note needs to be edited. The execution will stop now.')
                    print('\t'.join(parts))
                    error = True
                    break
                # 0 prepare
                # separate in syllables not separating the fusioned particles
                modif_type = ''
                if note.startswith('m'):
                    modif_type = 'm'
                elif note.startswith('p'):
                    modif_type = 'p'
                version = pre_process(note.replace(modif_type, ''), mode='syls')
                # delete the last element in the list of the note
                #if is_punct(version[-1]):
                if is_punct(version[-1]) and len(version) > 1:
                    del version[-1]
                    # reconstitute the punctuation for comparing the syllables:

                    # add a tsek to it if the original text has one
                    # if the last syllable is not a punctuation
                    if not version[-1].endswith('་'):
                        if not is_punct(text[number][-1]):
                            if not text[number][-1].endswith('་'):
                                version[-1] += '་'
                        # if the last syllable is a punctuation
                        else:
                            if text[number][-2].endswith('་'):
                                version[-1] += '་'

                # 1 find index
                # 1.a
                # find the index of the syllable from which to start replacing the original
                index = len(text[number]) - len(version)
                # go one syllable left if the last syllable of the original text is a punctuation
                if is_punct(text[number][-1]):
                    index -= 1
                # put the index at 0 if the replacement text is longer than the original
                if index < 0:
                    index = 0

                # 1.b
                # try to find a point of correspondence in case there are more than a few syllables that are added
                orig_sync_idx = False
                version_sync_idx = False
                window_size = 4
                maximum = len(text[number]) - 1
                # attempts_num becomes 0 if window_size is larger than the length of version, making window_indexes an empty list.
                # this way, window_size decides wether we search for a syncronisation point or not.
                attempts_num = len(version[window_size:])
                window_indexes = [(a, a + window_size) for a in range(attempts_num)]
                for v_w in window_indexes:
                    for a_n in range(attempts_num):
                        orig_window = text[number][maximum - window_size - a_n:maximum - a_n]
                        version_window = version[v_w[0]:v_w[1]]
                        if orig_window == version_window:
                            if not orig_sync_idx:
                                orig_sync_idx = maximum - window_size - a_n
                                version_sync_idx = v_w[0]

                # finding the sync point if it is the last syllable
                if not orig_sync_idx:
                    # detects which of the two syls is the longest to check if both start the same way
                    if len(text[number][-1]) > len(version[0]):
                        long = text[number][-1]
                        short = version[0].rstrip('་')
                    else:
                        long = version[0]
                        short = text[number][-1].rstrip('་')
                    # finds if long is short with an addition. This deals with བདེའང་ being replaced by བདེ་བའང་.
                    # Todo: similar replacements may occur elsewhere than the last syllable. implementation needed.
                    # in case both syllables are identical, the condition is also met.
                    if short in long:
                        orig_sync_idx = len(text[number])-1
                        version_sync_idx = 0

                # 2
                # generating the versions of the different editions
                edition_text = [b for b in text[number]]

                # A.1 for subsequent addition, keep the last syllable if it is a punctuation to add it at the end
                edition_text_last_syl = False
                if is_punct(edition_text[-1]):
                    edition_text_last_syl = edition_text[-1]

                # remove the ending tsek in version if it was not there in the original
                if edition_text[-1].endswith('་'):
                    if not version[-1].endswith('་'):
                        version[-1] += '་'
                    if version[-1].endswith('ང'):
                        version[-1] += '་'
                else:
                    if version[-1].endswith('་') and not version[-1].endswith('ང་'):
                        version[-1] = version[-1].rstrip('་')

                # 2.1 if the operation is a deletion (m stands for minus)
                if modif_type == 'm':
                    # a if there is a synchronizing point between the original and the version
                    if orig_sync_idx:
                        del edition_text[orig_sync_idx:]
                    # b if there is no sync point
                    else:
                        del edition_text[len(edition_text)-len(version):]

                # 2.2 if the operation is an addition (p stands for plus)
                elif modif_type == 'p':
                    # a if there is a synchronizing point between the original and the version
                    if orig_sync_idx:
                        # replace the part that precedes the synchronising point
                        edition_text[orig_sync_idx - version_sync_idx:orig_sync_idx] = version[:version_sync_idx]
                        # replacing from the synchronising point onwards
                        edition_text[orig_sync_idx:] = version[version_sync_idx:]
                    # b if there is no sync point
                    else:
                        # add a tsek if there is none on the last syllable
                        if not edition_text[-1].endswith('་'):
                            edition_text[-1] += '་'
                            # remove the ending tsek of version
                            if version[-1].endswith('་'):
                                version[-1] = version[-1].rstrip('་')
                        edition_text.extend(version)

                # 2.3 if the operation is a replacement
                else:
                    if orig_sync_idx:
                        # replace the part that precedes the synchronising point
                        edition_text[orig_sync_idx - version_sync_idx:orig_sync_idx] = version[:version_sync_idx]
                        # replacing from the synchronising point onwards
                        edition_text[orig_sync_idx:] = version[version_sync_idx:]
                        # 2.b if there is no synchronising point
                    else:
                        for e in range(len(version)):
                            edition_text[len(edition_text) - len(version) + e] = version[e]

                # A.2 add the punctuation to the end if needed
                # if a punctuation was saved in A.1 and if it is not the same as the last syllable of edition_text
                if edition_text_last_syl and edition_text_last_syl != edition_text[-1]:
                    # if the last syllable ends with a tsek
                    if edition_text[-1].endswith('་'):
                        # if there is a ང་
                        if not edition_text[-1].endswith('ང་'):
                            edition_text[-1] = edition_text[-1][:-1]
                    edition_text.append(edition_text_last_syl)


                # 2.4 if a sync point was found, i.e. if the size of version is longer than window_size,
                # add '%' to manually check the replacement has been correctly done
                #if orig_sync_idx:
                #    edition_text[-1] += '%'

                # 3 Add the text to the respective editions
                #
                edition_refs = re.findall(edition_regex, content[a])
                # 3.a add the versions of all the editions that require modifications from Derge and notify the edition is added
                for e in edition_refs:
                    chunk = ''.join(edition_text)
                    # remove the extra spaces inserted between the shad and the next verse
                    chunk = chunk.replace('_།_', '_།').replace('།__།', '།  །')
                    editions[e].append((chunk, len(version), page_number, note))
                    generated_versions[e] = True

        # 3.b add the original version of the text to the remaining
        for g in generated_versions:
            if not generated_versions[g]:
                chunk = ''.join(text[number])
                # remove the extra spaces inserted between the shad and the next verse
                chunk = chunk.replace('_།_', '_།').replace('།__།', '།  །')
                editions[g].append((chunk, '', page_number, note))

    # 4 add the last bit of the text that corresponds to no note
    for g in editions:
        chunk = ''.join(text[str(len(text))])
        chunk = chunk.replace('_།_', '_།').replace('།__།', '།  །')
        editions[g].append((chunk, '', '', ''))
        print(editions[g][-1])
    return editions


def generate_versions(text_name, notes_name, in_dir='input', out_dir='output', left=10):
    in_dir += '/'
    editions = reinsert_notes(open_file(in_dir+text_name), open_file(in_dir+notes_name))
    work_name = text_name.split('.')[0].replace(' ', '_')

    # writing all the editions in their respective folder
    for e in editions:
        path = out_dir+'/'+e+'/'
        file_name = work_name+'_'+e+'.txt'
        content = ''.join([e[0] for e in editions[e]]).replace('_', ' ')
        write_file(path+file_name, content)

    # generating the spreadsheet showing the changes
    wb = Workbook()
    sheet1 = wb.add_sheet('Sheet 1')

    ed_names = [a for a in editions if a != 'སྡེ་']
    num_notes = len(editions['སྡེ་'])
    line_number = 0
    for a in range(num_notes):
        # the versions
        modifs = []
        modif_len = 0
        for ed in ed_names:
            modif_chunk = pre_process(editions[ed][a][0].replace('_', ' '), mode='syls')
            modif_size = editions[ed][a][1]
            if modif_size != '':
                ed_start = len(modif_chunk)-modif_size
                if ed_start - left > 0:
                    ed_start -= left
                else:
                    ed_start = 0
                modif = ''.join(modif_chunk[ed_start:])
            else:
                modif = ''#'༡པ།'
            modifs.append((ed, modif))
            # find the length of the modification (take the longest modification)
            if editions[ed][a][1] != '' and modif_len < editions[ed][a][1]:
                modif_len = editions[ed][a][1]
        modifs = sorted(modifs)

        # from Derge
        orig_chunk = pre_process(editions['སྡེ་'][a][0], mode='syls')
        start = len(orig_chunk) - modif_len
        if start - left > 0:
            start -= left
        else:
            start = 0
        orig_modif = orig_chunk[start:]
        page = editions['སྡེ་'][a][2]
        if page != '':
            sheet1.write(line_number, 0, 'ཤོག་གྲངས་'+page+'པར་ཡོད་པའི་མཆན་' + str(a + 2) + 'པ།')
        else:
            sheet1.write(line_number, 0, 'མཆན་'+str(a+2)+'པ།')
        sheet1.write(line_number, 1, '༼སྡེ་༽ '+''.join(orig_modif))
        sheet1.write(line_number, 2, editions['སྡེ་'][a][3])
        sheet1.write(line_number, 3, ''.join(orig_chunk))
        line_number += 1
        for num, m in enumerate(modifs):
            sheet1.write(line_number, num, '༼'+m[0]+'༽ '+m[1])
        line_number += 2
    wb.save(out_dir+'/'+work_name+'_ཞུས་དག་ཆེད།.xls')

# put in this list the pairs of works and their respective notes

#works = [a.split('\t') for a in open_file('./note-text_correspondance.csv').strip().split('\n')]
works = [('i-1-92 རྩོད་པ་བཟློག་པའི་ཚིག་ལེའུར་བྱས་པ།.txt', '1-92 རྩོད་པ་བཟློག་པའི་ཚིག་ལེའུར་བྱས་པ།.csv'),
        ('i-5-10 དབུ་མ་ལ་འཇུག་པ།.txt', '5-10 དབུ་མ་ལ་འཇུག་པ།.csv'),
        ('i-1-88 རིགས་པ་དྲུག་ཅུ་པའི་ཚིག་ལེའུར་བྱས་པ།.txt', '1-88 རིགས་པ་དྲུག་ཅུ་པའི་ཚིག་ལེའུར་བྱས་པ།.csv')]

for w in works:
    print(w[0])
    generate_versions(w[0], w[1])
