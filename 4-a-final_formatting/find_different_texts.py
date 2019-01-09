from pathlib import Path

from multiprocessing import Pool
from jellyfish import jaro_winkler

n_path = Path('output/1-3-post_seg')
d_path = Path('output/3a-1-page_refs')

nalanda = [p.stem.replace('_post_seg', '') for p in n_path.glob('*.txt') if p.stem.startswith('D')]
derge_tengyur = [p.stem for p in d_path.glob('*.txt')]

missing_nalanda = [n for n in nalanda if n not in derge_tengyur]
print('\n'.join(missing_nalanda))
nalanda = [n for n in nalanda if n in derge_tengyur]


def get_distance(name):
    n_content = Path(n_path / str(name + '_post_seg.txt')).read_text(encoding='utf-8-sig')
    n_content = n_content.strip().split(':', maxsplit=1)[0]
    d_content = Path(d_path / str(name + '.txt')).read_text(encoding='utf-8-sig')
    d_content = d_content.strip()
    l_dist = jaro_winkler(n_content, d_content)
    percent = int(l_dist * 100)
    print(name, ':', percent)
    return (percent, name)


distances = []
with Pool(4) as p:
    distances.append(p.map(get_distance, nalanda))

# for n in nalanda:
#     n_content = Path(n_path / str(n + '_post_seg.txt')).read_text(encoding='utf-8-sig')
#     n_content = n_content.strip()
#     d_content = Path(d_path / str(n + '.txt')).read_text(encoding='utf-8-sig')
#     d_content = d_content.strip()
#     l_dist = jaro_winkler(n_content, d_content)
#     percent = int(l_dist * 100)
#     distances.append((percent, n))

distances = sorted(distances, reverse=True)
Path('distances.csv').write_text('percent,work' + '\n'.join([f'{b},{a}' for a, b in distances]))
print('ok')
