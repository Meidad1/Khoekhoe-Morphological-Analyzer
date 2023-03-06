# Khoekhoe-Morphological-Analyzer
This program consists of two main modules: preprocessing (cleaning and segmentation into morphemes) and glossing (i.e., morphological analysis).

________________________________________________________________________________
PREPROCESSING

This package includes code which handles the preprocessing of texts in Khoekhoe.

INPUT: A folder named "preprocessing\input" which contains ELAN files (eaf).
       Each eaf file should be time aligned and contain annotations in tx (text) and fte (translation) tiers.
       We also assume that all the input files are created with the project's templates (that define the tiers structures).
OUTPUT: The preprocessed eaf files (in "preprocessing\output" folder).

The preprocessing stage consists of the following steps:
1. Validation of character encodings
2. Copy all tx tiers to their corresponding orig tiers
3. Cleaning of tx annotations:
    a. Punctuation cleaning
    b. Decapitalization of words which are not proper names
4. Morpheme segmentation of the text in all tx tiers
________________________________________________________________________________

GLOSSING

This part of the code, which consists of "single_eaf_glosser.py", "glossing_dict_generator.py", "ambiguity_removing.py",
handles the process of glossing the texts in Khoekhoe, i.e., perform linguistic analysis.

INPUT: 1. A folder named "input" which contains ELAN files (eaf).
          Each eaf file should be time aligned, contain annotations in tx, mb, ge, ps and fte tiers. The text in tx should
          already be segmented into morphemes, and this text should be tokenized into mb, ge and ps tiers. The morphemes
          in ge and ps will be replaced with their (morphological/lexical) meanings.
       2. xlsx file which contains a morphological glossing dictionary of Khoekhoe
       3. xlsx file which contains a lexical glossing dictionary
       
We also assume that all the input files are created with the project's templates (that define the tiers structures).

OUTPUT: The glossed eaf files (in "preprocessing\output" folder).
