# Khoekhoe Grammatical Analyzer
## Description
This project is responsible for the processing pipeline of spoken and written texts (given as ELAN files) in Khoekhoe,
as part of a corpus construction in a linguistic project of the Hebrew University of Jerusalem.  
The analyzer consists of two main modules: preprocessing (cleaning and morpheme segmentation) and glossing (i.e., annotation of morphological functions and part-of-spheech tagging).

### Preprocessing
This package handles the preprocessing of texts in Khoekhoe, which includes the following steps:
* Validation of character encodings
* Copy \tx tiers to their corresponding \orig tiers
* Cleaning the tx annotations:
    - Punctuation cleaning
    - Decapitalization of words which are not proper names
    - Spelling check and correction
* Morpheme segmentation of the text in all tx tiers


### Glossing
This code section consists of _single_eaf_glosser.py_, _glossing_dict_generator.py_ and _ambiguity_removing.py_, which handle the process of glossing the texts in Khoekhoe, i.e., performing linguistic analysis. It fills the morphological meaning/function and part-of-speech of morphemes in \ge and \ps tiers of the input ELAN files.

## Usage
**INPUT**  
The folder _input_ should contain the following files:
1. All ELAN files (.eaf) you want to gloss. _pfsx_ files are allowed to be in this folder, they are ignored.  
Each eaf file should be time aligned and contain annotations in \tx (text) and \fte (translation) tiers. In addition, backchannel notations should be written in \fte tiers.    
It is also assumed that all the input files are created with the project's templates (that define the tiers structures).  
2. _ISF_Khoekhoe_dictionary_for_glosses.xlsx_ file which contains a glossing dictionary of Khoekhoe. This file must contain a sheet called: "KK_dict_for_glosses".
3. _misspellings_correction.json_: includes all the replacements needed for misspelled forms in the texts.  
   Be careful when editing it and do not change its structure.
4. _capital_words.txt_: includes a list of words that should be capitalized. This file is updated automatically, but one can manually add words to it. Each word should be in a separate line.
5. _words_not_to_segment.json_: includes two lists (in JSON format) of words which should not be segmented.
6. _paralinguistic_items.json_: includes a few lists (in JSON format) of phonetic representations of paralinguistic items, as backchannels and fillers.

<u>Note</u>: If you run the script on **macOS**, you will have to adjust the following paths:
* In main.py, change GLOSSES_DICT_PATH and CAPITALIZED_WORDS_LIST_PATH
* In annotation_cleaner.py, change MISSPELLINGS_DICTS_PATH

<br>

**OUTPUT**  
The glossed .eaf files will be in _output_ folder.

To run the script, navigate to the directory where the project files are located and execute the command in the terminal:

_python main.py_

If it doesn't work, try: _python3 main.py_

It is also possible to add one boolean argument (True/False) which determines whether to detect English parts automatically or not.
If you don't specify, the default is automatic detection. For example, the following command:
_python3 main.py False_  
will not use automatic detection tools for English. Otherwise, you can just run the command either without arguments or with "True" argument as here:  
_python3 main.py True_  

<u>Note</u>: If this is the first time you run the script, it will not compile until you install several packages.
To do so, you can run the following command:  
_pip install <package_name>_  
For example: _pip install speach_