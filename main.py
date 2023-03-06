from glossing_dict_generator import *
from single_eaf_glosser import *
import os
from preprocessing import preprocessor

MORPH_DICT_PATH = "input\\morph_gloss_dict.xlsx"
LEXICAL_DICT_PATH = "input\\lexical_gloss_dict.xlsx"
GLOSSING_INPUT_DIRECTORY_PATH = "C:\\Users\\User\\Desktop\\Meidad\\Work\\Khoekhoe Project\\KK_automatic_glossing\\input"
PREPROCESSING_INPUT_DIRECTORY_PATH = "C:\\Users\\User\\Desktop\\Meidad\\Work\\Khoekhoe Project\\KK_automatic_glossing\\preprocessing\\input"
OUTPUT_DIRECTORY_PATH = "C:\\Users\\User\\Desktop\\Meidad\\Work\\Khoekhoe Project\\KK_automatic_glossing\\output"
PREPROCESSING_OUTPUT_DIRECTORY_PATH = "C:\\Users\\User\\Desktop\\Meidad\\Work\\Khoekhoe Project\\KK_automatic_glossing\\preprocessing\\output"
CAPITALIZED_WORDS_LIST_PATH = "preprocessing\\capital_words.txt"


def preprocess_multiple_files():
    for filename in os.listdir(PREPROCESSING_INPUT_DIRECTORY_PATH):
        if filename.endswith(".eaf"):
            input_path = os.path.join(PREPROCESSING_INPUT_DIRECTORY_PATH, filename)
            output_path = os.path.join(PREPROCESSING_OUTPUT_DIRECTORY_PATH, filename)
            cur_preprocessor = preprocessor.Preprocessor(input_path, output_path, CAPITALIZED_WORDS_LIST_PATH)
            cur_preprocessor.preprocess_file()


def gloss_multiple_files():
    dict_generator = GlossingDictGenerator()
    morpho_dict = dict_generator.get_dict(MORPH_DICT_PATH)
    lexical_dict = dict_generator.get_dict(LEXICAL_DICT_PATH)
    for filename in os.listdir(GLOSSING_INPUT_DIRECTORY_PATH):
        if filename.endswith(".eaf"):
            f_input = os.path.join(GLOSSING_INPUT_DIRECTORY_PATH, filename)
            glosser = SingleEafGlosser(f_input)
            glosser.gloss_file(morpho_dict, lexical_dict)
            f_output = os.path.join(OUTPUT_DIRECTORY_PATH, filename)
            glosser.save_file(f_output)


if __name__ == '__main__':
    preprocess_multiple_files()
    gloss_multiple_files()
