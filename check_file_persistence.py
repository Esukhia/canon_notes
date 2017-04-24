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
    '4_final': ('4-a-final_formatting/output/3-3-final', '_final.txt'),
    '4_stats': ('4-a-final_formatting/output/stats', '_stats.txt'),
    '4_docx': ('layout/output', '.docx')
}


def find_intersection(section1, section2):
    list1 = [a.replace(structure[section1][1], '') for a in os.listdir(structure[section1][0])]
    list2 = [a.replace(structure[section2][1], '') for a in os.listdir(structure[section2][0])]
    set1 = set(list1)
    set2 = set(list2)
    diff1 = list(set2.difference(set1))
    diff2 = list(set1.difference(set2))
    return '< '+'\n< '.join(diff1) + '\n> '+'\n> '.join(diff2)

# 1 reinsertion
print(len(os.listdir(structure['txt_raw'][0])), ': txt_raw')
#print(find_intersection('txt_raw', 'conc_raw'))

print(len(os.listdir(structure['conc_raw'][0])), ': conc_raw')
print(find_intersection('conc_raw', 'structure_raw'))

print(len(os.listdir(structure['structure_raw'][0])), ': structure_raw')
print(find_intersection('structure_raw', 'conc_corrected'))

# manually corrected
print(len(os.listdir(structure['conc_corrected'][0])), ': conc_corrected')
print(find_intersection('conc_corrected', 'categorised'))

# 2 categorisation
print(len(os.listdir(structure['categorised'][0])), ': categorised')
print(find_intersection('conc_corrected', 'to_DUCK'))

# 3 DUCK
print(len(os.listdir(structure['to_DUCK'][0])), ': to_DUCK')
print(find_intersection('to_DUCK', 'structure_updated'))

print(len(os.listdir(structure['structure_updated'][0])), ': structure_updated')
print(find_intersection('structure_updated', 'DUCKed'))

# assumed K
print(len(os.listdir(structure['DUCKed'][0])), ': DUCKed')
print(find_intersection('DUCKed', '4_formatted'))

# 4
print(len(os.listdir(structure['4_formatted'][0])), ': 4_formatted')
print(find_intersection('4_formatted', '4_raw'))

print(len(os.listdir(structure['4_raw'][0])), ': 4_raw')
print(find_intersection('4_raw', '4_corrected'))

print(len(os.listdir(structure['4_corrected'][0])), ': 4_corrected')
print(find_intersection('4_corrected', '4_unmarked'))

print(len(os.listdir(structure['4_unmarked'][0])), ': 4_unmarked')
print(find_intersection('4_unmarked', '4_segmented'))

print(len(os.listdir(structure['4_segmented'][0])), ': 4_segmented')
print(find_intersection('4_segmented', '4_post_seg'))

print(len(os.listdir(structure['4_post_seg'][0])), ': 4_post_seg')
print(find_intersection('4_post_seg', '4_with_a'))

print(len(os.listdir(structure['4_with_a'][0])), ': 4_with_a')
print(find_intersection('4_with_a', '4_a_reinserted'))

print(len(os.listdir(structure['4_a_reinserted'][0])), ': 4_a_reinserted')
print(find_intersection('4_a_reinserted', '4_page_reinserted_raw'))

print(len(os.listdir(structure['4_page_reinserted_raw'][0])), ': 4_page_reinserted_raw')
print(find_intersection('4_page_reinserted_raw', '4_page_reinserted'))

print(len(os.listdir(structure['4_page_reinserted'][0])), ': 4_page_reinserted')
print(find_intersection('4_page_reinserted', '4_compared'))

print(len(os.listdir(structure['4_compared'][0])), ': 4_compared')
print(find_intersection('4_compared', '4_final'))

print(len(os.listdir(structure['4_final'][0])), ': 4_final')
print(find_intersection('4_final', '4_docx'))

print(len(os.listdir(structure['4_docx'][0])), ': 4_docx')