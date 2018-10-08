from pathlib import Path
import re
import csv

input_folder = Path('../1-a-reinsert_notes/input')
txt = sorted(list(input_folder.glob('*.txt')))
Csv = sorted(list(input_folder.glob('*.csv')))


# Common checks
def check_csv_txt_pairs():
    """
    Each work must be a pair of a .txt and a .Csv file
    Checks for empty files and removes them for the following checking functions
    """
    txts = [t.stem for t in txt]
    csvs = [c.stem for c in Csv]
    csv_only = [c+'.csv' for c in csvs if c not in txts]
    txt_only = [t+'.txt' for t in txts if t not in csvs]

    # empty files
    empty = []
    for a in txt + Csv:
        content = a.read_text(encoding='utf-8-sig').strip()
        if not content:
            empty.append(a.name)
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
            total.append((a.name, bad))

    # formatting
    out = ''
    for filename, pairs in total:
        out += f'\n\t\t{filename}'
        for pair in pairs:
            out += f'\n\t\t\t{pair[0]}-->{pair[1]} (expected: {pair[0]}-->{pair[0]+1})'
    return f'\n4. Checking note sequence in txt files:' \
           f'\n\t{len(total)} files have bad sequences:{out}\n'


# 2. test Csv files
def check_csv_line_nums():
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
        # if not c.stem.startswith('11-10_'):
        #     continue
        content = list(csv.reader(c.open(newline='')))

        # delete ending empty rows
        if is_empty(content[-1]):
            while is_empty(content[-1]):
                del content[-1]
            csv.writer(c.open(mode='w', newline='', encoding='utf-8-sig')).writerows(content)

        mismatches = []
        previous = 0
        for row in content:
            try:
                line_num = int(row[2])
                if previous + 1 != line_num:
                    mismatches.append((previous, line_num))
                previous = line_num
            except ValueError:
                mismatches.append((previous, row[2]))
                previous += 1
        if mismatches:
            total.append((c.name, mismatches))

    out = ''
    for filename, pairs in total:
        out += f'\n\t\t{filename}'
        for prev, nxt in pairs:
            out += f'\n\t\t\t\t{prev}-->{nxt} (expected: {prev}-->{prev+1})'
    return f'\n5. Checking note sequence in csv files:' \
           f'\n\t{len(total)} files have bad sequences:{out}\n'


if __name__ == '__main__':
    log = ''
    log += check_csv_txt_pairs()
    log += check_empty_lines()
    log += check_txt_formatting()
    log += check_txt_note_sequence()
    log += check_csv_line_nums()
    print('ok')
    Path('log.txt').write_text(log, encoding='utf-8-sig')
