import os

structure = [
    '1-a-reinsert_notes',
    '1-a-reinsert_notes/input',
    '1-a-reinsert_notes/output',
    '1-a-reinsert_notes/output/comparison_xls',
    '1-a-reinsert_notes/output/conc_yaml',
    '1-a-reinsert_notes/output/mistakes',
    '1-a-reinsert_notes/output/unified_structure',
    '1-b-manually_corrected_conc/notes_formatted',
    '1-b-manually_corrected_conc',
    '1-b-manually_corrected_conc/notes_formatted',
    '2-automatic_categorisation',
    '2-automatic_categorisation/output',
    '2-automatic_categorisation/segmented',
    '2-b-manually_corrected_automatic_categorisation',
    '3-a-revision_format',
    '3-a-revision_format/output',
    '3-a-revision_format/output/antconc_format',
    '3-a-revision_format/output/updated_structure',
    '3-b-reviewed_texts',
    '4-a-final_formatting',
    '4-a-final_formatting/output',
    '4-a-final_formatting/output/0-1-formatted',
    '4-a-final_formatting/output/0-2-raw_text',
    '4-a-final_formatting/output/0-3-corrected',
    '4-a-final_formatting/output/1-1-unmarked',
    '4-a-final_formatting/output/1-2-segmented',
    '4-a-final_formatting/output/1-3-post_seg',
    '4-a-final_formatting/output/2-0-with_a',
    '4-a-final_formatting/output/2-1-a_reinserted',
    '4-a-final_formatting/output/2-2-raw_page_reinserted',
    '4-a-final_formatting/output/3-0-pdfs',
    '4-a-final_formatting/output/3-1-page_reinserted',
    '4-a-final_formatting/output/3-2-compared',
    '4-a-final_formatting/output/3-2-compared/extra_copies',
    '4-a-final_formatting/output/3-3-final',
    '4-a-final_formatting/output/stats',
    '5-layered_texts',
    '5-layered_texts/output',
    'layout',
    'layout/output'
]

for folder in structure:
    if not os.path.exists(folder):
        os.makedirs(folder)
