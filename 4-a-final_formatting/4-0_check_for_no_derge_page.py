from pathlib import Path
import re

to_check = Path('output/3-3-final').glob('*.txt')

REGEX = r'([༠༡༢༣༤༥༦༧༨༩]+[བན]\\\])'

no_page = []
for f in to_check:
    content = f.read_text()
    matches = re.findall(REGEX, content)
    if not matches:
        no_page.append(f.name)
        out_file = Path('output/4-0-find_with_out_derge_page/derge_page_missing') / f.name
        out_file.write_text(content)
    else:
        out_file = Path('output/4-0-find_with_out_derge_page/to_check') / f.name
        out_file.write_text(content)

print('ok')
print('\n'.join(no_page))
