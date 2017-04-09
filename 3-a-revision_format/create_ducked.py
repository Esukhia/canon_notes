from PyTib.common import open_file, write_file
import os


in_path = 'output/antconc_format'
out_path = '../3-b-reviewed_texts'
for f in os.listdir(in_path):
    name = f.replace('_antconc_format.txt', '')
    print(name)

    content = open_file('{}/{}'.format(in_path, f)).strip()
    lines = content.split('\n')

    output = ['Left,p,c,d,n,right,new,min_mod,particles,spelling_mistake,sskrt,verb,?,empty,double,profile,ngram_freq,file name,note_num']
    for line in lines:
        columns = line.split('\t')
        columns[6] = 'K'
        output.append(','.join(columns))
    write_file('{}/{}_DUCKed.csv'.format(out_path, name), '\n'.join(output))
