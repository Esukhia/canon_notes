What is This Project?
=====================

Project Goal
------------

Tackle the problem HHDL raised about the Peydurma. Something along the lines of "It is great, but it is not friendly for a regular reader. Plus, a lot of the notes are minor spelling mistakes/divergences that can very easily dealt with, thus greatly reducing the noise and improving readability."

### Input

Text (docx) + notes (xlsx) file pairs for every text in the Nalanda corpus.

### Output

The regular user-friendly version of each text in two formats (docx and layered text)

Strategy:
---------

-   input all the Peydurma notes for the whole collection in xlsx files

-   get a clean Derge version of each text in the collection

-   mark it with the note number so as to have a "copy" of the Peydurma files

-   reinsert the marks in the text

-   check for evident spelling mistakes and select the right spelling (noise reduction)

-   apply heuristics to discard un-necessary notes, ideally keeping only the notes that affect the understanding of a given passage. (noise reduction)

-   go from syllable-based notes to word-based notes to improve readability (and modify sufficiently Peydurma to not have copyright problems. leverages pytib)

-   improve the note format to increase readability

-   provide a layered version of the final document for an online platform where users/scholars will be able to give feedback/provide choices between notes

How is it done?
===============

-1 Before canon-notes
---------------------

Where: Files are a bit scattered all over the place [here](https://drive.google.com/drive/folders/0B7LZlj4jGHpLTjhCTXVYaVNPYmc) and [here](https://github.com/Esukhia/nalanda-corpus).

Esukhia team in Dharamsala has produced the following for every text:

-   text.docx contains:

-   raw text

-   page numbers in Derge edition

-   note information from Peydurma

-   text.xlsx contains:

-   note mark corresponding to what is found in text.docx

-   note content: what every edition says

-   notes added by the Esukhia staff (to be detected and ignored)

-   formatting (color/background/size that has simply been ignored)

Issues:

1.  notes number discrepancies: sizes of docx and xlsx don't correspond, ...

1.  strategy: see where the scripts fail and manually detect and correct files

3.  the notes added by Esukhia staff has to be identified and ignored

1.  strategy implemented by Rabten: put all of them on the F row since there can't possibly be any note that far)

5.  files were produced alongside the work was done, so the naming conventions are not consistent and my attempt to create a unified format met opposition with Tibetans.

0 Preparing input
-----------------

As shown in [this Drawing](https://docs.google.com/drawings/d/10VGIbmooQOT_Z2N73QP_1fGZe093BuOvEEtFvPmCi7s/edit), and lines 1 to 10 of [this table](https://docs.google.com/spreadsheets/d/1BdArgkswmSREsrig7CTl--H7kX_eqqqgdwxwcbxAQnw/edit#gid=0), the docx and xlsx have to be converted to txt and csv files using [this script](https://github.com/Esukhia/nalanda-corpus/blob/master/%E0%BC%A1%E0%BC%BD%20%E0%BD%98%E0%BD%82%E0%BD%BC%E0%BD%93%E0%BC%8B%E0%BD%94%E0%BD%BC%E0%BC%8B%E0%BD%80%E0%BE%B3%E0%BD%B4%E0%BC%8B%E0%BD%A6%E0%BE%92%E0%BE%B2%E0%BD%B4%E0%BD%96%E0%BC%8D/docx_txt.sh). The output files are then copied in canon-notes/1-a-reinsert_notes/input.

Issues:

1 Reinserting notes
-------------------

-   csv_contains_pardrang.py:

detects and deletes an additional column preventing the correct execution of reinsertion.py

-   reinsertion.py:

loops over every pair of txt+csv files and attempts to reconstruct the passage for every of the existing editions for a given note.

The aim is ultimately to reconstruct digital versions of all the editions from the txt file using the notes.

[output/comparison_xls/ ](https://github.com/Esukhia/canon_notes/tree/latest/1-a-reinsert_notes/output/comparison_xls)was the first attempt of reinsertion. It has better formatting than the yaml counterparts in [conc_yaml/](https://github.com/Esukhia/canon_notes/tree/latest/1-a-reinsert_notes/output/conc_yaml), but is not used in the workflow.

output/unified_structure/ contains a version of every text segmented in syllables.

Every syllable subjected to a note is a yaml dict with the editions as keys, a list of syllables as values. It is used as the single-source-of-truth for all the workflow from that point onwards.

2 Automatic Categorisation
--------------------------

The rationale is to automatise as much as possible the process of categorising notes and enriching them with the relevant information so that human reviewers of each note will have the maximum information at hand, without having to resort to external sources such as dictionaries, verb lexicons, etc.

This implies the categorisation is going to be modified/enhanced by humans, before moving to the next step, but this has never happened.

First, segment.py is ran, to produce a segmented version of the different editions, which will then individually checked for spelling mistakes, etc. (the whole categorization script)

I hoped that for each file, the segmentation is reviewed by a human to reduce to the maximum the bad segmentations and thus reduce false positives and inaccuracies in the categorisation (based of words rather than syllables). I have processed a few files like that, but it implies a lot of manual work.

categorisation.py includes many different things, out of which the figures of n-gram frequencies in the Kangyur for all segmenting mistakes detected by pytib.

3 Revision format
-----------------

The rationale is explained [here](https://docs.google.com/document/d/1vnwMYS_ZXcNwoGefX9vH9oKMg3iFNMzZOXsmIMDOY7M/edit#heading=h.j8jssqobvma).

parse_json.py creates the "revision interface" that presents the alternatives of a given notes with left and right context (word-based, not syllable based as in the docx and xlsx or Peydurma). It also includes some information gathered during the automatic categorisation and provides a column where the reviewer will put his final decision for a given note.

Notes in a text are grouped by type so the reviewing process is more effective and comparing similar notes or adjusting decisions is easier.

parse_json.py also produced an updated version of the "unified_structure" from 1-a-reinsert_notes/output/unified_structure

An example is [here](https://docs.google.com/spreadsheets/d/1BX5lj_8YygGspIseRBM14bAYoVr6s-x0sDTRc3TljbM/edit#gid=1304534009) or any other tab of the same document (I manually processed them). The choices are encoded in the letters of DUCK in the "new" column.

An unimplemented attempt to automatize the DUCKing process based on heuristics is described [here](https://docs.google.com/presentation/d/1kU7lzTpAb-cBLSApH6VjGOUxLRzvNnsxVTkwHtb7PNo/edit#slide=id.p). The most difficult choices would then be left for scholars, while the easiest ones could be applied automatically, thus achieving the aim of reducing the noise of unnecessary notes.

create_ducked.py takes as input the output of parse_json in output/antconc_format/, applies a K(eep note) default choice to mimic what I have manually done in the Google Spreadsheet and allow to continue the workflow.

4 Final Formatting
------------------

0-1_apply_note_choices.py: applies the note choices in the DUCKed file onto the updated_structure to have the final edition.

0-2_rawify.py: create a version of the text without any formatting, segmented on shad and spaces (for later comparison)

1-1_unmark.py: creates a version of the text without note marks so as not to hinder segmentation and spell check in subsequent step.

1-2_segment_final.py: use pytib to find any newly introduced spelling errors/inaccuracies, and propose pre-formatted notes in case we want to correct the spelling.

1-3_copy_post_seg.py: glueware to ensure manually modified files do not overwrite the ones generated automatically.

2-1_reinsert_a.py: get the line breaks("a"s) from the Derge Kangyur (eKangyur) and apply them on our final edition.

3-1_reinsert_page_nums.py: take the data from resources/དཀར་ཆག་ཀུན་གསལ་མེ་ལོང་། - format example.csv (contains the pagination information compiled from various sources by NT)

and infers the exact page start location, number and side in the Derge Edition (wanted by the Geshe at Namgyal Tratsang). (this implies the titles of each work corresponds to the name of our files, so implies some manual work)

3-3_copy_final.py: glueware that puts the result of the whole workflow in output/3-3-final/ (any file [here](https://github.com/Esukhia/canon_notes/tree/nagarjuna/4-a-final_formatting/output/3-3-final), for ex)

files [here](https://github.com/Esukhia/canon_notes/tree/nagarjuna/4-a-final_formatting/output/stats) provide statistics oriented towards estimating the risk of having copyright problems (amount of similar notes) and a visual representation of text where syllables are converted to dots and the modified syllables bear the letter of the DUCKing decision that was made.

layout
------

contains a .sh script to convert the final files into docx files with page + side marks and the notes reformatted and DUCKed.

Any question or remark is welcome!

the latest branch of canon-notes includes all the data for the whole Nalanda corpus, while the nagarjuna branch focuses on this specific author. It was meant as a work basis with Rabten, but the Indian internet connection forced me to create a "code" branch, that is stripped of all data files.
