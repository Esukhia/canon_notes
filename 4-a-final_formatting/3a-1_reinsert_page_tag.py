from pathlib import Path
from diff_match_patch import diff_match_patch
import re


def make_page_patches(base_str, mod_str):
    patches = dmp.patch_make(base_str, mod_str)
    new_patches = []
    for patch in patches:
        to_apply = False
        new_diffs = []
        for op, text in patch.diffs:
            if '[' in text and ']' in text and op == 1:
                page = re.findall(r'(\\\[.*?\\\])', text)
                if page and len(page) == 1:
                    new_text = page[0]
                    new_diffs.append((op, new_text))
                    to_apply = True
            elif op == 0:
                new_diffs.append((op, text))
        if to_apply:
            patch.diffs = new_diffs
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


def insert_derge_pages(base, modified):
    with_page = Path(modified).read_text()
    with_page = format_page_ref(with_page)

    base = Path(base).read_text()

    page_patches = make_page_patches(base, with_page)
    page_inserted, res = dmp.patch_apply(page_patches, base)
    log = ''
    for num, r in enumerate(res):
        if not r:
            log += f'{num} not applied:\n\t{page_patches[num]}\n'
    return page_inserted, log


def process(base_dir, mod_dir, out_dir):
    base_dir = Path(base_dir)
    mod_dir = Path(mod_dir)
    out_dir = Path(out_dir)

    for base in base_dir.glob('*.txt'):
        toh = base.stem.split('_')[0]
        mod = mod_dir / f'{toh}.txt'
        if mod.is_file():
            out, log = insert_derge_pages(base, mod)
            Path(out_dir / f'{toh}_final.txt').write_text(out)
        else:
            print(mod)


if __name__ == '__main__':
    dmp = diff_match_patch()

    base_dir = 'output/1-3-post_seg/'
    mod_dir = 'output/3a-1-page_refs/'
    out_dir = 'output/3-3-final/'
    process(base_dir, mod_dir, out_dir)
