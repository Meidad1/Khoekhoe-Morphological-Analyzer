class Lemma:
    def __init__(self, mb: str, ge: str, ps: str, common_misspellings: str, gender: str, so: str,
                 other_translations: list[str], lemma_type: str):
        self.mb = mb
        self.ge = ge
        self.ps = ps
        self.so = so
        self.gender = gender
        self.other_translations = other_translations
        self.lemma_type = lemma_type
        self.common_misspellings = common_misspellings
