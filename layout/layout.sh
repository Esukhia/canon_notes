#!/usr/bin/env bash
# This script takes all .docx files, uses docx2txt to convert all docx files in txt.
# sudo apt-get install docx2txt xlsx2csv
# xlsx2csv requires to escape the spaces in the file names. The easiest is to remove all spaces from file names.

FILES=../4-a-final_formatting/output/3-3-final/*.txt
for f in $FILES
do
  filename="${f#../4-a-final_formatting/output/3-3-final/}"
  filename="${filename%_final.*}"
  echo "Converting $f"
  `pandoc -f markdown -t docx $f -o ./output/$filename.docx`
done