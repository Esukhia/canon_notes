#### Format of layered texts

Each layered text will comprise of:
- a base text: the raw Derge edition ("InDesign files" in the Esukhia workflow)
- reconstructed versions of all editions available for the text excepting Derge
- layout texts using the base text on which linebreaks and pagebreaks are inserted
- a note-categorisation file in json (output of categorisation.py)
- the Esukhia final version with reinserted notes (only for the first few texts fully processed)
 
note: Approximately 3% of all the reconstructed and reinserted notes suffer from wrong reinsertion. This comes from the fact the original note format was not thought for being processed in a script. They were designed to be just long enough for a human reader to reconstruct the passage.

##### Naming conventions
- base text: `<text>_base.txt`
- edition versions: `<text>_<edition>_derge_layer.txt`
- layout texts: `<text>_<edition>_layout.txt`
- note-categorisation files: `<text>_cats.json`
- final version: `<text>_final.txt`

