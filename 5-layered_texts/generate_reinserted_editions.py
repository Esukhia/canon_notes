import os
import re
import yaml
from PyTib.common import open_file, write_file


def find_ed_names(structure):
    """
    Finds all editions except Derge that is already in the base text
    (also takes out ཞོལ་པར་མ་ as it is a mistake from Esukhia workers for the Tengyur)
    :return:
    """
    names = []
    for el in structure:
        if type(el) is not dict:
            pass
        else:
            names = [a for a in el.keys() if a != 'སྡེ་' and a != 'ཞོལ་']
            break
    return names


def reconstruct_edition_versions(structure):
    ed_names = find_ed_names(structure)
    reconstructed = {ed: '' for ed in ed_names}
    for syl in structure:
        if type(syl) == dict:
            for ed in ed_names:
                reconstructed[ed] += ''.join(syl[ed])
        else:
            for ed in ed_names:
                reconstructed[ed] += syl
    return reconstructed


def reconstruct_version_texts(in_path):
    for f in os.listdir(in_path):
        text_name = f.strip('_updated_structure.txt')
        # create a folder for the layered files if missing
        if text_name in os.listdir('output'):
            current_out_folder = 'output/' + text_name
            # open structure file
            from_structure = yaml.load(open_file('{}/{}'.format(in_path, f)))
            # reconstruct the editions
            editions = reconstruct_edition_versions(from_structure)
            # write them in the corresponding folder
            for ed, version in editions.items():
                version = version.replace('_', ' ')  # reconstruct spaces
                write_file('{}/{}_{}_layer.txt'.format(current_out_folder, text_name, ed), version)


def create_dirs(jsons, structures, raws, derge_layouts, with_as):
    json_files = [a.replace('_cats.json', '') for a in os.listdir(jsons)]
    structure_files = [a.replace('_updated_structure.txt', '') for a in os.listdir(structures)]
    raw_files = [a.replace('_raw.txt', '') for a in os.listdir(raws)]
    try:
        derge_layout_files = [a.replace('_raw_page_reinserted.txt', '') for a in os.listdir(derge_layouts)]
    except FileNotFoundError:
        return
    with_a_files = [a.replace('_with_a.txt', '') for a in os.listdir(with_as)]

    for f in structure_files:
        if f in json_files and f in raw_files and (f in derge_layout_files or f in with_a_files):
            if not os.path.exists('output/' + f):
                os.makedirs('output/' + f)


def create_base_text(raw_path):
    for f in os.listdir('output'):
        content = open_file('{}/{}_raw.txt'.format(raw_path, f))
        # put back in a single line
        content = content.replace('\n', ' ')
        write_file('output/{}/{}_base.txt'.format(f, f), content)


def copy_cat_json_file(json_path):
    for f in os.listdir('output'):
        write_file('output/{}/{}'.format(f, f+'_cats.json'), open_file('{}/{}_cats.json'.format(json_path, f)))


def copy_final_version(final_path):
    for f in os.listdir('output'):
        if f+'_final.txt' in os.listdir('../4-a-final_formatting/output/3-3-final'):
            write_file('output/{}/{}'.format(f, f+'_final.txt'), open_file('{}/{}_final.txt'.format(final_path, f)))


def copy_derge_layout(derge_layout):
    for f in os.listdir('output'):
        no_layout = True
        if f in [a.replace('_raw_page_reinserted.txt', '') for a in os.listdir(derge_layout)]:
            content = open_file('{}/{}_raw_page_reinserted.txt'.format(derge_layout, f))
            reformated = re.sub(r'\n-+', '', content).replace('\\', '')
            write_file('output/{}/{}'.format(f, f+'_derge_layout.txt'), reformated)
            no_layout = False
        if no_layout and f in [a.replace('_with_a.txt', '') for a in os.listdir('../4-a-final_formatting/output/2-0-with_a')]:
            content = open_file('../4-a-final_formatting/output/2-0-with_a/{}_with_a.txt'.format(f))
            reformated = content.replace('\n', ' ').replace('a', '\n')
            write_file('output/{}/{}'.format(f, f + '_derge_lines.txt'), reformated)


def main():
    to_process = ['1-རྒྱུད།_ཀླུའི་དབང་ཕྱུག་རྒྱལ་པོའི་སྒྲུབ་ཐབས།', '1-རྒྱུད།_ཀླུ་སྒྲུབ་ཀྱི་གླུ།', '1-སྐྱེས་རབས།_སྦྱིན་པའི་གཏམ།', '1-རྒྱུད།_གོས་སྔོན་པོ་ཅན་གྱི་དངོས་གྲུབ་ཉེ་བ།', '1-སྐྱེས་རབས།_རྒྱལ་པོ་གཏམ་བྱ་བ་རིན་པོ་ཆེའི་ཕྲེང་བ།', '1-རྒྱུད།_སྒྲུབ་པའི་ཐབས་མདོར་བྱས་པ།', '1-སྐྱེས་རབས།_སྲིད་པ་ལས་འདས་པའི་གཏམ།', '1-སྐྱེས་རབས།_རྨི་ལམ་ཡིད་བཞིན་ནོར་བུའི་གཏམ།', '1-རྒྱུད།_སྔགས་ཀྱི་རྒྱན་གྱི་སྒྲུབ་ཐབས།', '1-རྒྱུད།_འཇམ་དཔལ་རྡོ་རྗེ་བློ་གྲོས་འཕེལ་བ།']

    cats_json_path = '../2-automatic_categorisation/output'
    struct_path = '../3-a-revision_format/output/updated_structure'
    raw_texts_path = '../4-a-final_formatting/output/0-2-raw_text'
    final_path = '../4-a-final_formatting/output/3-3-final'
    derge_pages_path = '../4-a-final_formatting/output/2-2-raw_page_reinserted'
    with_a_path = '../4-a-final_formatting/output/2-0-with_a/'
    # create output directories for all texts to be processed
    create_dirs(cats_json_path, struct_path, raw_texts_path, derge_pages_path, with_a_path)
    # create the derge layout version
    copy_derge_layout(derge_pages_path)
    # create the base text
    create_base_text(raw_texts_path)
    # copy the categorisations in json format
    copy_cat_json_file(cats_json_path)
    # copy the final version
    #copy_final_version(final_path)
    # reconstruct versions for each text
    reconstruct_version_texts(struct_path)
    # Todo implement a function that outputs the lines that are close to a multiple of the average line length
    # reconstruct Derge layout


main()
