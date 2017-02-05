from PyTib.common import open_file, write_file, tib_sort

content = open_file('17_Panditas_Text_List_grouped.csv').split('\n')
fields = [a.split(',') for a in content]
rows = [tib_sort([b for b in a if b != '']) for a in fields]
write_file('sorted_authors.csv', '\n'.join([','.join(a) for a in rows]))
print('ok')