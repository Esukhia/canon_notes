from collections import defaultdict
from pathlib import Path
import re
import csv

input_folder = Path('../1-a-reinsert_notes/input')
txt = sorted(list(input_folder.glob('*.txt')))
Csv = sorted(list(input_folder.glob('*.csv')))

issues = 0
files = defaultdict(int)


# Common checks
def check_csv_txt_pairs():
    global issues, files
    """
    Each work must be a pair of a .txt and a .Csv file
    Checks for empty files and removes them for the following checking functions
    """
    txts = [t.stem for t in txt]
    csvs = [c.stem for c in Csv]
    csv_only = [c+'.csv' for c in csvs if c not in txts]
    txt_only = [t+'.txt' for t in txts if t not in csvs]
    issues += len(csv_only) + len(txt_only)
    for a in csv_only + txt_only:
        files[a] += 1

    # empty files
    empty = []
    for a in txt + Csv:
        content = a.read_text(encoding='utf-8-sig').strip()
        if not content:
            empty.append(a.name)
            issues += 1
            files[a.name] += 1
            if a in txt:
                txt.remove(a)
            else:
                Csv.remove(a)

    # formatting
    out_csv = '\n\t\t'.join(csv_only)
    out_txt = '\n\t\t'.join(txt_only)
    emptys = '\n\t\t' + '\n\t\t'.join(empty)
    return f'1. Checking file pairs:' \
           f'\n\t{len(csv_only)} txt files missing:\n\t\t{out_csv}' \
           f'\n\t{len(txt_only)} Csv files missing:\n{out_txt}' \
           f'\n\t{len(empty)} empty files:{emptys}\n\n'


def check_empty_lines():
    global issues, files
    """
    No empty lines are allowed in either .txt or .Csv files
    """
    total = []
    for a in txt + Csv:
        content = a.read_text(encoding='utf-8-sig').split('\n')
        lines = []
        for num, line in enumerate(content[:-1]):
            if line == '':
                lines.append(num + 1)
        if lines:
            total.append((a.name, lines))
            issues += len(lines)
            files[a.name] += 1
        # remove ending empty lines
        if content and len(content) >= 2 and content[-2].strip() == '':
            while content and len(content) >= 2 and content[-2].strip() == '':
                del content[-2]
            a.write_text('\n'.join(content), encoding='utf-8-sig')

    # formatting
    out = ''
    for t in total:
        out += f'\n\t\t{t[0]}'
        out += '\n\t\t\t{}'.format('\n\t\t\t'.join(sorted([str(a) for a in t[1]])))
    return f'2. Checking empty lines:' \
           f'\n\t{len(total)} files have empty lines:{out}\n\n'


# Check .txt files
def check_txt_formatting():
    global issues, files
    """
    Each .txt file must be formatted as follows:
        - int + ".": the note number
        - " ": a space delimiter
        - string: the
    """
    line_format = r'[0-9]+\. .+'

    total = []
    for a in txt:
        content = a.read_text(encoding='utf-8-sig').split('\n')
        if content[-1] == '':
            del content[-1]

        # replace tabs instead of spaces and write new content
        if re.findall(r'[0-9]+\.\t.+', content[0]):
            content = [a.replace('.\t', '. ') for a in content]
            a.write_text('\n'.join(content), encoding='utf-8-sig')

        bad = []
        for num, line in enumerate(content):
            if not re.findall(line_format, line) and num + 1 != len(content):
                if len(line) > 50:
                    line = line[:50] + '(...)'
                bad.append((num + 1, line))
        if bad:
            issues += len(bad)
            files[a.name] += 1
            total.append((a.name, bad))

    # formatting
    out = ''
    for filename, lines in total:
        out += f'\n\t\t{filename}'
        for num, line in lines:
            out += f'\n\t\t\tn. {num}: "{line}"'
    return f'3. Checking txt file format:' \
           f'\n\t{len(total)} files are badly formatted:{out}\n'


def check_txt_note_sequence():
    global issues, files
    total = []
    for a in txt:
        content = a.read_text(encoding='utf-8-sig').split('\n')
        if content[-1] == '':
            del content[-1]

        bad = []
        previous_num = 0
        for line in content:
            current_num = re.findall(r'^[0-9]+', line)
            if current_num:
                current_num = int(current_num[0])
                if current_num != previous_num + 1:
                    bad.append((previous_num, current_num))
                previous_num = current_num
        if bad:
            issues += len(bad)
            files[a.name] += 1
            total.append((a.name, bad))

    # formatting
    out = ''
    for filename, pairs in total:
        out += f'\n\t\t{filename}'
        for pair in pairs:
            out += f'\n\t\t\t{pair[0]}-->{pair[1]} (expected: {pair[0]}-->{pair[0]+1})'
    return f'\n4. Checking note sequence in txt files:' \
           f'\n\t{len(total)} files have bad sequences:{out}\n'


