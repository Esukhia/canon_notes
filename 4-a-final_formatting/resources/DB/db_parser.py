import csv

# contains authors
with open('table1.csv', newline='') as csvfile:
    table1 = csv.reader(csvfile, delimiter=',', quotechar='"')
    lines1 = [a for a in table1]
    en_header1 = lines1[0]
    cn_header1 = lines1[1]
    del lines1[:2]

# contains the different editions
with open('table2.csv', newline='') as csvfile:
    table2 = csv.reader(csvfile, delimiter=',', quotechar='"')
    lines2 = [a for a in table2]
    en_header2 = lines2[0]
    cn_header2 = lines2[1]
    del lines2[:2]

# only contains Chinese
with open('table3.csv', newline='') as csvfile:
    table3 = csv.reader(csvfile, delimiter=',', quotechar='"')
    lines3 = [a for a in table3]
    en_header3 = lines3[0]
    cn_header3 = lines3[1]
    del lines3[:2]

with open('authors_tib.csv', newline='') as csvfile:
    authors = csv.reader(csvfile, delimiter=',', quotechar='"')
    authors = {a[0]: a[1] for a in authors if a[1] != ''}

print('ok')