import json
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import load_workbook


class InputFilesHandler:

    @staticmethod
    def read_excel_worksheet(excel_path: str, worksheet_name: str) -> Worksheet:
        wb = load_workbook(excel_path)
        return wb[worksheet_name]

    @staticmethod
    def read_json_into_dict(json_path: str) -> dict:
        with open(json_path, 'r', encoding="utf8") as json_file:
            return json.load(json_file)

    def read_capitalized_words_file(self, capitalized_words_path):
        capitalized_words_set = set()
        with open(capitalized_words_path, "r", encoding='utf-8') as file:
            cur_line = file.readline()
            while cur_line:
                capitalized_words_set.add(cur_line.strip())
                cur_line = file.readline()
        return capitalized_words_set
