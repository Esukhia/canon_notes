from PyTib.common import open_file, write_file


def parse_raw(string):
    notes = []
    for num, note in enumerate(string.split('\n---')):
        eds = {}
        for ed in note.strip().split('\n'):
            name, text = ed.strip().split(': ')
            eds[name] = text
        notes.append((num+1, eds))
    return notes


def parse_corrected(string):
    lines = string.split('\n')
    legend = lines[0]
    raw = '\n'.join(lines[1:-1]).split('\n-')  # first two lines are not a note, last line is empty
    notes = {}
    for r in raw:
        note_text = {}
        for n in r.split('\n'):
            if not n.startswith('-'):
                ed, text = n.split(',')[0].split(': ')
                note_text[ed] = text
        note_text = '\n'.join([note_text[a] for a in sorted(note_text)])
        notes[note_text] = r

    return notes, legend


def reorder(raw_yaml, corrected_csv):
    c = 0
    out = {}
    for note in raw_yaml:
        entry = '\n'.join([note[1][a] for a in sorted(note[1])])
        if entry in corrected_csv.keys():
            out[note[0]] = corrected_csv[entry]
        else:
            out[note[0]] = '---\n'+'\n'.join(['*{}: {}'.format(a, note[1][a]) for a in sorted(note[1])])
            c += 1
    print('number of notes that were modified: {}'.format(c))
    return '\n'.join(['{}{}'.format(a, out[a]) for a in sorted(out)])


def main():
    raw = 'i-6-1 བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།_conc.yaml'
    raw_reinserted = open_file('../conc_yaml/{}'.format(raw))
    yaml_notes = parse_raw(raw_reinserted)

    corrected = 'chonjuk - Feuille 1.csv'
    corrected_reinserted = open_file('./{}'.format(corrected))
    csv_notes, legend = parse_corrected(corrected_reinserted)

    reordered = reorder(yaml_notes, csv_notes)
    write_file('reordered.csv', '{}\n{}'.format(legend, reordered))


main()
