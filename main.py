import os
import sys
from copy import copy
from pprint import pprint
from fix_glosses import fix_glosses
import googleDrive_connection
from input_files_handler import *
from single_eaf_glosser import *
from preprocessing import preprocessor
from glosses_dictionary_parser import glossesDictionaryParser


GLOSSES_DICT_PATH = "input\\ISF_Khoekhoe_dictionary_for_glosses.xlsx"
# GLOSSES_DICT_PATH = "input/ISF_Khoekhoe_dictionary_for_glosses.xlsx"        # for macOS
INPUT_DIRECTORY_PATH = "input"
OUTPUT_DIRECTORY_PATH = "output"
CAPITALIZED_WORDS_LIST_PATH = "input\\capitalized_words.txt"
# CAPITALIZED_WORDS_LIST_PATH = "input/capitalized_words.txt"                 # for macOS
WORDS_NOT_TO_SEGMENT = "input\\words_not_to_segment.json"
# WORDS_NOT_TO_SEGMENT = "input/words_not_to_segment.json"                    # for macOS
PARALINGUISTIC_ITEMS_PATH = "input\\paralinguistic_items.json"
# PARALINGUISTIC_ITEMS_PATH = "input/paralinguistic_items.json"               # for macOS
GLOSSES_DICT_WORKSHEET_NAME = "KK_dict_for_glosses"


def process_all_files(auto_detect_english=True):
    input_files_reader = InputFilesHandler()
    dicts_parser = glossesDictionaryParser()
    glosses_dict_worksheet = input_files_reader.read_excel_worksheet(GLOSSES_DICT_PATH, GLOSSES_DICT_WORKSHEET_NAME)
    glossing_dicts = dicts_parser.parse_dicts(glosses_dict_worksheet)
    gram_dict = glossing_dicts[0]
    lexical_dict = glossing_dicts[1]
    adverbs = dicts_parser.get_adverbs_set()
    paralinguistic_items = input_files_reader.read_json_into_dict(PARALINGUISTIC_ITEMS_PATH)
    words_not_to_segment = input_files_reader.read_json_into_dict(WORDS_NOT_TO_SEGMENT)
    capitalized_words = input_files_reader.read_capitalized_words_file(CAPITALIZED_WORDS_LIST_PATH)

    for filename in os.listdir(INPUT_DIRECTORY_PATH):
        if filename.endswith(".eaf") and filename:
            input_path = os.path.join(INPUT_DIRECTORY_PATH, filename)
            output_path = os.path.join(OUTPUT_DIRECTORY_PATH, filename)

            # Pre-process
            cur_preprocessor = preprocessor.Preprocessor(input_path,
                                                         output_path,
                                                         CAPITALIZED_WORDS_LIST_PATH,
                                                         auto_detect_english,
                                                         capitalized_words,
                                                         words_not_to_segment,
                                                         paralinguistic_items,
                                                         adverbs)
            cur_preprocessor.preprocess_file()

            # Tokenize \tx into \mb and copy \mb to \ge and \ps tiers
            eaf = elan.read_eaf(output_path)
            eaf_parser = EAF_Parser(eaf)
            eaf_parser.tokenize_all_tx_tiers()
            eaf_parser.save_file(output_path)

            # Gloss
            glosser = SingleEafGlosser(output_path, capitalized_words, paralinguistic_items)
            glosser.gloss_file(gram_dict, lexical_dict)
            glosser.save_file(output_path)


def check_input_args(args):
    """
    checks the validity of the user arguments
    :param args: a list of the arguments
    :return: if input is valid - true, otherwise False
    """
    if not (len(args) <= 1):
        return False
    elif len(args) == 1:
        if args[0] not in {"True", "False"}:
            return False
    return True


def run_text_processing():
    args_lst = sys.argv[1:]
    if not check_input_args(args_lst):
        raise Exception("The provided arguments are invalid.")
    auto_detect_english = True
    if len(args_lst) == 1 and args_lst[0] == "False":
        auto_detect_english = False
    process_all_files(auto_detect_english)


if __name__ == '__main__':
    # googleDrive_connection.download_glosses_dictionary_from_googleDrive()
    run_text_processing()
    # fix_glosses.fix_multiple_files()
