import re
import zipfile
from difflib import ndiff
import tempfile
from subprocess import Popen, PIPE


class MLD:
    def __init__(self, mld=None):
        self.base_string = ''
        self.layers = {}
        self.dependency = []
        self.file_name = ''
        self.metadata = ''

        # if a mld file is passed to the object
        if mld.endswith('.mld'):
            # find the name from the file name
            self.file_name = mld.split('/')[-1].replace('.mld', '')
            # read the zip
            zf = zipfile.ZipFile(mld, 'r')

            # Populate the object variables
            # list the files in the zip
            file_names = zf.namelist()
            # read the base orig_list to base_string
            self.base_string = str(zf.read('base_string'), 'utf-8')
            # populate the layer dict
            layers = [l for l in file_names if re.match('[0-9]+', l)]
            for layer in layers:
                self.layers[layer] = str(zf.read(layer), 'utf-8')
        # if the base orig_list is directly passed to the object
        elif mld:
            self.base_string = mld
        self.base_string = self.base_string.replace('\n', 'ᚻ')

    def flatten(self, string, flattened):
        lines = [(line.split('\t')[0], line.split('\t')[1]) for line in string.split('\n') if line != '']
        idx = 0  # the index of the base orig_list
        val = 1  # the orig_list obtained from the operations
        for index, modif in lines:
            temp = ['', '']  # simulates the key and value to be added to flattened
            if index in flattened:
                temp = [index, flattened[index]]
            operation = modif[0]
            modified = modif[1:]
            if temp[idx] == '':
                temp[idx] = index

            if temp[idx] == '' or index == temp[idx]:
                if operation == 'ᛯ':
                    if temp[val] == '':
                        temp[val] = modified+'ᛝ'
                    else:
                        temp[val] = temp[val][:-1]+modified+temp[val][-1]
                elif operation == 'ᛞ':
                    temp[val] = temp[val][:-1] + modified
                elif operation == 'ᛰ':  # assumes that there is at least one character in the orig_list
                    temp[val] = temp[val][:-1] + 'ᛰ'
            flattened[temp[0]] = temp[1]
        return flattened

    def temp_object(self, content):
        temp = tempfile.NamedTemporaryFile()
        temp.write(str.encode(content))
        temp.flush()
        return temp

    def unix_diff(self, string_a, string_b, windows=False):
        def one_char_per_line(string):
            return '\n'.join(list(string)) + '\n'

        diff_command = 'diff'
        # support for windows
        if windows:
            diff_command = 'third_parties/diff_exe/diff.exe'

        temp_a = self.temp_object(one_char_per_line(string_a))
        temp_b = self.temp_object(one_char_per_line(string_b))

        # diff call
        raw_diff = Popen([diff_command, "--new-line-format=+ %L", "--old-line-format=- %L", "--unchanged-line-format=  %L", temp_a.name, temp_b.name], shell=False, stdout=PIPE)
        raw_diff = bytes.decode(raw_diff.communicate()[0])
        raw_diff = [a for a in raw_diff.split('\n') if a != '']
        temp_a.close()
        temp_b.close()
        return raw_diff

    def create_layer(self, layer_name, modified, use_ndiff=False):
        """
        creates a layer using difflib.ndiff()
        :param modified: modified orig_list
        :return:
        """
        # replace cr to distinguish the
        modified = modified.replace('\n', 'ᚻ')
        # make a diff of both strings with ndiff
        if use_ndiff:
            diff = list(ndiff(self.base_string, modified))
        else:
            diff = self.unix_diff(self.base_string, modified)
        # list all changes, either additions or deletions
        layer = []
        c = 0
        for line in diff:
            operation = line[0] + line[2:]
            # only increment the counter when there is no modification in the current line
            if line.startswith(' '):
                c += 1
            # append the modification found in the current line
            else:
                if line.startswith('+'):
                    layer.append([c, 'ᛯ'+operation[1:]])
                elif line.startswith('-'):
                    # only increment the counter for deletions
                    layer.append([c, 'ᛰ'+operation[1:]])
                    c += 1
        # find replacements and apply them
        c = 0
        while c < len(layer)-1:
            # if current and next operations are on the same index
            if layer[c][0] == layer[c+1][0]:
                # if there is + followed by -
                if 'ᛯ' in layer[c][1] and 'ᛰ' in layer[c+1][1]:
                    layer[c][1] = layer[c][1].replace('ᛯ', 'ᛞ')
                    del layer[c+1]
                    c += 1
                # if there is - followed by +
                elif 'ᛰ' in layer[c][1] and 'ᛯ' in layer[c+1][1]:
                    del layer[c]
                    layer[c][1] = layer[c][1].replace('ᛯ', 'ᛞ')
                    c += 1
                else:
                    c += 1
            else:
                c += 1
        # join the tuples with \t and return the list
        self.layers[layer_name] = '\n'.join([str(i[0])+'\t'+i[1] for i in layer])

    def merge_layers(self, layers):
        merged = {}
        for layer in layers.split('+'):
            merged.update(self.flatten(self.layers[layer], merged))
        return merged

    def export_view(self, layers=''):
        """
        method to export a view of the multi-layered data
        :param layers: provide references of the layers to apply separated by '+'
        :return: a orig_list where none or the specified layers have been applied
        """
        if layers == '':
            return self.base_string
        else:
            merged_layers = self.merge_layers(layers)
            view = ''
            counter = 0
            for num, char in enumerate(self.base_string):
                # searches in all layers if the current index exists
                # todo : try to merge all layers first
                temp = char
                if str(num) in merged_layers:
                    modif = merged_layers[str(num)]
                    # if modif is only 1 char, it can either be a deletion ('ᛰ') or a replacement
                    if len(modif) == 1:
                        if modif == 'ᛰ':
                            # delete the current char
                            temp = ''
                        else:
                            # replace the current char
                            temp = modif
                    # if it has more than a char, 1. either an addition (xxx_), or 2. an addition and a deletion (xxx-) or 3. an addition and a replacement (xxxy)
                    # 1. add modif before the current index char
                    elif modif.endswith('ᛝ'):
                        temp = temp[:-1]+modif[:-1]+temp[-1]
                    # 2. delete current index char
                    elif modif.endswith('ᛰ'):
                        temp = temp[:-1]+modif[:-1]
                    # 3. apply the addition and replace the current index char
                    else:
                        temp = temp[:-1]+modif
                view += temp
            # add the last element in merged_layers if there is one
            last_elt = str(int(num)+1)
            if last_elt in merged_layers:
                view += merged_layers[last_elt][:-1]
            return view.replace('ᚻ', '\n')

    def write_mld(self, file_name):
        with zipfile.ZipFile(file_name+'.mld', 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('base_string', self.base_string)
            for l in self.layers:
                z.writestr(l, self.layers[l])

    def __repr__(self):
        if type(self.base_string) is str:
            # generate a list of the layers
            layers = ' + '.join([key for key in self.layers])

            # generate the first string_len characters separated on a new line every line_len characters
            string_len = 594
            line_len = 200
            start = '\n'.join([self.base_string[:string_len][i:i+line_len] for i in range(0, string_len, line_len)])+'[...]'

            return '\n'.join([layers, start])
        else:
            return 'non-valid file'

'''
Layers:

    flatten_layer()
        input : a layer file
        output : flattens all the operations into a single orig_list following this scheme:
                    z   : replace the char at current index with z
                    xyz : replace the char at current index by z and add xy before the char
                    xyᛝ : keep the char at current index and add xy before it
                    xyᛰ : delete the char at current index and add xy before it
                    ᛰ   : delete the char at current index

    create layer()
        input : - processed base orig_list that contains +, - or = signs and name for the layer
                note : regroup all the characters preceded by a + in a single operation
                - compares  1. either the base orig_list (default) or the provided indexed file
                   and 2. the processed orig_list minus modifications and breaks if different
                - can compare to either an index file (export_indexed() ) or to the base_string
        Action : adds an entry in self.layers with the name and the layer as the key.

    delete layer()
        - deletes the layer corresponding to the name given

    rename_layer()
        input : old_name, new_name


Output:

    export_flattened(suffix, layers)
        generates a txt file with the given suffix.
        The output orig_list is the base orig_list on which the given layers have been applied.
        the raw orig_list is given if layers equals ''


Metadata:

    fields to have :
        id : int, generated number corresponding to the
        name : orig_list, human-readable name
        dependencies : list of names or ids
        author : orig_list
        description : multi-line orig_list
        project : path to a project file (used to copy the meta-data of the file)

'''
'''
layer layout :
    index\tᛯchar    # add a character before index
    index\tᛰchar    # deletes the character at index
    index\tᛞchar    # replaces the character at index
'''



import os
from PyTib.common import open_file, write_file

def reinsert_a(raw_path, with_a_path, with_notes_path):
    for f in os.listdir(raw_path):
        print(f)
        work_name = f.replace('_raw.txt', '')
        raw = open_file('{}/{}_raw.txt'.format(raw_path, work_name))
        with_a = open_file('{}/{}_with_a.txt'.format(with_a_path, work_name))
        with_notes_raw = open_file('{}/{}_post_seg.txt'.format(with_notes_path, work_name))
        if not re.findall(r'\n\[\^[0-9A-Z]+\]\:', with_notes_raw):
            with_notes = with_notes_raw
            notes = ''
        else:
            with_notes, notes = [a for a in re.split(r'((?:\n?\[\^[0-9A-Z]+\]\:[^\n]+\n?)+)', with_notes_raw) if a != '']

        text = MLD(raw)
        text.create_layer('witha', with_a)
        text.create_layer('with_notes', with_notes)
        merged = text.export_view(layers='with_notes+witha')
        write_file('output/2-1-a_reinserted/{}_a_reinserted.txt'.format(work_name), '{}{}'.format(merged, notes))

raw_path = 'output/0-2-raw_text'
with_a_path = 'output/2-0-with_a'
with_notes_path = 'output/1-3-post_seg'
reinsert_a(raw_path, with_a_path, with_notes_path)