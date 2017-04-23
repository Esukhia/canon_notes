import os

structure = {
    'txt_raw': ('1-a-reinsert_notes/input', '.txt'),
    'conc_raw': ('1-a-reinsert_notes/output/conc_yaml', '_conc.txt'),
    'structure_raw': ('1-a-reinsert_notes/output/unified_structure', '_unified_structure.yaml'),
    'conc_corrected': ('1-b-manually_corrected_conc/notes_formatted', '_conc-corrected.txt'),
    'categorised': ('2-automatic_categorisation/output', '_cats.json'),
    'segmented': ('2-automatic_categorisation/segmented', '_segmented.txt'),
    'to_DUCK': ('3-a-revision_format/output/antconc_format', '_antconc_format.txt'),
    'structure_updated': ('3-a-revision_format/output/updated_structure', '_updated_structure.txt'),
    'DUCKed': ('3-b-reviewed_texts', '_DUCKed.csv'),
    '4_formatted': ('4-a-final_formatting/output/0-1-formatted', '_formatted.txt'),
    '4_raw': ('4-a-final_formatting/output/0-2-raw_text', '_raw.txt'),
    '4_corrected': ('4-a-final_formatting/output/0-3-corrected', '_corrected.txt'),
    '4_unmarked': ('4-a-final_formatting/output/1-1-unmarked', '_unmarked.txt'),
    '4_segmented': ('4-a-final_formatting/output/1-2-segmented', '_segmented.txt'),
    '4_post_seg': ('4-a-final_formatting/output/1-3-post_seg', '_post_seg.txt'),
    '4_with_a': ('4-a-final_formatting/output/2-0-with_a', '_with_a.txt'),
    '4_a_reinserted': ('4-a-final_formatting/output/2-1-a_reinserted', '_a_reinserted.txt'),
    '4_page_reinserted_raw': ('4-a-final_formatting/output/2-2-raw_page_reinserted', '_raw_page_reinserted.txt'),
    '4_page_reinserted': ('4-a-final_formatting/output/3-1-page_reinserted', '_page_reinserted.txt'),
    '4_compared': ('4-a-final_formatting/output/3-2-compared', '_compared.txt'),
    '4_extra': ('4-a-final_formatting/output/3-2-compared/extra_copies', ''),
    '4_final': ('4-a-final_formatting/output/3-3-final', '_final.txt'),
    '4_stats': ('4-a-final_formatting/output/stats', '_stats.txt'),
    '4_docx': ('layout/output', '.docx')
}


def find_intersection(section1, section2):
    list1 = [a.replace(structure[section1][1], '') for a in os.listdir(structure[section1][0])]
    list2 = [a.replace(structure[section2][1], '') for a in os.listdir(structure[section2][0])]
    set1 = set(list1)
    set2 = set(list2)
    return set2.symmetric_difference(set1)

print(int(len(os.listdir(structure['txt_raw'][0]))/2), ': txt_raw')
print(len(os.listdir(structure['conc_raw'][0])), ': conc_raw')
print(len(os.listdir(structure['structure_raw'][0])), ': structure_raw')
print(len(os.listdir(structure['segmented'][0])), ': segmented')
print(find_intersection('conc_raw', 'conc_corrected'))
print(len(os.listdir(structure['conc_corrected'][0])), ': conc_corrected')
print(len(os.listdir(structure['categorised'][0])), ': categorised')

print(len(os.listdir(structure['to_DUCK'][0])), ': to_DUCK')
print(len(os.listdir(structure['structure_updated'][0])), ': structure_updated')
print(len(os.listdir(structure['DUCKed'][0])), ': DUCKed')
print(len(os.listdir(structure['4_formatted'][0])), ': 4_formatted')
print(len(os.listdir(structure['4_corrected'][0])), ': 4_corrected')
print(len(os.listdir(structure['4_unmarked'][0])), ': 4_unmarked')
print(len(os.listdir(structure['4_segmented'][0])), ': 4_segmented')
print(len(os.listdir(structure['4_post_seg'][0])), ': 4_post_seg')
print(len(os.listdir(structure['4_with_a'][0])), ': 4_with_a')
print(len(os.listdir(structure['4_a_reinserted'][0])), ': 4_a_reinserted')
print(len(os.listdir(structure['4_page_reinserted_raw'][0])), ': 4_page_reinserted_raw')
print(len(os.listdir(structure['4_page_reinserted'][0])), ': 4_page_reinserted')
print(len(os.listdir(structure['4_compared'][0])), ': 4_compared')
print(len(os.listdir(structure['4_extra'][0])), ': 4_extra')
print(len(os.listdir(structure['4_final'][0])), ': 4_final')
print(len(os.listdir(structure['4_stats'][0])), ': 4_stats')
print(len(os.listdir(structure['4_docx'][0])), ': 4_docx')