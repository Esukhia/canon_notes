from pathlib import Path
from formated_dmp import FormattedDMP as diff_match_patch
# from diff_match_patch import diff_match_patch
import re


def is_notemark_diff(diff):
    op, text = diff
    text = text.replace('\n', '')
    decision = False
    if '[' in text or ']' in text:

        decision = True

    return decision


def match_notemark(text):
    regex = r'(\[\^[0-9]+K\])'
    match = re.findall(regex, text)
    return match[0] if match else None


def clean_patches(orig_patches, is_needed_diff, find_needed):
    """
    Selects and cleans a given patch list using functions given as arguments
    Intended for patches generated by Google's diff_match_patch module.

    :param orig_patches: original set of patches
    :type orig_patches: patch objects created with DMP.patch_make(str, str)
    :param is_needed_diff: test to see if a diff contains a wanted modification
    :type is_needed_diff: funct returning a boolean
    :param find_needed: finds the parts of the diff that are to keep
    :type find_needed: funct returning the replacement str
    :return: filtered set of patches that only contain the needed modifications
    """
    new_patches = []
    for patch in orig_patches:
        keep = False
        new_diffs = []
        for diff in patch.diffs:

            # Important: keep the diffs with no modification used as context
            # (used by DMP to calculate the correct patching location)
            if diff[0] == 0:
                new_diffs.append(diff)

            # find diff to modify
            elif is_needed_diff(diff):
                op, text = diff
                if text == '\n།རྣམས་':
                    print('ok')
                needed = find_needed(text)
                if needed:
                    new_diffs.append((op, needed))
                    keep = True

        # select only relevant patches
        if keep:
            patch.diffs = new_diffs  # replace the old diffs with the modified ones
            new_patches.append(patch)

    return new_patches


def format_page_ref(string):
    replacement = [('1', '༡'), ('2', '༢'), ('3', '༣'), ('4', '༤'), ('5', '༥'),
                   ('6', '༦'), ('7', '༧'), ('8', '༨'), ('9', '༩'), ('0', '༠'),
                   ('a', 'ན'), ('b', 'བ')]
    chunks = re.split(r'(\[.*?\])', string)
    i = 0
    while i < len(chunks):
        if '[' in chunks[i]:
            c = chunks[i].replace('[', '\[').replace(']', '\]')
            for x, y in replacement:
                c = c.replace(x, y)
            chunks[i] = c
        i += 1

    return ''.join(chunks)


def insert_corrections(base, modified):
    # 0. prepare
    # input from derge-tengyur: with pages + corrections
    with_page = Path(modified).read_text()
    with_page = format_page_ref(with_page)

    # 1. get the corrections in base
    base, notes = Path(base).read_text().rsplit('\n\n', maxsplit=1)

    patches = dmp.patch_make(with_page, base)
    # 2. apply note patches

    page_patches = clean_patches(patches, is_notemark_diff, match_notemark)
    page_inserted, res = dmp.patch_apply(page_patches, with_page)
    log = ''
    for num, r in enumerate(res):
        if not r and num < len(page_patches):
            log += f'{num} not applied:\n\t{dmp.decode_patch(str(page_patches[num]))}\n'

    page_inserted += '\n\n' + notes
    return page_inserted, log


def process(base_dir, mod_dir, out_dir):
    base_dir = Path(base_dir)
    mod_dir = Path(mod_dir)
    out_dir = Path(out_dir)

    for base in base_dir.glob('*.txt'):
        if 'D1133' in base.stem:
            print('ok')
        else:
            continue
        toh = base.stem.split('_')[0]
        mod = mod_dir / f'{toh}.txt'
        if mod.is_file():
            print(mod)
            out, log = insert_corrections(base, mod)
            Path(out_dir / f'{toh}_final.txt').write_text(out)
            if log:
                Path(out_dir / f'{toh}_final.log').write_text(log)
        else:
            print(mod)


if __name__ == '__main__':
    dmp = diff_match_patch()

    base_dir = 'output/1-3-post_seg/'
    mod_dir = 'output/3a-1-page_refs/'
    out_dir = 'output/3-3-final'
    process(base_dir, mod_dir, out_dir)