def check_number(previous, current, mismatches):
    try:
        line_num = int(current)
        if previous + 1 != line_num:
            mismatches.append([previous, line_num])
        previous = line_num
    except ValueError:
        mismatches.append([previous, current])
        previous += 1
    return previous


# 2. test Csv files
def check_csv_line_nums():
    global issues, files
    """
    Checks if the line numbers are correct
    Deletes any trailing empty rows
    """
    def is_empty(row):
        empty = True
        for r in row:
            if r.strip():
                empty = False
        return empty

    total = []
    for c in Csv:
        content = list(csv.reader(c.open(newline='')))

        # delete ending empty rows
        if is_empty(content[-1]):
            while is_empty(content[-1]):
                del content[-1]
            csv.writer(c.open(mode='w', newline='', encoding='utf-8-sig')).writerows(content)

        mismatches = []
        previous = 0
        for row in content:
            previous = check_number(previous, row[2], mismatches)
        if mismatches:
            total.append((c.name, mismatches))
            issues += len(mismatches)
            files[c.name] += 1

    out = ''
    for filename, pairs in total:
        out += f'\n\t\t{filename}'
        for prev, nxt in pairs:
            out += f'\n\t\t\t\t{prev}-->{nxt} (expected: {prev}-->{prev+1})'
    return f'\n5. Checking line sequence in csv files:' \
           f'\n\t{len(total)} files have bad sequences:{out}\n'


def check_csv_note_nums():
    global issues, files
    """
    Checks the sequences of notes in csv files
    """
    note_total = []
    page_total = []
    for c in Csv:
        content = list(csv.reader(c.open(newline='')))

        note_mismatches = []
        page_mismatches = []
        prev_note = 0
        prev_page = -1
        for row in content[1:]:
            if prev_page == -1:
                try:
                    prev_page = int(content[1][1])
                except ValueError:
                    prev_page = 0
            else:
                if row[1].strip():
                    prev_page = check_number(prev_page, row[1], page_mismatches)
                    prev_note = 0

            prev_note = check_number(prev_note, row[3], note_mismatches)
            if note_mismatches and len(note_mismatches[-1]) == 2:
                note_mismatches[-1] = [prev_page] + note_mismatches[-1]
        if note_mismatches:
            note_total.append((c.name, note_mismatches))
            issues += len(note_mismatches)
            files[c.name] += 1
        if page_mismatches:
            page_total.append((c.name, page_mismatches))
            issues += len(note_mismatches)
            files[c.name] += 1


    out = ''
    # out += f'\n\t{len(page_total)} files have bad page sequences:\n'
    # for filename, pairs in page_total:
    #     out += f'\n\t\t{filename}'
    #     for prev, nxt in pairs:
    #         out += f'\n\t\t\t\t{prev}-->{nxt} (expected: {prev}-->{prev+1})'
    out += f'\n\n\t{len(note_total)} files have bad note sequences:'
    for filename, pairs in note_total:
        out += f'\n\t\t{filename}'
        for note, prev, nxt in pairs:
            out += f'\n\t\t\t\tpage {note} — {prev}-->{nxt} (expected: {prev}-->{prev+1})'
    return f'\n6. Checking note sequence in csv files:{out}\n'


def check_note_quantities():
    global issues, files
    stems = defaultdict(int)
    for a in txt + Csv:
        stems[a.stem] += 1

    total = []
    for t in txt:
        if t.stem not in stems and stems[t.stem] != 2:
            continue
        txt_lines = t.read_text(encoding='utf-8-sig').strip().split('\n')
        csv_lines = Path(str(t).replace('.txt', '.csv')).read_text(encoding='utf-8-sig').strip().split('\n')
        txt_num, csv_num = (len(txt_lines), len(csv_lines))
        if txt_num != csv_num:
            total.append(f'\n\t\t{str(abs(txt_num - csv_num)).zfill(3)} missing. txt: {str(txt_num).zfill(5)}; '
                         f'csv: {str(csv_num).zfill(5)} notes: {t.stem}')
            issues += abs(txt_num - csv_num)
            files[t.name] += 1
    return f'\n7. Checking how many notes in txt and csv:' \
           f'{"".join(total)}\n'


if __name__ == '__main__':
    log = ''
    log += check_csv_txt_pairs()
    log += check_empty_lines()
    log += check_txt_formatting()
    log += check_txt_note_sequence()
    log += check_csv_line_nums()
    log += check_csv_note_nums()
    log += check_note_quantities()
    log = f'{issues} issues in {len(files)} files.\n\n{log}'
    print('ok')
    Path('log.txt').write_text(log, encoding='utf-8-sig')
